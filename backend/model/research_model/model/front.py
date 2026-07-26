"""
Netran AI — Stage 1: JD Research & Market Intelligence Engine
Module: front.py
Description: Standalone Kivy Desktop GUI application for Stage 1 JD research, web intelligence visualization,
             preset dummy input loading, and rubric generation.
"""

import json
import sys
import threading
from datetime import datetime
from pathlib import Path

# Add current directory to path for clean imports when running directly
current_dir = Path(__file__).resolve().parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))
parent_dir = current_dir.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))
root_dir = parent_dir.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Line, RoundedRectangle
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import FadeTransition, Screen, ScreenManager
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput

try:
    from .pipeline import run_pipeline
    from .schemas import InterviewRubric, Stage1Output
except ImportError:
    try:
        from model.research_model.model.pipeline import run_pipeline
        from model.research_model.model.schemas import InterviewRubric, Stage1Output
    except ImportError:
        from pipeline import run_pipeline
        from schemas import Stage1Output

# Window setup with modern dimensions
Window.size = (1024, 768)
Window.clearcolor = (0.05, 0.06, 0.09, 1)  # Deep Obsidian #0D0F17

# Test Paths
TEST_INPUT_DIR = parent_dir / "test" / "input"
TEST_OUTPUT_DIR = parent_dir / "test" / "output"

# Color Tokens
COLOR_BG = (0.05, 0.06, 0.09, 1)        # #0D0F17 Deep Obsidian
COLOR_CARD = (0.09, 0.10, 0.15, 1)      # #171A26 Card Surface
COLOR_CARD_ALT = (0.12, 0.13, 0.20, 1)  # #1F2233 Active Card Surface
COLOR_BORDER = (0.18, 0.20, 0.30, 1)    # Subtle Card Border
COLOR_PRIMARY = (0.39, 0.40, 0.95, 1)   # #6366F1 Electric Indigo
COLOR_ACCENT = (0.54, 0.36, 0.96, 1)    # #8B5CF6 Violet Neon
COLOR_SUCCESS = (0.06, 0.72, 0.51, 1)   # #10B981 Emerald Green
COLOR_WARNING = (0.96, 0.62, 0.04, 1)   # #F59E0B Amber Flame
COLOR_DANGER = (0.93, 0.27, 0.38, 1)    # #EF4444 Crimson Red
COLOR_TEXT_PRIMARY = (0.95, 0.96, 1.0, 1)
COLOR_TEXT_MUTED = (0.55, 0.58, 0.70, 1)

