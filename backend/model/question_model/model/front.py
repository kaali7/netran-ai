"""
Netran AI — Stage 2: Contextual Question & Behavioral Prompt Engine
Module: front.py
Description: Standalone Kivy Desktop GUI application for Stage 2 Question Tree & System Prompt generation.
"""

import json
import os
import sys
import threading
from datetime import datetime
from pathlib import Path

# Add paths for direct execution
current_dir = Path(__file__).resolve().parent
parent_dir = current_dir.parent
root_dir = parent_dir.parent
for d in [str(current_dir), str(parent_dir), str(root_dir)]:
    if d not in sys.path:
        sys.path.insert(0, d)

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
    from .question_generator import generate_stage2_output
    from .schemas import QuestionItem, Stage2Output
except ImportError:
    try:
        from model.question_model.model.question_generator import generate_stage2_output
        from model.question_model.model.schemas import QuestionItem, Stage2Output
    except ImportError:
        from question_generator import generate_stage2_output
        from schemas import Stage2Output

# Window Setup
Window.size = (1024, 768)
Window.clearcolor = (0.05, 0.06, 0.09, 1)  # Deep Obsidian #0D0F17

# Test Paths
TEST_INPUT_DIR = parent_dir / "test" / "input"
TEST_OUTPUT_DIR = parent_dir / "test" / "output"

# Color Tokens
COLOR_BG = (0.05, 0.06, 0.09, 1)        # #0D0F17 Deep Obsidian
COLOR_CARD = (0.09, 0.10, 0.15, 1)      # #171A26 Card Surface
COLOR_BORDER = (0.18, 0.20, 0.30, 1)    # Subtle Card Border
COLOR_PRIMARY = (0.39, 0.40, 0.95, 1)   # #6366F1 Electric Indigo
COLOR_ACCENT = (0.54, 0.36, 0.96, 1)    # #8B5CF6 Violet Neon
COLOR_SUCCESS = (0.06, 0.72, 0.51, 1)   # #10B981 Emerald Green
COLOR_WARNING = (0.96, 0.62, 0.04, 1)   # #F59E0B Amber Flame
COLOR_DANGER = (0.93, 0.27, 0.38, 1)    # #EF4444 Crimson Red
COLOR_TEXT_PRIMARY = (0.95, 0.96, 1.0, 1)
COLOR_TEXT_MUTED = (0.55, 0.58, 0.70, 1)


