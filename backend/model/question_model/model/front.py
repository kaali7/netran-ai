"""
Netran AI — Stage 2: Contextual Question & Behavioral Prompt Engine
Module: front.py
Description: Standalone Kivy Desktop GUI application for Stage 2 Question Tree, Resume Analysis, & System Prompt generation.
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
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import FadeTransition, Screen, ScreenManager
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput

try:
    from .pipeline import Stage2Pipeline
    from .schemas import QuestionItem, Stage2Output
except ImportError:
    try:
        from model.question_model.model.pipeline import Stage2Pipeline
        from model.question_model.model.schemas import QuestionItem, Stage2Output
    except ImportError:
        from pipeline import Stage2Pipeline
        from schemas import Stage2Output

# Window Setup
Window.size = (1080, 810)
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
        brand_icon = Label(text="[*]", font_size='18sp', bold=True, color=COLOR_PRIMARY, size_hint_x=None, width=30)
        brand_title = Label(
            text="[b]Netran AI[/b]  [color=8B5CF6]•[/color]  [size=14sp][color=8888AA]Stage 2 Contextual Question Engine[/color][/size]",
            markup=True,
            font_size='19sp',
            color=COLOR_TEXT_PRIMARY,
            halign='left',
            valign='middle'
        )
        brand_title.bind(size=brand_title.setter('text_size'))
        logo_box.add_widget(brand_icon)
        logo_box.add_widget(brand_title)

        history_btn = Button(
            text="[History] Previous Outputs",
            size_hint=(None, None),
            size=(190, 34),
            background_normal='',
            background_color=(0.18, 0.22, 0.35, 1),
            color=(0.8, 0.9, 1, 1),
            font_size='11sp',
            bold=True
        )
        history_btn.bind(on_press=self.open_history_modal)

        badge_card = GlassCard(
            bg_color=(0.12, 0.15, 0.25, 1),
            border_color=(0.3, 0.35, 0.6, 1),
            radius=14,
            size_hint=(None, None),
            size=(230, 34),
            padding=[10, 4]
        )
        badge_label = Label(
            text="[b]15 Tiered Questions + Eva Prompt[/b]",
            markup=True,
            font_size='11sp',
            color=(0.7, 0.85, 1, 1)
        )
        badge_card.add_widget(badge_label)

        nav_bar.add_widget(logo_box)
        nav_bar.add_widget(history_btn)
        nav_bar.add_widget(badge_card)
        main_layout.add_widget(nav_bar)

        # ── PRESET SELECTOR & SENIORITY BAR ──
        control_bar = BoxLayout(orientation='horizontal', size_hint_y=None, height=38, spacing=8)
        preset_title = Label(
            text="[b]Presets:[/b]",
            markup=True,
            font_size='12sp',
            color=COLOR_TEXT_MUTED,
            size_hint_x=0.12,
            halign='left',
            valign='middle'
        )
        preset_title.bind(size=preset_title.setter('text_size'))
        control_bar.add_widget(preset_title)

        btn1 = Button(
            text="Backend Systems",
            size_hint_x=0.18,
            background_normal='',
            background_color=(0.14, 0.16, 0.26, 1),
            color=(0.8, 0.9, 1, 1),
            font_size='11sp',
            bold=True
        )
        btn1.bind(on_press=lambda inst: self.load_preset("sample_backend"))

        btn2 = Button(
            text="Frontend React",
            size_hint_x=0.18,
            background_normal='',
            background_color=(0.14, 0.16, 0.26, 1),
            color=(0.8, 0.9, 1, 1),
            font_size='11sp',
            bold=True
        )
        btn2.bind(on_press=lambda inst: self.load_preset("sample_frontend"))

        btn3 = Button(
            text="Full Stack AI",
            size_hint_x=0.18,
            background_normal='',
            background_color=(0.14, 0.16, 0.26, 1),
            color=(0.8, 0.9, 1, 1),
            font_size='11sp',
            bold=True
        )
        btn3.bind(on_press=lambda inst: self.load_preset("sample_fullstack"))

        control_bar.add_widget(btn1)
        control_bar.add_widget(btn2)
        control_bar.add_widget(btn3)

        # Seniority Selector Buttons
        sen_label = Label(text="[b]Seniority:[/b]", markup=True, font_size='12sp', color=COLOR_TEXT_MUTED, size_hint_x=0.10)
        control_bar.add_widget(sen_label)

        self.sen_btns = {}
        for sen in ["Junior", "Mid", "Senior", "Lead", "Staff"]:
            b = Button(
                text=sen,
                size_hint_x=0.08,
                background_normal='',
                background_color=COLOR_PRIMARY if sen == "Senior" else (0.12, 0.14, 0.2, 1),
                color=COLOR_TEXT_PRIMARY if sen == "Senior" else COLOR_TEXT_MUTED,
                font_size='11sp',
                bold=(sen == "Senior")
            )
            b.bind(on_press=lambda inst, level=sen: self.set_seniority(level))
            self.sen_btns[sen] = b
            control_bar.add_widget(b)

        main_layout.add_widget(control_bar)

        # ── SIDE-BY-SIDE DUAL INPUT CARDS ──
        dual_container = BoxLayout(orientation='horizontal', spacing=12, size_hint=(1, 1))

        # 1. Job Description Card
        jd_card = GlassCard(bg_color=COLOR_CARD, border_color=COLOR_BORDER, radius=12, orientation='vertical', padding=12, spacing=6, size_hint_x=0.5)
        jd_head = Label(text="[b]Job Description / Stage 1 Rubric JSON[/b]", markup=True, font_size='13sp', color=(0.7, 0.85, 1, 1), size_hint_y=None, height=22, halign='left')
        jd_head.bind(size=jd_head.setter('text_size'))
        self.jd_input = TextInput(
            hint_text="Paste Job Description text or Stage 1 Output JSON...",
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
        resume_head = Label(text="[b]Candidate Resume Text[/b]", markup=True, font_size='13sp', color=(0.7, 0.85, 1, 1), size_hint_y=None, height=22, halign='left')
        resume_head.bind(size=resume_head.setter('text_size'))
        self.resume_input = TextInput(
            hint_text="Paste Candidate Resume text here...",
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
        action_bar = BoxLayout(orientation='horizontal', size_hint_y=None, height=44, spacing=12)
        save_btn = Button(
            text="[Save] Save Inputs (JSON)",
            size_hint_x=0.30,
            background_normal='',
            background_color=(0.16, 0.18, 0.28, 1),
            color=(0.8, 0.9, 1, 1),
            font_size='12sp'
        )
        save_btn.bind(on_press=self.save_pasted_inputs)

        self.generate_btn = PrimaryButton(
            text="Generate Question Tree & Behavioral System Prompt",
            size_hint_x=0.70
        )
        self.generate_btn.bind(on_press=self.start_generation)

        action_bar.add_widget(save_btn)
        action_bar.add_widget(self.generate_btn)
        main_layout.add_widget(action_bar)

        # ── FOOTER STATUS BAR ──
        status_card = GlassCard(
            bg_color=(0.07, 0.08, 0.13, 1),
            border_color=(0.14, 0.16, 0.24, 1),
            radius=10,
            size_hint_y=None,
            height=34,
            padding=[12, 6]
        )
        self.status_label = Label(
            text="[Idle] Select preset or paste custom JD & Resume to run Stage 2",
            font_size='12sp',
            color=COLOR_TEXT_MUTED,
            halign='left',
            valign='middle'
        )
        self.status_label.bind(size=self.status_label.setter('text_size'))
        status_card.add_widget(self.status_label)
        main_layout.add_widget(status_card)

        self.add_widget(main_layout)

    def set_seniority(self, level: str):
        self.target_seniority = level
        for sen, b in self.sen_btns.items():
            if sen == level:
                b.background_color = COLOR_PRIMARY
                b.color = COLOR_TEXT_PRIMARY
                b.bold = True
            else:
                b.background_color = (0.12, 0.14, 0.2, 1)
                b.color = COLOR_TEXT_MUTED
                b.bold = False

    def load_preset(self, preset_name: str):
        pdir = TEST_INPUT_DIR / preset_name
        jd_file = pdir / "sample_job_detail.json"
        res_file = pdir / "sample_resume.json"

        if jd_file.exists() and res_file.exists():
            try:
                with open(jd_file, "r", encoding="utf-8-sig") as f:
                    content = f.read().strip()
                    jd_data = json.loads(content) if content else {}
                with open(res_file, "r", encoding="utf-8-sig") as f:
                    content_res = f.read().strip()
                    res_data = json.loads(content_res) if content_res else {}

                if "jd_text" in jd_data:
                    self.jd_input.text = jd_data.get("jd_text", "").strip()
                else:
                    self.jd_input.text = json.dumps(jd_data, indent=2)

                self.resume_input.text = res_data.get("resume_text", "").strip()
                target_sen = jd_data.get("target_seniority", "Senior")
                if "parsed_jd" in jd_data and isinstance(jd_data["parsed_jd"], dict):
                    target_sen = jd_data["parsed_jd"].get("target_seniority", target_sen)
                self.set_seniority(target_sen)

                self.status_label.text = f"[Loaded] Loaded preset: '{preset_name}'"
                self.status_label.color = COLOR_SUCCESS
            except Exception as e:
                self.status_label.text = f"[Error] Preset read error for '{preset_name}': {e}"
                self.status_label.color = COLOR_DANGER
        else:
            self.status_label.text = f"[Error] Preset files for '{preset_name}' not found."
            self.status_label.color = COLOR_WARNING

    def save_pasted_inputs(self, instance):
        jd_text = self.jd_input.text.strip()
        resume_text = self.resume_input.text.strip()

        if not jd_text or not resume_text:
            self.status_label.text = "[Error] JD and Resume fields cannot be empty."
            self.status_label.color = COLOR_WARNING
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        preset_dir = TEST_INPUT_DIR / f"custom_{timestamp}"
        preset_dir.mkdir(parents=True, exist_ok=True)

        jd_payload = {"company": "Target Company", "role": "Custom Role", "target_seniority": self.target_seniority, "jd_text": jd_text}
        res_payload = {"candidate_name": "Custom Candidate", "target_role": "Custom Role", "resume_text": resume_text}

        with open(preset_dir / "sample_job_detail.json", "w", encoding="utf-8") as f:
            json.dump(jd_payload, f, indent=2)
        with open(preset_dir / "sample_resume.json", "w", encoding="utf-8") as f:
            json.dump(res_payload, f, indent=2)

        self.status_label.text = f"[Saved] Saved custom inputs to test/input/{preset_dir.name}"
        self.status_label.color = COLOR_SUCCESS

    def open_history_modal(self, instance):
        """Opens popup modal to view and load previously saved Stage 2 output session folders."""
        TEST_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        session_dirs = sorted(
            [d for d in TEST_OUTPUT_DIR.glob("sess_*") if d.is_dir()],
            key=lambda d: d.name,
            reverse=True
        )

        content = BoxLayout(orientation='vertical', padding=12, spacing=10)
        title_lbl = Label(
            text="[b]Select Saved Stage 2 Session Output (test/output/):[/b]",
            markup=True,
            font_size='14sp',
            size_hint_y=None,
            height=26,
            color=COLOR_TEXT_PRIMARY
        )
        content.add_widget(title_lbl)

        scroll = ScrollView(size_hint=(1, 1))
        file_grid = GridLayout(cols=1, spacing=8, size_hint_y=None)
        file_grid.bind(minimum_height=file_grid.setter('height'))

        popup = Popup(
            title="Saved Session History",
            content=content,
            size_hint=(0.85, 0.85),
            background_color=(0.08, 0.09, 0.15, 0.95)
        )

        if session_dirs:
            for sdir in session_dirs:
                btn = Button(
                    text=f"[Session Folder] {sdir.name}",
                    size_hint_y=None,
                    height=38,
                    background_normal='',
                    background_color=(0.14, 0.17, 0.28, 1),
                    color=(0.85, 0.92, 1, 1),
                    font_size='12sp'
                )
                btn.bind(on_press=lambda inst, p=sdir: self._load_saved_session_folder(p, popup))
                file_grid.add_widget(btn)
        else:
            no_files_lbl = Label(text="No saved Stage 2 output session folders found.", font_size='12sp', color=COLOR_TEXT_MUTED)
            file_grid.add_widget(no_files_lbl)

        scroll.add_widget(file_grid)
        content.add_widget(scroll)

        close_btn = Button(text="Close", size_hint_y=None, height=36, background_normal='', background_color=(0.25, 0.28, 0.38, 1))
        close_btn.bind(on_press=popup.dismiss)
        content.add_widget(close_btn)

        popup.open()

    def _load_saved_session_folder(self, session_dir: Path, popup: Popup):
        popup.dismiss()
        try:
            questions_file = session_dir / "interview_questions.json"
            behavior_file = session_dir / "interviewer_behavior.json"
            analysis_file = session_dir / "resume_analysis.json"

            if not (questions_file.exists() and behavior_file.exists()):
                raise FileNotFoundError("Session directory missing required JSON files.")

            with open(questions_file, "r", encoding="utf-8") as f:
                q_tree = json.load(f)
            with open(behavior_file, "r", encoding="utf-8") as f:
                b_data = json.load(f)

            r_analysis = {}
            if analysis_file.exists():
                with open(analysis_file, "r", encoding="utf-8") as f:
                    r_analysis = json.load(f)

            output = Stage2Output.model_validate({
                "session_id": session_dir.name,
                "resume_analysis": r_analysis or {
                    "matched_skills": [], "missing_or_gap_skills": [], "resume_red_flags": [], "key_projects_to_probe": []
                },
                "interview_questions": q_tree,
                "interviewer_behavior": b_data
            })
            self.status_label.text = f"[Loaded] Loaded session history: '{session_dir.name}'"
            self.status_label.color = COLOR_SUCCESS
            app = App.get_running_app()
            app.show_results(output)
        except Exception as e:
            self.status_label.text = f"[Error] Failed to load session folder '{session_dir.name}': {e}"
            self.status_label.color = COLOR_DANGER

    def start_generation(self, instance):
        jd_text = self.jd_input.text.strip()
        resume_text = self.resume_input.text.strip()

        if not jd_text or not resume_text:
            self.status_label.text = "[Error] Please provide both Job Description and Candidate Resume text."
            self.status_label.color = COLOR_WARNING
            return

        self.generate_btn.disabled = True
        self.status_label.color = (0.7, 0.8, 1, 1)
        self.status_label.text = "[Processing] Synthesizing Resume Gap Analysis & 15-Question Branching Tree..."

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_id = f"sess_{timestamp}"
        output_dir = str(TEST_OUTPUT_DIR / session_id)

        # Temporary write resume text file for parser ingestion
        temp_resume_file = TEST_INPUT_DIR / f"temp_resume_{timestamp}.txt"
        with open(temp_resume_file, "w", encoding="utf-8") as f:
            f.write(resume_text)

        threading.Thread(
            target=self._run_async,
            args=(session_id, jd_text, str(temp_resume_file), self.target_seniority, output_dir, temp_resume_file),
            daemon=True
        ).start()

    def _run_async(self, session_id, jd_text, resume_path, target_seniority, output_dir, temp_file):
        try:
            pipeline = Stage2Pipeline()
            output = pipeline.run(
                session_id=session_id,
                jd_input=jd_text,
                resume_path=resume_path,
                target_seniority=target_seniority,
                output_dir=output_dir
            )
            Clock.schedule_once(lambda dt: self._on_success(output))
        except Exception as e:
            err_msg = str(e)
            Clock.schedule_once(lambda dt: self._on_error(err_msg))
        finally:
            if temp_file and os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except Exception:
                    pass

    def _on_success(self, output: Stage2Output):
        self.generate_btn.disabled = False
        self.status_label.text = "[Success] Stage 2 Synthesis complete! Displaying Question Tree & System Prompt..."
        self.status_label.color = COLOR_SUCCESS
        app = App.get_running_app()
        app.show_results(output)

    def _on_error(self, err_msg):
        self.generate_btn.disabled = False
        self.status_label.text = f"[Pipeline Error] {err_msg[:90]}"
        self.status_label.color = COLOR_DANGER


class Stage2ResultsScreen(Screen):
    """Screen 2: Stage 2 Assessment Artifacts (Resume Analysis, Question Tree & System Prompt)."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_output = None
        main_layout = BoxLayout(orientation='vertical', padding=[24, 16, 24, 16], spacing=12)

        # ── NAV HEADER BAR ──
        nav_bar = BoxLayout(orientation='horizontal', size_hint_y=None, height=44, spacing=10)

        back_btn = Button(
            text="<- Back to Input",
            size_hint_x=0.22,
            background_normal='',
            background_color=(0.14, 0.16, 0.24, 1),
            color=COLOR_TEXT_PRIMARY,
            font_size='12sp',
            bold=True
        )
        back_btn.bind(on_press=self.go_back)

        header_title = Label(
            text="[b]Stage 2: Adaptive Intelligence Dashboard[/b]",
            markup=True,
            font_size='18sp',
            color=COLOR_TEXT_PRIMARY,
            halign='left',
            valign='middle'
        )
        header_title.bind(size=header_title.setter('text_size'))

        history_btn = Button(
            text="[History]",
            size_hint_x=0.14,
            background_normal='',
            background_color=(0.18, 0.22, 0.35, 1),
            color=(0.8, 0.9, 1, 1),
            font_size='11sp',
            bold=True
        )
        history_btn.bind(on_press=self.open_history_modal)

        copy_q_btn = Button(
            text="[Copy Questions]",
            size_hint_x=0.18,
            background_normal='',
            background_color=(0.18, 0.22, 0.35, 1),
            color=(0.8, 0.9, 1, 1),
            font_size='11sp'
        )
        copy_q_btn.bind(on_press=self.copy_questions_json)

        copy_p_btn = Button(
            text="[Copy Prompt]",
            size_hint_x=0.16,
            background_normal='',
            background_color=(0.22, 0.18, 0.35, 1),
            color=(0.9, 0.8, 1, 1),
            font_size='11sp'
        )
        copy_p_btn.bind(on_press=self.copy_prompt_text)

        nav_bar.add_widget(back_btn)
        nav_bar.add_widget(header_title)
        nav_bar.add_widget(history_btn)
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

    def open_history_modal(self, instance):
        app = App.get_running_app()
        app.input_screen.open_history_modal(instance)

    def copy_questions_json(self, instance):
        if self.current_output and hasattr(self.current_output, 'interview_questions'):
            from kivy.core.clipboard import Clipboard
            json_str = json.dumps([q.model_dump() for q in self.current_output.interview_questions], indent=2)
            Clipboard.copy(json_str)
            instance.text = "[Copied!]"
            Clock.schedule_once(lambda dt: setattr(instance, 'text', '[Copy Questions]'), 2)

    def copy_prompt_text(self, instance):
        if self.current_output and hasattr(self.current_output, 'interviewer_behavior'):
            from kivy.core.clipboard import Clipboard
            Clipboard.copy(self.current_output.interviewer_behavior.interviewer_system_prompt)
            instance.text = "[Copied!]"
            Clock.schedule_once(lambda dt: setattr(instance, 'text', '[Copy Prompt]'), 2)

    def _create_auto_label(self, text, font_size='12sp', color=COLOR_TEXT_PRIMARY, markup=False):
        lbl = Label(
            text=text,
            markup=markup,
            font_size=font_size,
            color=color,
            size_hint_y=None,
            halign='left',
            valign='top'
        )
        lbl.bind(width=lambda inst, w: setattr(inst, 'text_size', (w, None)))
        lbl.bind(texture_size=lambda inst, tz: setattr(inst, 'height', tz[1]))
        return lbl

    def display_results(self, output: Stage2Output):
        self.current_output = output
        self.content_box.clear_widgets()

        # ── 1. RESUME ANALYSIS CARD (`resume_analysis.json`) ──
        ra = output.resume_analysis
        if ra:
            analysis_card = GlassCard(
                bg_color=(0.10, 0.12, 0.19, 1),
                border_color=(0.25, 0.35, 0.55, 1),
                radius=12,
                orientation='vertical',
                padding=16,
                spacing=12,
                size_hint_y=None
            )

            an_title = Label(
                text="[b]Candidate Resume Analysis & Skill Gap Matrix[/b]",
                markup=True,
                font_size='16sp',
                color=(0.55, 0.85, 1.0, 1),
                size_hint_y=None,
                height=28,
                halign='left'
            )
            an_title.bind(size=an_title.setter('text_size'))
            analysis_card.add_widget(an_title)

            # Matched Skills
            m_lines = [f"  • [b]{sm.skill}:[/b] {sm.resume_evidence} [color=34D399]({sm.proficiency_tier})[/color]" for sm in ra.matched_skills]
            m_str = "\n".join(m_lines) if m_lines else "None identified"
            m_lbl = self._create_auto_label(
                f"[b][color=34D399][+ Matched Technical Skills]:[/color][/b]\n{m_str}",
                font_size='13sp',
                color=(0.95, 0.96, 1.0, 1),
                markup=True
            )
            analysis_card.add_widget(m_lbl)

            # Missing / Skill Gaps
            g_lines = [f"  • [b]{sg.missing_skill}:[/b] {sg.probing_strategy} [color=FBBF24]({sg.jd_importance})[/color]" for sg in ra.missing_or_gap_skills]
            g_str = "\n".join(g_lines) if g_lines else "None identified"
            g_lbl = self._create_auto_label(
                f"[b][color=FBBF24][- Missing / Skill Gaps & Probing Strategy]:[/color][/b]\n{g_str}",
                font_size='13sp',
                color=(0.95, 0.96, 1.0, 1),
                markup=True
            )
            analysis_card.add_widget(g_lbl)

            # Red Flags & Key Projects
            rf_str = "\n".join([f"  • {rf}" for rf in ra.resume_red_flags]) if ra.resume_red_flags else "None detected"
            kp_str = "  •  ".join(ra.key_projects_to_probe) if ra.key_projects_to_probe else "General Candidate Profile"

            extra_lbl = self._create_auto_label(
                f"[b][color=FF6B6B][! Resume Warning Flags]:[/color][/b]\n{rf_str}\n\n"
                f"[b][color=C084FC][* Top Resume Projects to Probe]:[/color][/b]  [color=E0F8FF]{kp_str}[/color]",
                font_size='13sp',
                color=(0.95, 0.96, 1.0, 1),
                markup=True
            )
            analysis_card.add_widget(extra_lbl)

            Clock.schedule_once(lambda dt, card=analysis_card, m=m_lbl, g=g_lbl, e=extra_lbl: setattr(card, 'height', 75 + m.height + g.height + e.height))
            self.content_box.add_widget(analysis_card)

        # ── 2. SYSTEM PROMPT CARD (`interviewer_behavior.json`) ──
        ib = output.interviewer_behavior
        prompt_card = GlassCard(
            bg_color=(0.10, 0.13, 0.22, 1),
            border_color=(0.30, 0.38, 0.60, 1),
            radius=12,
            orientation='vertical',
            padding=16,
            spacing=10,
            size_hint_y=None
        )

        card_head = BoxLayout(orientation='horizontal', size_hint_y=None, height=28)
        prompt_title = Label(
            text=f"[b]Interviewer System Prompt (Persona: {ib.persona})[/b]",
            markup=True,
            font_size='16sp',
            color=(0.6, 0.85, 1.0, 1),
            size_hint_x=0.75,
            halign='left',
            valign='middle'
        )
        prompt_title.bind(size=prompt_title.setter('text_size'))

        badge_latency = Label(
            text="[color=34D399][1-2 Sentences Max][/color]",
            markup=True,
            font_size='12sp',
            size_hint_x=0.25,
            halign='right',
            valign='middle'
        )
        badge_latency.bind(size=badge_latency.setter('text_size'))

        card_head.add_widget(prompt_title)
        card_head.add_widget(badge_latency)
        prompt_card.add_widget(card_head)

        prompt_text_label = self._create_auto_label(f'"{ib.interviewer_system_prompt}"', font_size='13sp', color=(0.95, 0.96, 1.0, 1))
        prompt_card.add_widget(prompt_text_label)

        Clock.schedule_once(lambda dt, card=prompt_card, p_t=prompt_text_label: setattr(card, 'height', 65 + p_t.height))
        self.content_box.add_widget(prompt_card)

        # ── 3. QUESTION TREE HEADER ──
        q_section_head = Label(
            text=f"[b]15-Question Branching Tree ({len(output.interview_questions)} Items)[/b]",
            markup=True,
            font_size='17sp',
            color=(1.0, 0.85, 0.45, 1),
            size_hint_y=None,
            height=32,
            halign='left'
        )
        q_section_head.bind(size=q_section_head.setter('text_size'))
        self.content_box.add_widget(q_section_head)

        difficulty_badges = {
            "Junior": "[color=34D399][Junior][/color]",
            "Mid": "[color=FBBF24][Mid][/color]",
            "Senior": "[color=FF6B6B][Senior][/color]",
            "Lead": "[color=C084FC][Lead][/color]",
            "Staff": "[color=60A5FA][Staff][/color]"
        }

        # ── 4. QUESTION CARDS (`interview_questions.json`) ──
        for q in output.interview_questions:
            q_card = GlassCard(
                bg_color=(0.09, 0.11, 0.17, 1),
                border_color=(0.22, 0.26, 0.40, 1),
                radius=10,
                orientation='vertical',
                padding=16,
                spacing=10,
                size_hint_y=None
            )

            diff_tag = difficulty_badges.get(q.difficulty, q.difficulty)
            header_str = f"[b]Q{q.id}. {q.topic}[/b]   [size=12sp]•   {diff_tag}   •   [color=C084FC]({q.tier})[/color][/size]"

            q_title = Label(text=header_str, markup=True, font_size='14sp', color=(0.85, 0.92, 1.0, 1), size_hint_y=None, height=24, halign='left')
            q_title.bind(size=q_title.setter('text_size'))
            q_card.add_widget(q_title)

            q_text = self._create_auto_label(q.question_text, font_size='14sp', color=(1.0, 1.0, 1.0, 1))
            q_card.add_widget(q_text)

            keywords_str = "  •  ".join(q.expected_keywords) if q.expected_keywords else "General Architecture"
            kw_label = Label(
                text=f"[color=94A3B8]Keywords:[/color]  [color=93C5FD]{keywords_str}[/color]",
                markup=True,
                font_size='12sp',
                size_hint_y=None,
                height=20,
                halign='left'
            )
            kw_label.bind(size=kw_label.setter('text_size'))
            q_card.add_widget(kw_label)

            # Rubric Indicators
            rub = q.rubric
            rub_str = (
                f"[color=FF6B6B][- Poor]:[/color] {', '.join(rub.poor_answer_indicators[:2])}\n"
                f"[color=FBBF24][= Good]:[/color] {', '.join(rub.good_answer_indicators[:2])}\n"
                f"[color=34D399][+ Bar-Raiser]:[/color] {', '.join(rub.bar_raiser_indicators[:2])}"
            )
            rub_lbl = self._create_auto_label(rub_str, font_size='12sp', color=(0.95, 0.96, 1.0, 1), markup=True)
            q_card.add_widget(rub_lbl)

            # Branching Follow-ups
            branch_str = (
                f"[color=38BDF8][Follow-up if Strong]:[/color] {q.followup_if_strong}\n"
                f"[color=FB7185][Follow-up if Weak]:[/color] {q.followup_if_weak}"
            )
            branch_lbl = self._create_auto_label(branch_str, font_size='12sp', color=(0.95, 0.96, 1.0, 1), markup=True)
            q_card.add_widget(branch_lbl)

            Clock.schedule_once(
                lambda dt, card=q_card, q_t=q_text, r_l=rub_lbl, b_l=branch_lbl: setattr(
                    card, 'height', 115 + q_t.height + r_l.height + b_l.height
                )
            )
            self.content_box.add_widget(q_card)


class NetranQuestionApp(App):
    def build(self):
        self.title = "Netran AI — Stage 2: Question Engine & Adaptive Intelligence Client"
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