# Domain Source Badge Colors
DOMAIN_COLORS = {
    "linkedin.com": ("[color=0077B5]💼 LinkedIn[/color]", (0.0, 0.47, 0.75, 1)),
    "leetcode.com": ("[color=F59E0B]⚡ LeetCode[/color]", (0.96, 0.62, 0.04, 1)),
    "glassdoor.com": ("[color=10B981]📊 Glassdoor[/color]", (0.06, 0.72, 0.51, 1)),
    "github.com": ("[color=8888AA]🐙 GitHub[/color]", (0.53, 0.53, 0.67, 1)),
    "stackoverflow.com": ("[color=F48024]🥞 StackOverflow[/color]", (0.95, 0.50, 0.14, 1)),
    "geeksforgeeks.org": ("[color=2F9E44]🟢 GeeksforGeeks[/color]", (0.18, 0.62, 0.27, 1)),
    "reddit.com": ("[color=FF4500]🤖 Reddit[/color]", (1.0, 0.27, 0.0, 1)),
    "medium.com": ("[color=8B5CF6]📝 Medium[/color]", (0.54, 0.36, 0.96, 1)),
    "dev.to": ("[color=6366F1]💻 Dev.to[/color]", (0.39, 0.40, 0.95, 1)),
}


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
    """Screen 1: Job Description Input & Preset Selector Panel."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        main_layout = BoxLayout(orientation='vertical', padding=[24, 20, 24, 20], spacing=14)

        # ── TOP NAV / BRAND HEADER ──
        nav_bar = BoxLayout(orientation='horizontal', size_hint_y=None, height=48, spacing=12)
        
        logo_box = BoxLayout(orientation='horizontal', spacing=8)
        brand_icon = Label(
            text="⚡",
            font_size='24sp',
            size_hint_x=None,
            width=32
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
            size=(220, 36),
            padding=[12, 4]
        )
        badge_label = Label(
            text="✨ [b]Gemini 3.6 + Tavily Live Search[/b]",
            markup=True,
            font_size='11sp',
            color=(0.7, 0.85, 1, 1)
        )
        badge_card.add_widget(badge_label)

        nav_bar.add_widget(logo_box)
        nav_bar.add_widget(badge_card)
        main_layout.add_widget(nav_bar)

        # ── PRESET DUMMY SELECTION BAR ──
        preset_bar = BoxLayout(orientation='horizontal', size_hint_y=None, height=40, spacing=8)
        preset_title = Label(
            text="📁 [b]Preset Dummy Inputs:[/b]",
            markup=True,
            font_size='12sp',
            color=COLOR_TEXT_MUTED,
            size_hint_x=0.25,
            halign='left',
            valign='middle'
        )
        preset_title.bind(size=preset_title.setter('text_size'))
        preset_bar.add_widget(preset_title)

        sample1_btn = Button(
            text="💡 Google Frontend",
            size_hint_x=0.25,
            background_normal='',
            background_color=(0.14, 0.16, 0.26, 1),
            color=(0.8, 0.9, 1, 1),
            font_size='12sp',
            bold=True
        )
        sample1_btn.bind(on_press=lambda inst: self.load_preset("sample_jd_google_frontend.json"))

        sample2_btn = Button(
            text="⚡ Backend Systems",
            size_hint_x=0.25,
            background_normal='',
            background_color=(0.14, 0.16, 0.26, 1),
            color=(0.8, 0.9, 1, 1),
            font_size='12sp',
            bold=True
        )
        sample2_btn.bind(on_press=lambda inst: self.load_preset("sample_jd_backend_engineer.json"))

        sample3_btn = Button(
            text="🤖 Full Stack AI",
            size_hint_x=0.25,
            background_normal='',
            background_color=(0.14, 0.16, 0.26, 1),
            color=(0.8, 0.9, 1, 1),
            font_size='12sp',
            bold=True
        )
        sample3_btn.bind(on_press=lambda inst: self.load_preset("sample_jd_fullstack.json"))

        preset_bar.add_widget(sample1_btn)
        preset_bar.add_widget(sample2_btn)
        preset_bar.add_widget(sample3_btn)
        main_layout.add_widget(preset_bar)

        # ── INPUT CONTAINER CARD ──
        input_card = GlassCard(
            bg_color=COLOR_CARD,
            border_color=COLOR_BORDER,
            radius=14,
            orientation='vertical',
            padding=[16, 12, 16, 12],
            spacing=8
        )

        input_header = BoxLayout(orientation='horizontal', size_hint_y=None, height=26)
        input_title = Label(
            text="📋 [b]Job Description Text (Paste or Select Preset)[/b]",
            markup=True,
            font_size='13sp',
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
            hint_text="Paste raw Job Description (JD) text here or click a preset dummy input above...\nSupports role expectations, tech stack requirements, and company context.",
            background_color=(0.06, 0.07, 0.11, 1),
            foreground_color=COLOR_TEXT_PRIMARY,
            hint_text_color=(0.35, 0.38, 0.48, 1),
            cursor_color=COLOR_PRIMARY,
            multiline=True,
            padding=[14, 12, 14, 12],
            font_size='13sp'
        )
        self.jd_input.bind(text=self.on_text_change)
        input_card.add_widget(self.jd_input)
        main_layout.add_widget(input_card)

        # ── BUTTON ACTION BAR ──
        btn_bar = BoxLayout(orientation='horizontal', size_hint_y=None, height=46, spacing=12)

        save_preset_btn = Button(
            text="💾 Save Pasted JD (JSON) to test/input/",
            size_hint_x=0.38,
            background_normal='',
            background_color=(0.16, 0.18, 0.28, 1),
            color=(0.8, 0.9, 1, 1),
            font_size='12sp'
        )
        save_preset_btn.bind(on_press=self.save_pasted_jd)

        self.analyze_btn = PrimaryButton(
            text="🚀 Analyze JD & Search Live Market Intel",
            size_hint_x=0.62
        )
        self.analyze_btn.bind(on_press=self.start_analysis)

        btn_bar.add_widget(save_preset_btn)
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
            text="● Idle — Select preset dummy or paste custom JD to start research",
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

    def load_preset(self, filename: str):
        filepath = TEST_INPUT_DIR / filename
        if not filepath.exists():
            alt = filename.replace('.txt', '.json') if filename.endswith('.txt') else filename.replace('.json', '.txt')
            filepath = TEST_INPUT_DIR / alt

        if filepath.exists():
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read().strip()
            if filepath.suffix.lower() == ".json":
                try:
                    data = json.loads(content)
                    if isinstance(data, dict):
                        content = data.get("jd_text", content)
                except Exception:
                    pass
            self.jd_input.text = content
            self.status_label.text = f"● Loaded preset JSON: '{filepath.name}'"
            self.status_label.color = COLOR_SUCCESS
        else:
            self.status_label.text = f"⚠️ Preset file '{filename}' not found."
            self.status_label.color = COLOR_WARNING

    def save_pasted_jd(self, instance):
        text = self.jd_input.text.strip()
        if not text:
            self.status_label.text = "⚠️ Cannot save empty text."
            self.status_label.color = COLOR_WARNING
            return
        
        TEST_INPUT_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"custom_jd_{timestamp}.json"
        save_path = TEST_INPUT_DIR / filename
        
        payload = {
            "company": "Target Company",
            "role": "Custom Role",
            "target_seniority": "Senior",
            "jd_text": text
        }
        
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        
        self.status_label.text = f"✅ Saved custom JD JSON to test/input/{filename}"
        self.status_label.color = COLOR_SUCCESS

    def start_analysis(self, instance):
        jd_text = self.jd_input.text.strip()
        if not jd_text:
            self.status_label.text = "⚠️ Please select a preset or paste a Job Description first."
            self.status_label.color = COLOR_WARNING
            return

        self.analyze_btn.disabled = True
        self.status_label.color = (0.7, 0.8, 1, 1)
        self.status_label.text = "⏳ Initializing AI reasoning & web search pipeline..."

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_file = str(TEST_OUTPUT_DIR / f"sess_{timestamp}.json")

        threading.Thread(target=self._run_async, args=(jd_text, session_file), daemon=True).start()

    def _run_async(self, jd_text, session_dir):
        def update_status(msg):
            Clock.schedule_once(lambda dt: setattr(self.status_label, 'text', f"⏳ {msg}"))

        try:
            output: Stage1Output = run_pipeline(jd_text, status_callback=update_status, output_dir=session_dir)
            Clock.schedule_once(lambda dt: self._on_success(output))
        except Exception as e:
            err_msg = str(e)
            Clock.schedule_once(lambda dt: self._on_error(err_msg))

    def _on_success(self, output: Stage1Output):
        self.analyze_btn.disabled = False
        self.status_label.text = "✅ Analysis complete! Displaying web intel & rubric..."
        self.status_label.color = COLOR_SUCCESS
        app = App.get_running_app()
        app.show_results(output)

    def _on_error(self, err_msg):
        self.analyze_btn.disabled = False
        self.status_label.text = f"❌ Pipeline Error: {err_msg[:90]}"
        self.status_label.color = COLOR_DANGER


class ResultsScreen(Screen):
    """Screen 2: Redesigned Visual Display for Web Intelligence & Interview Rubric."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_output = None
        main_layout = BoxLayout(orientation='vertical', padding=[24, 20, 24, 20], spacing=14)

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
            text="🎯 [b]Market Intelligence & Assessment Rubric[/b]",
            markup=True,
            font_size='18sp',
            color=COLOR_TEXT_PRIMARY,
            halign='left',
            valign='middle'
        )
        header_title.bind(size=header_title.setter('text_size'))

        copy_btn = Button(
            text="📄 Copy JSON",
            size_hint_x=0.22,
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

        # ── SCROLLABLE CONTENT AREA ──
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
        if self.current_output and hasattr(self.current_output, 'rubric'):
            from kivy.core.clipboard import Clipboard
            json_str = json.dumps(self.current_output.rubric.model_dump(), indent=2)
            Clipboard.copy(json_str)
            instance.text = "✅ Copied!"
            Clock.schedule_once(lambda dt: setattr(instance, 'text', '📄 Copy JSON'), 2)

    def display_results(self, output: Stage1Output):
        self.current_output = output
        self.content_box.clear_widgets()
        
        rubric = output.rubric
        parsed_jd = output.parsed_jd
        search_context = output.search_context

        # ── 1. ROLE PROFILE & EXTRACTED METADATA CARD ──
        profile_card = GlassCard(
            bg_color=(0.10, 0.12, 0.20, 1),
            border_color=(0.28, 0.32, 0.52, 1),
            radius=12,
            orientation='vertical',
            padding=16,
            spacing=10,
            size_hint_y=None
        )

        role_str = f"[b]{parsed_jd.role}[/b]   [size=13sp][color=8B5CF6]at[/color] [color=10B981]{parsed_jd.company}[/color][/size]"
        profile_title = Label(
            text=f"👤 {role_str}",
            markup=True,
            font_size='16sp',
            color=COLOR_TEXT_PRIMARY,
            size_hint_y=None,
            height=26,
            halign='left'
        )
        profile_title.bind(size=profile_title.setter('text_size'))
        profile_card.add_widget(profile_title)

        tech_chips = "  •  ".join(parsed_jd.tech_stack) if parsed_jd.tech_stack else "General Technical Stack"
        tech_label = Label(
            text=f"[color=8888AA]Extracted Tech Stack:[/color]  [color=70C0FF]{tech_chips}[/color]",
            markup=True,
            font_size='12sp',
            size_hint_y=None,
            height=22,
            halign='left'
        )
        tech_label.bind(size=tech_label.setter('text_size'))
        profile_card.add_widget(tech_label)

        if parsed_jd.search_queries:
            queries_str = " | ".join([f'"{q}"' for q in parsed_jd.search_queries[:3]])
            query_label = Label(
                text=f"[color=8888AA]Executed Web Search Queries:[/color]  [color=F59E0B]{queries_str}[/color]",
                markup=True,
                font_size='11sp',
                size_hint_y=None,
                height=22,
                halign='left'
            )
            query_label.bind(size=query_label.setter('text_size'))
            profile_card.add_widget(query_label)
            profile_card.height = 95
        else:
            profile_card.height = 72

        self.content_box.add_widget(profile_card)

        # ── 2. LIVE WEB INTELLIGENCE SOURCES CARD ──
        intel_section_label = Label(
            text="🌐 [b]Retrieved Live Market Web Intelligence Sources[/b]",
            markup=True,
            font_size='16sp',
            color=(0.4, 0.8, 1, 1),
            size_hint_y=None,
            height=26,
            halign='left'
        )
        intel_section_label.bind(size=intel_section_label.setter('text_size'))
        self.content_box.add_widget(intel_section_label)

        if search_context:
            for item in search_context:
                url = item.get("url", "")
                title = item.get("title", "Market Intel Source")
                snippet = item.get("content", "")

                # Detect domain badge formatting
                badge_text = "🌐 Web Source"
                for domain_key, (tag, _color) in DOMAIN_COLORS.items():
                    if domain_key in url.lower():
                        badge_text = tag
                        break

                source_card = GlassCard(
                    bg_color=(0.08, 0.10, 0.16, 1),
                    border_color=(0.20, 0.24, 0.38, 1),
                    radius=10,
                    orientation='vertical',
                    padding=14,
                    spacing=8,
                    size_hint_y=None
                )

                card_head = BoxLayout(orientation='horizontal', size_hint_y=None, height=24)
                source_title = Label(
                    text=f"[b]{title}[/b]",
                    markup=True,
                    font_size='13sp',
                    color=COLOR_TEXT_PRIMARY,
                    size_hint_x=0.72,
                    halign='left',
                    valign='middle'
                )
                source_title.bind(size=source_title.setter('text_size'))

                domain_badge = Label(
                    text=badge_text,
                    markup=True,
                    font_size='11sp',
                    size_hint_x=0.28,
                    halign='right',
                    valign='middle'
                )
                domain_badge.bind(size=domain_badge.setter('text_size'))

                card_head.add_widget(source_title)
                card_head.add_widget(domain_badge)
                source_card.add_widget(card_head)

                url_label = Label(
                    text=f"[color=5588DD]{url}[/color]",
                    markup=True,
                    font_size='11sp',
                    size_hint_y=None,
                    height=18,
                    halign='left'
                )
                url_label.bind(size=url_label.setter('text_size'))
                source_card.add_widget(url_label)

                clean_snippet = snippet[:220].strip().replace('\n', ' ')
                snippet_label = Label(
                    text=f'"{clean_snippet}..."',
                    font_size='12sp',
                    color=COLOR_TEXT_MUTED,
                    size_hint_y=None,
                    halign='left',
                    valign='top'
                )
                snippet_label.bind(width=lambda *x: snippet_label.setter('text_size')(snippet_label, (snippet_label.width, None)))
                snippet_label.bind(texture_size=lambda *x: setattr(snippet_label, 'height', snippet_label.texture_size[1]))
                source_card.add_widget(snippet_label)

                source_card.height = 65 + snippet_label.height
                self.content_box.add_widget(source_card)
        else:
            no_intel_card = GlassCard(
                bg_color=(0.08, 0.09, 0.14, 1),
                border_color=(0.2, 0.22, 0.32, 1),
                radius=10,
                orientation='vertical',
                padding=14,
                size_hint_y=None,
                height=54
            )
            msg = "⚡ Cached Result / Gemini Baseline mode — Web search skipped for cached JD text." if output.cached else "ℹ️ Operating in fallback mode using LLM domain baseline knowledge."
            no_intel_label = Label(
                text=msg,
                font_size='12sp',
                color=COLOR_TEXT_MUTED,
                halign='left'
            )
            no_intel_card.add_widget(no_intel_label)
            self.content_box.add_widget(no_intel_card)

        # ── 3. ROLE OVERVIEW CARD ──
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
            text="📌 [b]Role Overview & Target Candidate Profile[/b]",
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

        # ── 4. KEY TECHNICAL PILLARS CARD ──
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
            text="⚙️ [b]Core Technical Assessment Pillars[/b]",
            markup=True,
            font_size='15sp',
            color=(0.6, 0.82, 1, 1),
            size_hint_y=None,
            height=24,
            halign='left'
        )
        pillars_title.bind(size=pillars_title.setter('text_size'))
        pillars_card.add_widget(pillars_title)

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

        # ── 5. INTERVIEW TOPICS & REAL-WORLD QUESTIONS ──
        section_label = Label(
            text="🔥 [b]Categorized Topics & Market-Sourced Questions[/b]",
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
        self.title = "Netran AI — Stage 1: JD Research & Intelligence Engine"
        self.sm = ScreenManager(transition=FadeTransition(duration=0.2))

        self.input_screen = InputScreen(name='input')
        self.results_screen = ResultsScreen(name='results')

        self.sm.add_widget(self.input_screen)
        self.sm.add_widget(self.results_screen)

        return self.sm

    def show_results(self, output: Stage1Output):
        self.results_screen.display_results(output)
        self.sm.current = 'results'


if __name__ == '__main__':
    NetranResearchApp().run()