class GlassCard(BoxLayout):
    """Premium Card Widget with rounded corners and subtle border outline."""
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
    """Custom styled primary button."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ''
        self.background_color = COLOR_PRIMARY
        self.color = COLOR_TEXT_PRIMARY
        self.bold = True
        self.font_size = '14sp'


class Stage2InputScreen(Screen):
    """Screen 1: Job Description & Resume Input Panel with Presets."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.target_seniority = "Senior"
        main_layout = BoxLayout(orientation='vertical', padding=[24, 16, 24, 16], spacing=12)

        # ── TOP BRAND NAV BAR ──
        nav_bar = BoxLayout(orientation='horizontal', size_hint_y=None, height=44, spacing=12)
        logo_box = BoxLayout(orientation='horizontal', spacing=8)
        brand_icon = Label(text="🌳", font_size='22sp', size_hint_x=None, width=30)
        brand_title = Label(
            text="[b]Netran AI[/b]  [color=8B5CF6]•[/color]  [size=14sp][color=8888AA]Stage 2 Question Engine[/color][/size]",
            markup=True,
            font_size='19sp',
            color=COLOR_TEXT_PRIMARY,
            halign='left',
            valign='middle'
        )
        brand_title.bind(size=brand_title.setter('text_size'))
        logo_box.add_widget(brand_icon)
        logo_box.add_widget(brand_title)

        badge_card = GlassCard(
            bg_color=(0.12, 0.15, 0.25, 1),
            border_color=(0.3, 0.35, 0.6, 1),
            radius=14,
            size_hint=(None, None),
            size=(230, 34),
            padding=[10, 4]
        )
        badge_label = Label(
            text="✨ [b]15 Tiered Questions + Eva Prompt[/b]",
            markup=True,
            font_size='11sp',
            color=(0.7, 0.85, 1, 1)
        )
        badge_card.add_widget(badge_label)

        nav_bar.add_widget(logo_box)
        nav_bar.add_widget(badge_card)
        main_layout.add_widget(nav_bar)

        # ── PRESET SELECTOR & SENIORITY BAR ──
        control_bar = BoxLayout(orientation='horizontal', size_hint_y=None, height=38, spacing=8)
        preset_title = Label(
            text="📁 [b]Presets:[/b]",
            markup=True,
            font_size='12sp',
            color=COLOR_TEXT_MUTED,
            size_hint_x=0.15,
            halign='left',
            valign='middle'
        )
        preset_title.bind(size=preset_title.setter('text_size'))
        control_bar.add_widget(preset_title)

        btn1 = Button(
            text="⚡ Backend Systems",
            size_hint_x=0.22,
            background_normal='',
            background_color=(0.14, 0.16, 0.26, 1),
            color=(0.8, 0.9, 1, 1),
            font_size='12sp',
            bold=True
        )
        btn1.bind(on_press=lambda inst: self.load_preset("sample_backend"))

        btn2 = Button(
            text="🎨 Frontend React",
            size_hint_x=0.22,
            background_normal='',
            background_color=(0.14, 0.16, 0.26, 1),
            color=(0.8, 0.9, 1, 1),
            font_size='12sp',
            bold=True
        )
        btn2.bind(on_press=lambda inst: self.load_preset("sample_frontend"))

        btn3 = Button(
            text="🤖 Full Stack AI",
            size_hint_x=0.22,
            background_normal='',
            background_color=(0.14, 0.16, 0.26, 1),
            color=(0.8, 0.9, 1, 1),
            font_size='12sp',
            bold=True
        )
        btn3.bind(on_press=lambda inst: self.load_preset("sample_fullstack"))

        control_bar.add_widget(btn1)
        control_bar.add_widget(btn2)
        control_bar.add_widget(btn3)

        # Seniority Selector Buttons
        sen_label = Label(text="Level:", font_size='12sp', color=COLOR_TEXT_MUTED, size_hint_x=0.08)
        control_bar.add_widget(sen_label)

        self.sen_junior_btn = Button(text="Junior", size_hint_x=0.10, background_normal='', background_color=(0.12, 0.14, 0.2, 1), font_size='11sp')
        self.sen_mid_btn = Button(text="Mid", size_hint_x=0.10, background_normal='', background_color=(0.12, 0.14, 0.2, 1), font_size='11sp')
        self.sen_senior_btn = Button(text="Senior", size_hint_x=0.10, background_normal='', background_color=COLOR_PRIMARY, font_size='11sp', bold=True)

        self.sen_junior_btn.bind(on_press=lambda inst: self.set_seniority("Junior"))
        self.sen_mid_btn.bind(on_press=lambda inst: self.set_seniority("Mid"))
        self.sen_senior_btn.bind(on_press=lambda inst: self.set_seniority("Senior"))

        control_bar.add_widget(self.sen_junior_btn)
        control_bar.add_widget(self.sen_mid_btn)
        control_bar.add_widget(self.sen_senior_btn)

        main_layout.add_widget(control_bar)

        # ── SIDE-BY-SIDE DUAL INPUT CARDS ──
        dual_container = BoxLayout(orientation='horizontal', spacing=12, size_hint=(1, 1))

        # 1. Job Description Card
        jd_card = GlassCard(bg_color=COLOR_CARD, border_color=COLOR_BORDER, radius=12, orientation='vertical', padding=12, spacing=6, size_hint_x=0.5)
        jd_head = Label(text="📋 [b]Job Description / Key Pillars[/b]", markup=True, font_size='13sp', color=(0.7, 0.85, 1, 1), size_hint_y=None, height=22, halign='left')
        jd_head.bind(size=jd_head.setter('text_size'))
        self.jd_input = TextInput(
            hint_text="Paste Job Description text or click a preset above...",
            background_color=(0.06, 0.07, 0.11, 1),
            foreground_color=COLOR_TEXT_PRIMARY,
            hint_text_color=(0.35, 0.38, 0.48, 1),
            cursor_color=COLOR_PRIMARY,
            multiline=True,
            padding=[10, 10, 10, 10],
            font_size='12sp'
        )
        jd_card.add_widget(jd_head)
        jd_card.add_widget(self.jd_input)

        # 2. Candidate Resume Card
        resume_card = GlassCard(bg_color=COLOR_CARD, border_color=COLOR_BORDER, radius=12, orientation='vertical', padding=12, spacing=6, size_hint_x=0.5)
        resume_head = Label(text="📄 [b]Candidate Resume Text[/b]", markup=True, font_size='13sp', color=(0.7, 0.85, 1, 1), size_hint_y=None, height=22, halign='left')
        resume_head.bind(size=resume_head.setter('text_size'))
        self.resume_input = TextInput(
            hint_text="Paste Candidate Resume text or click a preset above...",
            background_color=(0.06, 0.07, 0.11, 1),
            foreground_color=COLOR_TEXT_PRIMARY,
            hint_text_color=(0.35, 0.38, 0.48, 1),
            cursor_color=COLOR_PRIMARY,
            multiline=True,
            padding=[10, 10, 10, 10],
            font_size='12sp'
        )
        resume_card.add_widget(resume_head)
        resume_card.add_widget(self.resume_input)

        dual_container.add_widget(jd_card)
        dual_container.add_widget(resume_card)
        main_layout.add_widget(dual_container)

        # ── ACTION BUTTON BAR ──
        btn_bar = BoxLayout(orientation='horizontal', size_hint_y=None, height=44, spacing=12)
        save_btn = Button(
            text="💾 Save Inputs to test/input/",
            size_hint_x=0.35,
            background_normal='',
            background_color=(0.16, 0.18, 0.28, 1),
            color=(0.8, 0.9, 1, 1),
            font_size='12sp'
        )
        save_btn.bind(on_press=self.save_pasted_inputs)

        self.generate_btn = PrimaryButton(
            text="🚀 Generate Question Tree & System Prompt",
            size_hint_x=0.65
        )
        self.generate_btn.bind(on_press=self.start_generation)

        btn_bar.add_widget(save_btn)
        btn_bar.add_widget(self.generate_btn)
        main_layout.add_widget(btn_bar)

        # ── STATUS FOOTER ──
        status_card = GlassCard(bg_color=(0.07, 0.08, 0.13, 1), border_color=(0.14, 0.16, 0.24, 1), radius=10, size_hint_y=None, height=34, padding=[10, 4])
        self.status_label = Label(text="● Idle — Select preset or paste JD & Resume to start Stage 2", font_size='12sp', color=COLOR_TEXT_MUTED, halign='left', valign='middle')
        self.status_label.bind(size=self.status_label.setter('text_size'))
        status_card.add_widget(self.status_label)
        main_layout.add_widget(status_card)

        self.add_widget(main_layout)

    def set_seniority(self, level: str):
        self.target_seniority = level
        for btn, l in [(self.sen_junior_btn, "Junior"), (self.sen_mid_btn, "Mid"), (self.sen_senior_btn, "Senior")]:
            if l == level:
                btn.background_color = COLOR_PRIMARY
                btn.bold = True
            else:
                btn.background_color = (0.12, 0.14, 0.2, 1)
                btn.bold = False

    def load_preset(self, preset_name: str):
        pdir = TEST_INPUT_DIR / preset_name
        jd_file = pdir / "sample_job_detail.json"
        res_file = pdir / "sample_resume.json"

        if not (jd_file.exists() and res_file.exists()):
            jd_file = TEST_INPUT_DIR / "sample_job_detail.json"
            res_file = TEST_INPUT_DIR / "sample_resume.json"

        if jd_file.exists() and res_file.exists():
            with open(jd_file, "r", encoding="utf-8") as f:
                jd_data = json.load(f)
            with open(res_file, "r", encoding="utf-8") as f:
                res_data = json.load(f)

            self.jd_input.text = jd_data.get("jd_text", "").strip()
            self.resume_input.text = res_data.get("resume_text", "").strip()
            self.set_seniority(jd_data.get("target_seniority", "Senior"))

            self.status_label.text = f"● Loaded preset: '{preset_name}'"
            self.status_label.color = COLOR_SUCCESS
        else:
            self.status_label.text = f"⚠️ Preset files for '{preset_name}' not found."
            self.status_label.color = COLOR_WARNING

    def save_pasted_inputs(self, instance):
        jd_text = self.jd_input.text.strip()
        resume_text = self.resume_input.text.strip()

        if not jd_text or not resume_text:
            self.status_label.text = "⚠️ Cannot save empty JD or Resume text."
            self.status_label.color = COLOR_WARNING
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        preset_dir = TEST_INPUT_DIR / f"sample_custom_{timestamp}"
        preset_dir.mkdir(parents=True, exist_ok=True)

        jd_payload = {"company": "Custom Company", "role": "Custom Role", "target_seniority": self.target_seniority, "jd_text": jd_text}
        res_payload = {"candidate_name": "Custom Candidate", "resume_text": resume_text}

        with open(preset_dir / "sample_job_detail.json", "w", encoding="utf-8") as f:
            json.dump(jd_payload, f, indent=2)
        with open(preset_dir / "sample_resume.json", "w", encoding="utf-8") as f:
            json.dump(res_payload, f, indent=2)

        self.status_label.text = f"✅ Saved inputs to test/input/{preset_dir.name}/"
        self.status_label.color = COLOR_SUCCESS

    def start_generation(self, instance):
        jd_text = self.jd_input.text.strip()
        resume_text = self.resume_input.text.strip()

        if not jd_text or not resume_text:
            self.status_label.text = "⚠️ Please provide both Job Description and Candidate Resume text."
            self.status_label.color = COLOR_WARNING
            return

        self.generate_btn.disabled = True
        self.status_label.color = (0.7, 0.8, 1, 1)
        self.status_label.text = "⏳ Generating 15-question tree & interviewer system prompt..."

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_id = f"sess_{timestamp}"
        session_dir = str(TEST_OUTPUT_DIR / session_id)

        # Temporary resume file for parser input
        temp_resume_path = TEST_INPUT_DIR / f"_temp_gui_resume_{timestamp}.txt"
        with open(temp_resume_path, "w", encoding="utf-8") as f:
            f.write(resume_text)

        threading.Thread(target=self._run_async, args=(session_id, jd_text, str(temp_resume_path), session_dir), daemon=True).start()

    def _run_async(self, session_id, jd_text, temp_resume_path, session_dir):
        try:
            output: Stage2Output = generate_stage2_output(
                session_id=session_id,
                jd_text=jd_text,
                resume_path=temp_resume_path,
                target_seniority=self.target_seniority,
                output_dir=session_dir
            )
            # Cleanup temp resume
            if os.path.exists(temp_resume_path):
                os.remove(temp_resume_path)

            Clock.schedule_once(lambda dt: self._on_success(output))
        except Exception as e:
            if os.path.exists(temp_resume_path):
                os.remove(temp_resume_path)
            err_msg = str(e)
            Clock.schedule_once(lambda dt: self._on_error(err_msg))

    def _on_success(self, output: Stage2Output):
        self.generate_btn.disabled = False
        self.status_label.text = "✅ Stage 2 generation complete! Displaying Question Tree..."
        self.status_label.color = COLOR_SUCCESS
        app = App.get_running_app()
        app.show_results(output)

    def _on_error(self, err_msg):
        self.generate_btn.disabled = False
        self.status_label.text = f"❌ Stage 2 Error: {err_msg[:90]}"
        self.status_label.color = COLOR_DANGER


