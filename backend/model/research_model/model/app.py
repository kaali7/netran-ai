import os
import sys
import threading
import json
from pathlib import Path

# Add current directory to path for clean imports when running directly
current_dir = Path(__file__).resolve().parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))
parent_dir = current_dir.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

import kivy
from kivy.app import App
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle, RoundedRectangle, Line

from model.pipeline import run_pipeline
from model.schemas import InterviewRubric

# Window setup with modern dimensions
Window.size = (960, 720)
Window.clearcolor = (0.05, 0.06, 0.09, 1)  # Deep Obsidian #0D0F17

SAMPLE_JD = """Company: Google
Role: Senior Frontend Engineer (React & TypeScript)

Responsibilities:
- Build high-performance, accessible, and scalable web applications using React, TypeScript, and modern Web APIs.
- Optimize frontend web performance, bundle size, Core Web Vitals, and client-side caching.
- Collaborate with backend engineers to integrate GraphQL and REST APIs.
- Conduct technical design reviews and mentor junior frontend developers.

Requirements:
- 5+ years of experience with React, TypeScript, JavaScript (ES6+), HTML5, and CSS3.
- Deep understanding of state management (Redux/Zustand), Webpack/Vite build tools, and micro-frontend architectures.
- Strong knowledge of web security (CORS, XSS, CSRF) and performance profiling.
"""

# Color Tokens (RGB values normalized to 0-1)
COLOR_BG = (0.05, 0.06, 0.09, 1)        # #0D0F17 Deep Obsidian
COLOR_CARD = (0.09, 0.10, 0.15, 1)      # #171A26 Card Surface
COLOR_CARD_ALT = (0.12, 0.13, 0.20, 1)  # #1F2233 Active Card Surface
COLOR_BORDER = (0.18, 0.20, 0.30, 1)    # Subtle Card Border
COLOR_PRIMARY = (0.39, 0.40, 0.95, 1)   # #6366F1 Electric Indigo
COLOR_PRIMARY_HOVER = (0.32, 0.33, 0.85, 1)
COLOR_ACCENT = (0.54, 0.36, 0.96, 1)    # #8B5CF6 Violet Neon
COLOR_SUCCESS = (0.06, 0.72, 0.51, 1)   # #10B981 Emerald Green
COLOR_WARNING = (0.96, 0.62, 0.04, 1)   # #F59E0B Amber Flame
COLOR_DANGER = (0.93, 0.27, 0.38, 1)    # #EF4444 Crimson Red
COLOR_TEXT_PRIMARY = (0.95, 0.96, 1.0, 1)
COLOR_TEXT_MUTED = (0.55, 0.58, 0.70, 1)


class GlassCard(BoxLayout):
    """Premium Card Widget with rounded corners and border outline."""
    def __init__(self, bg_color=COLOR_CARD, border_color=COLOR_BORDER, radius=12, **kwargs):
        super().__init__(**kwargs)
        self.bg_color = bg_color
        self.border_color = border_color
        self.radius = radius
        with self.canvas.before:
            Color(*self.bg_color)
            self.rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[self.radius])
            Color(*self.border_color)
            self.border = Line(rounded_rectangle=(self.x, self.y, self.width, self.height, self.radius), width=1.1)
        self.bind(pos=self._update_graphics, size=self._update_graphics)

    def _update_graphics(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size
        self.border.rounded_rectangle = (self.x, self.y, self.width, self.height, self.radius)


class PrimaryButton(Button):
    """Custom styled button with primary theme colors."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ''
        self.background_color = COLOR_PRIMARY
        self.color = COLOR_TEXT_PRIMARY
        self.bold = True
        self.font_size = '14sp'


class InputScreen(Screen):
    """Screen 1: Job Description Input & Control Panel."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        main_layout = BoxLayout(orientation='vertical', padding=[24, 20, 24, 20], spacing=16)

        # ── TOP NAV / BRAND HEADER ──
        nav_bar = BoxLayout(orientation='horizontal', size_hint_y=None, height=50, spacing=12)
        
        logo_box = BoxLayout(orientation='horizontal', spacing=8)
        brand_icon = Label(
            text="⚡",
            font_size='22sp',
            size_hint_x=None,
            width=30
        )
        brand_title = Label(
            text="[b]Netran AI[/b]  [color=8B5CF6]•[/color]  [size=14sp][color=8888AA]JD Research Engine[/color][/size]",
            markup=True,
            font_size='20sp',
            color=COLOR_TEXT_PRIMARY,
            halign='left',
            valign='middle'
        )
        brand_title.bind(size=brand_title.setter('text_size'))
        logo_box.add_widget(brand_icon)
        logo_box.add_widget(brand_title)

        # Badge pill
        badge_card = GlassCard(
            bg_color=(0.12, 0.15, 0.25, 1),
            border_color=(0.3, 0.35, 0.6, 1),
            radius=16,
            size_hint=(None, None),
            size=(190, 34),
            padding=[10, 4]
        )
        badge_label = Label(
            text="✨ [b]Gemini 3.6 + Tavily[/b]",
            markup=True,
            font_size='11sp',
            color=(0.7, 0.8, 1, 1)
        )
        badge_card.add_widget(badge_label)

        nav_bar.add_widget(logo_box)
        nav_bar.add_widget(badge_card)
        main_layout.add_widget(nav_bar)

        # Subtitle banner
        sub_label = Label(
            text="Synthesize live market interview intel with Job Descriptions into structured technical rubrics.",
            font_size='13sp',
            color=COLOR_TEXT_MUTED,
            size_hint_y=None,
            height=20,
            halign='left'
        )
        sub_label.bind(size=sub_label.setter('text_size'))
        main_layout.add_widget(sub_label)

        # ── INPUT CONTAINER CARD ──
        input_card = GlassCard(
            bg_color=COLOR_CARD,
            border_color=COLOR_BORDER,
            radius=14,
            orientation='vertical',
            padding=[16, 14, 16, 14],
            spacing=10
        )

        input_header = BoxLayout(orientation='horizontal', size_hint_y=None, height=28)
        input_title = Label(
            text="📋 [b]Job Description Text[/b]",
            markup=True,
            font_size='14sp',
            color=(0.7, 0.85, 1, 1),
            halign='left',
            valign='middle'
        )
        input_title.bind(size=input_title.setter('text_size'))
        
        char_counter = Label(
            text="Ready",
            font_size='12sp',
            color=COLOR_TEXT_MUTED,
            halign='right',
            valign='middle'
        )
        char_counter.bind(size=char_counter.setter('text_size'))
        self.char_counter = char_counter

        input_header.add_widget(input_title)
        input_header.add_widget(char_counter)
        input_card.add_widget(input_header)

        self.jd_input = TextInput(
            hint_text="Paste raw Job Description (JD) text here...\nExample: Company, Responsibilities, Technical Requirements, Tech Stack...",
            background_color=(0.06, 0.07, 0.11, 1),
            foreground_color=COLOR_TEXT_PRIMARY,
            hint_text_color=(0.35, 0.38, 0.48, 1),
            cursor_color=COLOR_PRIMARY,
            multiline=True,
            padding=[14, 12, 14, 12],
            font_size='14sp'
        )
        self.jd_input.bind(text=self.on_text_change)
        input_card.add_widget(self.jd_input)
        main_layout.add_widget(input_card)

        # ── BUTTON BAR ──
        btn_bar = BoxLayout(orientation='horizontal', size_hint_y=None, height=48, spacing=12)

        sample_btn = Button(
            text="💡 Load Sample JD",
            size_hint_x=0.32,
            background_normal='',
            background_color=(0.15, 0.17, 0.25, 1),
            color=(0.8, 0.85, 1, 1),
            font_size='13sp',
            bold=True
        )
        sample_btn.bind(on_press=self.load_sample)

        self.analyze_btn = PrimaryButton(
            text="🚀 Analyze JD & Search Market Intel",
            size_hint_x=0.68
        )
        self.analyze_btn.bind(on_press=self.start_analysis)

        btn_bar.add_widget(sample_btn)
        btn_bar.add_widget(self.analyze_btn)
        main_layout.add_widget(btn_bar)

        # ── STATUS FOOTER BAR ──
        status_card = GlassCard(
            bg_color=(0.07, 0.08, 0.13, 1),
            border_color=(0.14, 0.16, 0.24, 1),
            radius=10,
            size_hint_y=None,
            height=36,
            padding=[12, 6]
        )
        self.status_label = Label(
            text="● Idle — Ready to analyze job requirements",
            font_size='12sp',
            color=COLOR_TEXT_MUTED,
            halign='left',
            valign='middle'
        )
        self.status_label.bind(size=self.status_label.setter('text_size'))
        status_card.add_widget(self.status_label)
        main_layout.add_widget(status_card)

        self.add_widget(main_layout)

    def on_text_change(self, instance, text):
        length = len(text.strip())
        if length > 0:
            self.char_counter.text = f"{length} chars"
        else:
            self.char_counter.text = "Ready"

    def load_sample(self, instance):
        self.jd_input.text = SAMPLE_JD
        self.status_label.text = "● Sample Google Senior Frontend Engineer JD loaded"

    def start_analysis(self, instance):
        jd_text = self.jd_input.text.strip()
        if not jd_text:
            self.status_label.text = "⚠️ Please paste a Job Description first."
            self.status_label.color = COLOR_WARNING
            return

        self.analyze_btn.disabled = True
        self.status_label.color = (0.7, 0.8, 1, 1)
        self.status_label.text = "⏳ Initializing AI reasoning pipeline..."

        threading.Thread(target=self._run_async, args=(jd_text,), daemon=True).start()

    def _run_async(self, jd_text):
        def update_status(msg):
            Clock.schedule_once(lambda dt: setattr(self.status_label, 'text', f"⏳ {msg}"))

        try:
            rubric = run_pipeline(jd_text, status_callback=update_status)
            Clock.schedule_once(lambda dt: self._on_success(rubric))
        except Exception as e:
            err_msg = str(e)
            Clock.schedule_once(lambda dt: self._on_error(err_msg))

    def _on_success(self, rubric: InterviewRubric):
        self.analyze_btn.disabled = False
        self.status_label.text = "✅ Analysis complete!"
        self.status_label.color = COLOR_SUCCESS
        app = App.get_running_app()
        app.show_results(rubric)

    def _on_error(self, err_msg):
        self.analyze_btn.disabled = False
        self.status_label.text = f"❌ Pipeline Error: {err_msg[:90]}"
        self.status_label.color = COLOR_DANGER


class ResultsScreen(Screen):
    """Screen 2: Display Structured Interview Rubric Cards."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_rubric = None
        main_layout = BoxLayout(orientation='vertical', padding=[24, 20, 24, 20], spacing=16)

        # ── NAVIGATION / HEADER BAR ──
        nav_bar = BoxLayout(orientation='horizontal', size_hint_y=None, height=46, spacing=12)

        back_btn = Button(
            text="← Analyze Another JD",
            size_hint_x=0.28,
            background_normal='',
            background_color=(0.14, 0.16, 0.24, 1),
            color=COLOR_TEXT_PRIMARY,
            font_size='13sp',
            bold=True
        )
        back_btn.bind(on_press=self.go_back)

        header_title = Label(
            text="🎯 [b]Generated Interview Rubric & Intel[/b]",
            markup=True,
            font_size='18sp',
            color=COLOR_TEXT_PRIMARY,
            halign='left',
            valign='middle'
        )
        header_title.bind(size=header_title.setter('text_size'))

        copy_btn = Button(
            text="📄 Copy JSON",
            size_hint_x=0.20,
            background_normal='',
            background_color=(0.18, 0.22, 0.35, 1),
            color=(0.8, 0.9, 1, 1),
            font_size='12sp'
        )
        copy_btn.bind(on_press=self.copy_json)

        nav_bar.add_widget(back_btn)
        nav_bar.add_widget(header_title)
        nav_bar.add_widget(copy_btn)
        main_layout.add_widget(nav_bar)

        # ── SCROLLABLE RUBRIC CONTENT ──
        self.scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False)
        self.content_box = GridLayout(cols=1, spacing=16, size_hint_y=None)
        self.content_box.bind(minimum_height=self.content_box.setter('height'))
        self.scroll.add_widget(self.content_box)
        main_layout.add_widget(self.scroll)

        self.add_widget(main_layout)

    def go_back(self, instance):
        app = App.get_running_app()
        app.sm.current = 'input'

    def copy_json(self, instance):
        if self.current_rubric:
            from kivy.core.clipboard import Clipboard
            json_str = json.dumps(self.current_rubric.model_dump(), indent=2)
            Clipboard.copy(json_str)
            instance.text = "✅ Copied!"
            Clock.schedule_once(lambda dt: setattr(instance, 'text', '📄 Copy JSON'), 2)

    def display_rubric(self, rubric: InterviewRubric):
        self.current_rubric = rubric
        self.content_box.clear_widgets()

        # ── 1. ROLE OVERVIEW CARD ──
        overview_card = GlassCard(
            bg_color=(0.10, 0.12, 0.19, 1),
            border_color=(0.25, 0.30, 0.48, 1),
            radius=12,
            orientation='vertical',
            padding=16,
            spacing=10,
            size_hint_y=None
        )

        overview_title = Label(
            text="📌 [b]Role Overview & Target Profile[/b]",
            markup=True,
            font_size='15sp',
            color=(0.6, 0.82, 1, 1),
            size_hint_y=None,
            height=24,
            halign='left'
        )
        overview_title.bind(size=overview_title.setter('text_size'))
        overview_card.add_widget(overview_title)

        overview_text = Label(
            text=rubric.roleOverview,
            font_size='13sp',
            color=(0.90, 0.92, 0.98, 1),
            size_hint_y=None,
            halign='left',
            valign='top'
        )
        overview_text.bind(width=lambda *x: overview_text.setter('text_size')(overview_text, (overview_text.width, None)))
        overview_text.bind(texture_size=lambda *x: setattr(overview_text, 'height', overview_text.texture_size[1]))
        overview_card.add_widget(overview_text)

        overview_card.height = 65 + overview_text.height
        self.content_box.add_widget(overview_card)

        # ── 2. KEY TECHNICAL PILLARS CARD ──
        pillars_card = GlassCard(
            bg_color=(0.10, 0.12, 0.19, 1),
            border_color=(0.25, 0.30, 0.48, 1),
            radius=12,
            orientation='vertical',
            padding=16,
            spacing=10,
            size_hint_y=None
        )

        pillars_title = Label(
            text="⚙️ [b]Core Technical Pillars[/b]",
            markup=True,
            font_size='15sp',
            color=(0.6, 0.82, 1, 1),
            size_hint_y=None,
            height=24,
            halign='left'
        )
        pillars_title.bind(size=pillars_title.setter('text_size'))
        pillars_card.add_widget(pillars_title)

        # Chip-style bullet display
        pillars_str = "\n".join([f"  ⚡  {pillar}" for pillar in rubric.keyTechnicalPillars])
        pillars_text = Label(
            text=pillars_str,
            font_size='13sp',
            color=(0.75, 0.92, 0.82, 1),
            size_hint_y=None,
            halign='left'
        )
        pillars_text.bind(width=lambda *x: pillars_text.setter('text_size')(pillars_text, (pillars_text.width, None)))
        pillars_text.bind(texture_size=lambda *x: setattr(pillars_text, 'height', pillars_text.texture_size[1]))
        pillars_card.add_widget(pillars_text)

        pillars_card.height = 65 + pillars_text.height
        self.content_box.add_widget(pillars_card)

        # ── 3. INTERVIEW TOPICS & QUESTIONS ──
        section_label = Label(
            text="🔥 [b]Assessment Topics & Real-World Questions[/b]",
            markup=True,
            font_size='16sp',
            color=(1, 0.82, 0.4, 1),
            size_hint_y=None,
            height=28,
            halign='left'
        )
        section_label.bind(size=section_label.setter('text_size'))
        self.content_box.add_widget(section_label)

        difficulty_badges = {
            "Junior": "[color=10B981]🟢 Junior Level[/color]",
            "Mid": "[color=F59E0B]🟡 Mid Level[/color]",
            "Senior": "[color=EF4444]🔴 Senior Level[/color]"
        }

        for idx, topic in enumerate(rubric.expectedInterviewTopics):
            topic_card = GlassCard(
                bg_color=(0.08, 0.09, 0.14, 1),
                border_color=(0.20, 0.22, 0.34, 1),
                radius=10,
                orientation='vertical',
                padding=14,
                spacing=10,
                size_hint_y=None
            )

            badge = difficulty_badges.get(topic.difficulty, topic.difficulty)
            header_str = f"[b]Topic {idx+1}: {topic.category}[/b]   [size=12sp]•   {badge}[/size]"

            topic_title = Label(
                text=header_str,
                markup=True,
                font_size='14sp',
                size_hint_y=None,
                height=24,
                halign='left'
            )
            topic_title.bind(size=topic_title.setter('text_size'))
            topic_card.add_widget(topic_title)

            # Format questions
            q_formatted = []
            for q_num, q in enumerate(topic.example_questions, start=1):
                q_formatted.append(f"[color=8B5CF6][b]Q{q_num}:[/b][/color] {q}")

            q_text_str = "\n\n".join(q_formatted)
            q_label = Label(
                text=q_text_str,
                markup=True,
                font_size='13sp',
                color=(0.88, 0.89, 0.95, 1),
                size_hint_y=None,
                halign='left'
            )
            q_label.bind(width=lambda *x: q_label.setter('text_size')(q_label, (q_label.width, None)))
            q_label.bind(texture_size=lambda *x: setattr(q_label, 'height', q_label.texture_size[1]))
            topic_card.add_widget(q_label)

            topic_card.height = 55 + q_label.height
            self.content_box.add_widget(topic_card)


class NetranResearchApp(App):
    def build(self):
        self.title = "Netran AI — JD Research Engine"
        self.sm = ScreenManager(transition=FadeTransition(duration=0.2))

        self.input_screen = InputScreen(name='input')
        self.results_screen = ResultsScreen(name='results')

        self.sm.add_widget(self.input_screen)
        self.sm.add_widget(self.results_screen)

        return self.sm

    def show_results(self, rubric: InterviewRubric):
        self.results_screen.display_rubric(rubric)
        self.sm.current = 'results'


if __name__ == '__main__':
    NetranResearchApp().run()