class Stage2ResultsScreen(Screen):
    """Screen 2: Visual Display for 15-Question Tree & Eva System Prompt."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_output = None
        main_layout = BoxLayout(orientation='vertical', padding=[24, 16, 24, 16], spacing=12)

        # ── NAV HEADER BAR ──
        nav_bar = BoxLayout(orientation='horizontal', size_hint_y=None, height=44, spacing=12)

        back_btn = Button(
            text="← Back to Input",
            size_hint_x=0.24,
            background_normal='',
            background_color=(0.14, 0.16, 0.24, 1),
            color=COLOR_TEXT_PRIMARY,
            font_size='13sp',
            bold=True
        )
        back_btn.bind(on_press=self.go_back)

        header_title = Label(
            text="🎯 [b]Stage 2: Question Tree & System Prompt[/b]",
            markup=True,
            font_size='18sp',
            color=COLOR_TEXT_PRIMARY,
            halign='left',
            valign='middle'
        )
        header_title.bind(size=header_title.setter('text_size'))

        copy_q_btn = Button(
            text="📄 Copy Questions JSON",
            size_hint_x=0.25,
            background_normal='',
            background_color=(0.18, 0.22, 0.35, 1),
            color=(0.8, 0.9, 1, 1),
            font_size='11sp'
        )
        copy_q_btn.bind(on_press=self.copy_questions_json)

        copy_p_btn = Button(
            text="🤖 Copy Prompt",
            size_hint_x=0.20,
            background_normal='',
            background_color=(0.22, 0.18, 0.35, 1),
            color=(0.9, 0.8, 1, 1),
            font_size='11sp'
        )
        copy_p_btn.bind(on_press=self.copy_prompt_text)

        nav_bar.add_widget(back_btn)
        nav_bar.add_widget(header_title)
        nav_bar.add_widget(copy_q_btn)
        nav_bar.add_widget(copy_p_btn)
        main_layout.add_widget(nav_bar)

        # ── SCROLLABLE CONTENT AREA ──
        self.scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False)
        self.content_box = GridLayout(cols=1, spacing=14, size_hint_y=None)
        self.content_box.bind(minimum_height=self.content_box.setter('height'))
        self.scroll.add_widget(self.content_box)
        main_layout.add_widget(self.scroll)

        self.add_widget(main_layout)

    def go_back(self, instance):
        app = App.get_running_app()
        app.sm.current = 'input'

    def copy_questions_json(self, instance):
        if self.current_output and hasattr(self.current_output, 'question_tree'):
            from kivy.core.clipboard import Clipboard
            json_str = json.dumps([q.model_dump() for q in self.current_output.question_tree], indent=2)
            Clipboard.copy(json_str)
            instance.text = "✅ Copied!"
            Clock.schedule_once(lambda dt: setattr(instance, 'text', '📄 Copy Questions JSON'), 2)

    def copy_prompt_text(self, instance):
        if self.current_output and hasattr(self.current_output, 'interviewer_system_prompt'):
            from kivy.core.clipboard import Clipboard
            Clipboard.copy(self.current_output.interviewer_system_prompt)
            instance.text = "✅ Copied!"
            Clock.schedule_once(lambda dt: setattr(instance, 'text', '🤖 Copy Prompt'), 2)

    def display_results(self, output: Stage2Output):
        self.current_output = output
        self.content_box.clear_widgets()

        # ── 1. SYSTEM PROMPT CARD (`interviewer_behavior.json`) ──
        prompt_card = GlassCard(
            bg_color=(0.10, 0.12, 0.20, 1),
            border_color=(0.28, 0.32, 0.52, 1),
            radius=12,
            orientation='vertical',
            padding=16,
            spacing=10,
            size_hint_y=None
        )

        card_head = BoxLayout(orientation='horizontal', size_hint_y=None, height=26)
        prompt_title = Label(
            text="🤖 [b]Interviewer System Prompt & Behavior Rules (Eva Persona)[/b]",
            markup=True,
            font_size='15sp',
            color=(0.7, 0.85, 1, 1),
            size_hint_x=0.75,
            halign='left',
            valign='middle'
        )
        prompt_title.bind(size=prompt_title.setter('text_size'))

        badge_latency = Label(
            text="[color=10B981]⚡ 1-2 Sentences Max[/color]",
            markup=True,
            font_size='11sp',
            size_hint_x=0.25,
            halign='right',
            valign='middle'
        )
        badge_latency.bind(size=badge_latency.setter('text_size'))

        card_head.add_widget(prompt_title)
        card_head.add_widget(badge_latency)
        prompt_card.add_widget(card_head)

        prompt_text_label = Label(
            text=f'"{output.interviewer_system_prompt}"',
            font_size='12sp',
            color=(0.90, 0.92, 0.98, 1),
            size_hint_y=None,
            halign='left',
            valign='top'
        )
        prompt_text_label.bind(width=lambda *x: prompt_text_label.setter('text_size')(prompt_text_label, (prompt_text_label.width, None)))
        prompt_text_label.bind(texture_size=lambda *x: setattr(prompt_text_label, 'height', prompt_text_label.texture_size[1]))
        prompt_card.add_widget(prompt_text_label)

        prompt_card.height = 55 + prompt_text_label.height
        self.content_box.add_widget(prompt_card)

        # ── 2. QUESTION TREE HEADER ──
        q_section_head = Label(
            text=f"🔥 [b]15-Question Stratified Question Tree ({len(output.question_tree)} Items)[/b]",
            markup=True,
            font_size='16sp',
            color=(1.0, 0.82, 0.4, 1),
            size_hint_y=None,
            height=28,
            halign='left'
        )
        q_section_head.bind(size=q_section_head.setter('text_size'))
        self.content_box.add_widget(q_section_head)

        difficulty_badges = {
            "Junior": "[color=10B981]🟢 Junior[/color]",
            "Mid": "[color=F59E0B]🟡 Mid[/color]",
            "Senior": "[color=EF4444]🔴 Senior[/color]"
        }

        # ── 3. QUESTION CARDS (`interview_questions.json`) ──
        for q in output.question_tree:
            q_card = GlassCard(
                bg_color=(0.08, 0.09, 0.14, 1),
                border_color=(0.20, 0.22, 0.34, 1),
                radius=10,
                orientation='vertical',
                padding=14,
                spacing=8,
                size_hint_y=None
            )

            # Determine Tier Label
            if q.id <= 2:
                tier_label = "[color=10B981]Tier 1 (Foundations)[/color]"
            elif q.id <= 12:
                tier_label = "[color=F59E0B]Tier 2 (Core Arch)[/color]"
            else:
                tier_label = "[color=EF4444]Tier 3 (System Design)[/color]"

            diff_tag = difficulty_badges.get(q.difficulty, q.difficulty)
            header_str = f"[b]Q{q.id}. {q.topic}[/b]   [size=11sp]•   {diff_tag}   •   {tier_label}[/size]"

            q_title = Label(text=header_str, markup=True, font_size='13sp', size_hint_y=None, height=22, halign='left')
            q_title.bind(size=q_title.setter('text_size'))
            q_card.add_widget(q_title)

            q_text = Label(text=q.question_text, font_size='13sp', color=COLOR_TEXT_PRIMARY, size_hint_y=None, halign='left', valign='top')
            q_text.bind(width=lambda *x: q_text.setter('text_size')(q_text, (q_text.width, None)))
            q_text.bind(texture_size=lambda *x: setattr(q_text, 'height', q_text.texture_size[1]))
            q_card.add_widget(q_text)

            keywords_str = "  •  ".join(q.expected_keywords) if q.expected_keywords else "General Architecture"
            kw_label = Label(
                text=f"[color=8888AA]Expected Keywords:[/color]  [color=70C0FF]{keywords_str}[/color]",
                markup=True,
                font_size='11sp',
                size_hint_y=None,
                height=18,
                halign='left'
            )
            kw_label.bind(size=kw_label.setter('text_size'))
            q_card.add_widget(kw_label)

            if q.resume_reference:
                res_label = Label(
                    text=f"[color=8888AA]Resume Mapped Project:[/color]  [color=F59E0B]{q.resume_reference}[/color]",
                    markup=True,
                    font_size='11sp',
                    size_hint_y=None,
                    height=18,
                    halign='left'
                )
                res_label.bind(size=res_label.setter('text_size'))
                q_card.add_widget(res_label)
                q_card.height = 75 + q_text.height
            else:
                q_card.height = 55 + q_text.height

            self.content_box.add_widget(q_card)


class NetranQuestionApp(App):
    def build(self):
        self.title = "Netran AI — Stage 2: Question Engine & System Prompt Client"
        self.sm = ScreenManager(transition=FadeTransition(duration=0.2))

        self.input_screen = Stage2InputScreen(name='input')
        self.results_screen = Stage2ResultsScreen(name='results')

        self.sm.add_widget(self.input_screen)
        self.sm.add_widget(self.results_screen)

        return self.sm

    def show_results(self, output: Stage2Output):
        self.results_screen.display_results(output)
        self.sm.current = 'results'


if __name__ == '__main__':
    NetranQuestionApp().run()
