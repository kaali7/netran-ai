"""
Netran AI — Stage 1: JD Research & Market Intelligence Engine
Module: front.py
Description: Standalone Kivy Desktop GUI application for Stage 1 JD research, web intelligence visualization,
             saved output history browser, market intelligence, and rubric generation.
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
from kivy.uix.popup import Popup
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
Window.size = (1080, 810)
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

# Domain Source Badges (Clean text formatting without emoji encoding issues)
DOMAIN_COLORS = {
    "linkedin.com": ("[color=0077B5][LinkedIn][/color]", (0.0, 0.47, 0.75, 1)),
    "leetcode.com": ("[color=F59E0B][LeetCode][/color]", (0.96, 0.62, 0.04, 1)),
    "levels.fyi": ("[color=00D26A][Levels.fyi][/color]", (0.0, 0.82, 0.41, 1)),
    "ambitionbox.com": ("[color=FF5A5F][AmbitionBox][/color]", (1.0, 0.35, 0.37, 1)),
    "teamblind.com": ("[color=00C4B4][Blind][/color]", (0.0, 0.77, 0.70, 1)),
    "glassdoor.com": ("[color=10B981][Glassdoor][/color]", (0.06, 0.72, 0.51, 1)),
    "github.com": ("[color=8888AA][GitHub][/color]", (0.53, 0.53, 0.67, 1)),
    "stackoverflow.com": ("[color=F48024][StackOverflow][/color]", (0.95, 0.50, 0.14, 1)),
    "geeksforgeeks.org": ("[color=2F9E44][GeeksforGeeks][/color]", (0.18, 0.62, 0.27, 1)),
    "reddit.com": ("[color=FF4500][Reddit][/color]", (1.0, 0.27, 0.0, 1)),
    "medium.com": ("[color=8B5CF6][Medium][/color]", (0.54, 0.36, 0.96, 1)),
    "dev.to": ("[color=6366F1][Dev.to][/color]", (0.39, 0.40, 0.95, 1)),
    "wellfound.com": ("[color=FF4A00][Wellfound][/color]", (1.0, 0.29, 0.0, 1)),
    "workable.com": ("[color=00A896][Workable][/color]", (0.0, 0.66, 0.59, 1)),
    "bytebytego.com": ("[color=8338EC][ByteByteGo][/color]", (0.51, 0.22, 0.92, 1)),
    "careercup.com": ("[color=3A86FF][CareerCup][/color]", (0.23, 0.52, 1.0, 1)),
    "tryexponent.com": ("[color=FF006E][Exponent][/color]", (1.0, 0.0, 0.43, 1)),
    "educative.io": ("[color=3A86FF][Educative][/color]", (0.23, 0.52, 1.0, 1)),
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
    """Screen 1: Job Description Input, Seniority Selector & Previous Output Browser."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.selected_seniority = "Senior"
        self.force_refresh = False
        main_layout = BoxLayout(orientation='vertical', padding=[24, 20, 24, 20], spacing=12)

        # ── TOP NAV / BRAND HEADER ──
        nav_bar = BoxLayout(orientation='horizontal', size_hint_y=None, height=48, spacing=12)
        
        logo_box = BoxLayout(orientation='horizontal', spacing=8)
        brand_icon = Label(
            text="[*]",
            font_size='18sp',
            bold=True,
            color=COLOR_PRIMARY,
            size_hint_x=None,
            width=32
        )
        brand_title = Label(
            text="[b]Netran AI[/b]  [color=8B5CF6]•[/color]  [size=14sp][color=8888AA]Market & Role Intelligence Engine[/color][/size]",
            markup=True,
            font_size='20sp',
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
            size=(190, 36),
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
            radius=16,
            size_hint=(None, None),
            size=(220, 36),
            padding=[12, 4]
        )
        badge_label = Label(
            text="[b]Gemini 3.6 + 3-Vector Tavily[/b]",
            markup=True,
            font_size='11sp',
            color=(0.7, 0.85, 1, 1)
        )
        badge_card.add_widget(badge_label)

        nav_bar.add_widget(logo_box)
        nav_bar.add_widget(history_btn)
        nav_bar.add_widget(badge_card)
        main_layout.add_widget(nav_bar)

        # ── PRESET TEST INPUTS BAR ──
        preset_bar = BoxLayout(orientation='horizontal', size_hint_y=None, height=38, spacing=8)
        preset_title = Label(
            text="[b]Preset Test Inputs:[/b]",
            markup=True,
            font_size='12sp',
            color=COLOR_TEXT_MUTED,
            size_hint_x=0.20,
            halign='left',
            valign='middle'
        )
        preset_title.bind(size=preset_title.setter('text_size'))
        preset_bar.add_widget(preset_title)

        sample1_btn = Button(
            text="Google Senior Frontend",
            size_hint_x=0.26,
            background_normal='',
            background_color=(0.14, 0.16, 0.26, 1),
            color=(0.8, 0.9, 1, 1),
            font_size='11sp',
            bold=True
        )
        sample1_btn.bind(on_press=lambda inst: self.load_preset("sample_jd_google_frontend.json"))

        sample2_btn = Button(
            text="Backend Systems Engineer",
            size_hint_x=0.27,
            background_normal='',
            background_color=(0.14, 0.16, 0.26, 1),
            color=(0.8, 0.9, 1, 1),
            font_size='11sp',
            bold=True
        )
        sample2_btn.bind(on_press=lambda inst: self.load_preset("sample_jd_backend_engineer.json"))

        sample3_btn = Button(
            text="Full Stack AI Engineer",
            size_hint_x=0.27,
            background_normal='',
            background_color=(0.14, 0.16, 0.26, 1),
            color=(0.8, 0.9, 1, 1),
            font_size='11sp',
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
            text="[b]Job Description Text (Paste or Select Preset)[/b]",
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
            hint_text="Paste raw Job Description (JD) text here or click a preset test input above...\nExtracts salary bands (USD/INR), recruiter green/red flags, soft skill matrices, and 3-vector web search intel.",
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

        # ── SENIORITY & REFRESH OPTIONS BAR ──
        options_bar = BoxLayout(orientation='horizontal', size_hint_y=None, height=36, spacing=8)
        
        sen_label = Label(
            text="[b]Target Seniority:[/b]",
            markup=True,
            font_size='12sp',
            color=COLOR_TEXT_MUTED,
            size_hint_x=0.20,
            halign='left',
            valign='middle'
        )
        sen_label.bind(size=sen_label.setter('text_size'))
        options_bar.add_widget(sen_label)

        self.sen_btns = {}
        for sen_level in ["Junior", "Mid", "Senior", "Lead", "Staff"]:
            btn = Button(
                text=sen_level,
                size_hint_x=0.16,
                background_normal='',
                background_color=(0.39, 0.40, 0.95, 1) if sen_level == "Senior" else (0.12, 0.14, 0.22, 1),
                color=COLOR_TEXT_PRIMARY if sen_level == "Senior" else COLOR_TEXT_MUTED,
                font_size='11sp',
                bold=True
            )
            btn.bind(on_press=lambda inst, lvl=sen_level: self.select_seniority(lvl))
            self.sen_btns[sen_level] = btn
            options_bar.add_widget(btn)

        main_layout.add_widget(options_bar)

        # ── BUTTON ACTION BAR ──
        btn_bar = BoxLayout(orientation='horizontal', size_hint_y=None, height=44, spacing=12)

        save_preset_btn = Button(
            text="[Save] Save Pasted JD",
            size_hint_x=0.30,
            background_normal='',
            background_color=(0.16, 0.18, 0.28, 1),
            color=(0.8, 0.9, 1, 1),
            font_size='12sp'
        )
        save_preset_btn.bind(on_press=self.save_pasted_jd)

        self.analyze_btn = PrimaryButton(
            text="Analyze JD & Build Market Intelligence Rubric",
            size_hint_x=0.70
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
            height=34,
            padding=[12, 6]
        )
        self.status_label = Label(
            text="[Idle] Select preset or paste custom JD to extract market intelligence",
            font_size='12sp',
            color=COLOR_TEXT_MUTED,
            halign='left',
            valign='middle'
        )
        self.status_label.bind(size=self.status_label.setter('text_size'))
        status_card.add_widget(self.status_label)
        main_layout.add_widget(status_card)

        self.add_widget(main_layout)

    def select_seniority(self, level: str):
        self.selected_seniority = level
        for lvl, btn in self.sen_btns.items():
            if lvl == level:
                btn.background_color = COLOR_PRIMARY
                btn.color = COLOR_TEXT_PRIMARY
            else:
                btn.background_color = (0.12, 0.14, 0.22, 1)
                btn.color = COLOR_TEXT_MUTED

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
            self.status_label.text = f"[Loaded] Loaded preset: '{filepath.name}'"
            self.status_label.color = COLOR_SUCCESS
        else:
            self.status_label.text = f"[Error] Preset file '{filename}' not found."
            self.status_label.color = COLOR_WARNING

    def save_pasted_jd(self, instance):
        text = self.jd_input.text.strip()
        if not text:
            self.status_label.text = "[Error] Cannot save empty text."
            self.status_label.color = COLOR_WARNING
            return
        
        TEST_INPUT_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"custom_jd_{timestamp}.json"
        save_path = TEST_INPUT_DIR / filename
        
        payload = {
            "company": "Target Company",
            "role": "Custom Role",
            "target_seniority": self.selected_seniority,
            "jd_text": text
        }
        
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        
        self.status_label.text = f"[Saved] Saved custom JD JSON to test/input/{filename}"
        self.status_label.color = COLOR_SUCCESS

    def open_history_modal(self, instance):
        """Opens popup modal to view and load previously saved session outputs."""
        TEST_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        files = sorted(list(TEST_OUTPUT_DIR.glob("sess_*.json")), key=lambda f: f.name, reverse=True)

        content = BoxLayout(orientation='vertical', padding=12, spacing=10)
        
        title_lbl = Label(
            text="[b]Select Saved Output Session File (test/output/):[/b]",
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

        if files:
            for fpath in files:
                btn = Button(
                    text=f"[Output] {fpath.name}",
                    size_hint_y=None,
                    height=38,
                    background_normal='',
                    background_color=(0.14, 0.17, 0.28, 1),
                    color=(0.85, 0.92, 1, 1),
                    font_size='12sp'
                )
                btn.bind(on_press=lambda inst, p=fpath: self._load_saved_output(p, popup))
                file_grid.add_widget(btn)
        else:
            no_files_lbl = Label(
                text="No saved session outputs found in test/output/.",
                font_size='12sp',
                color=COLOR_TEXT_MUTED
            )
            file_grid.add_widget(no_files_lbl)

        scroll.add_widget(file_grid)
        content.add_widget(scroll)

        close_btn = Button(
            text="Close",
            size_hint_y=None,
            height=36,
            background_normal='',
            background_color=(0.25, 0.28, 0.38, 1)
        )
        close_btn.bind(on_press=popup.dismiss)
        content.add_widget(close_btn)

        popup.open()

    def _load_saved_output(self, filepath: Path, popup: Popup):
        popup.dismiss()
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            output = Stage1Output.model_validate_json(content)
            self.status_label.text = f"[Loaded] Loaded saved output history: '{filepath.name}'"
            self.status_label.color = COLOR_SUCCESS
            app = App.get_running_app()
            app.show_results(output)
        except Exception as e:
            self.status_label.text = f"[Error] Failed to load output file '{filepath.name}': {e}"
            self.status_label.color = COLOR_DANGER

    def start_analysis(self, instance):
        jd_text = self.jd_input.text.strip()
        if not jd_text:
            self.status_label.text = "[Error] Please select a preset or paste a Job Description first."
            self.status_label.color = COLOR_WARNING
            return

        self.analyze_btn.disabled = True
        self.status_label.color = (0.7, 0.8, 1, 1)
        self.status_label.text = "[Processing] Running Gemini reasoning & 3-vector parallel Tavily search..."

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_file = str(TEST_OUTPUT_DIR / f"sess_{timestamp}.json")

        threading.Thread(
            target=self._run_async,
            args=(jd_text, session_file, self.force_refresh),
            daemon=True
        ).start()

    def _run_async(self, jd_text, session_file, force_refresh):
        def update_status(msg):
            Clock.schedule_once(lambda dt: setattr(self.status_label, 'text', f"[Processing] {msg}"))

        try:
            output: Stage1Output = run_pipeline(
                jd_text,
                status_callback=update_status,
                output_dir=session_file,
                force_refresh=force_refresh
            )
            Clock.schedule_once(lambda dt: self._on_success(output))
        except Exception as e:
            err_msg = str(e)
            Clock.schedule_once(lambda dt: self._on_error(err_msg))

    def _on_success(self, output: Stage1Output):
        self.analyze_btn.disabled = False
        self.status_label.text = "[Success] Analysis complete! Displaying Market & Role Intelligence Dashboard..."
        self.status_label.color = COLOR_SUCCESS
        app = App.get_running_app()
        app.show_results(output)

    def _on_error(self, err_msg):
        self.analyze_btn.disabled = False
        self.status_label.text = f"[Pipeline Error] {err_msg[:90]}"
        self.status_label.color = COLOR_DANGER


class ResultsScreen(Screen):
    """Screen 2: Market & Role Intelligence Dashboard (Salary, HR Flags, Soft Skills, Rubric)."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_output = None
        main_layout = BoxLayout(orientation='vertical', padding=[24, 20, 24, 20], spacing=12)

        # ── NAVIGATION / HEADER BAR ──
        nav_bar = BoxLayout(orientation='horizontal', size_hint_y=None, height=44, spacing=10)

        back_btn = Button(
            text="<- Analyze Another JD",
            size_hint_x=0.24,
            background_normal='',
            background_color=(0.14, 0.16, 0.24, 1),
            color=COLOR_TEXT_PRIMARY,
            font_size='12sp',
            bold=True
        )
        back_btn.bind(on_press=self.go_back)

        header_title = Label(
            text="[b]Market & Role Intelligence Dashboard[/b]",
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

        copy_summary_btn = Button(
            text="[Summary]",
            size_hint_x=0.16,
            background_normal='',
            background_color=(0.16, 0.20, 0.32, 1),
            color=(0.8, 0.9, 1, 1),
            font_size='11sp',
            bold=True
        )
        copy_summary_btn.bind(on_press=self.copy_summary)

        copy_json_btn = Button(
            text="[Copy JSON]",
            size_hint_x=0.16,
            background_normal='',
            background_color=(0.18, 0.22, 0.35, 1),
            color=(0.8, 0.9, 1, 1),
            font_size='11sp',
            bold=True
        )
        copy_json_btn.bind(on_press=self.copy_json)

        nav_bar.add_widget(back_btn)
        nav_bar.add_widget(header_title)
        nav_bar.add_widget(history_btn)
        nav_bar.add_widget(copy_summary_btn)
        nav_bar.add_widget(copy_json_btn)
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

    def copy_json(self, instance):
        if self.current_output:
            from kivy.core.clipboard import Clipboard
            json_str = json.dumps(self.current_output.model_dump(), indent=2)
            Clipboard.copy(json_str)
            instance.text = "[Copied!]"
            Clock.schedule_once(lambda dt: setattr(instance, 'text', '[Copy JSON]'), 2)

    def copy_summary(self, instance):
        if self.current_output and self.current_output.rubric:
            from kivy.core.clipboard import Clipboard
            rubric = self.current_output.rubric
            parsed = self.current_output.parsed_jd
            
            lines = [
                f"# Market & Role Intelligence: {parsed.role} at {parsed.company}",
                f"**Seniority**: {getattr(parsed, 'target_seniority', 'Senior')}",
                f"**Tech Stack**: {', '.join(parsed.tech_stack)}",
                "",
                "## Overview",
                rubric.roleOverview,
            ]
            if rubric.marketIntelligence:
                mi = rubric.marketIntelligence
                lines.extend([
                    "",
                    "## Market & Compensation",
                    f"- USD Range: {mi.salary_benchmark.usd_range}",
                    f"- INR CTC Range: {mi.salary_benchmark.inr_range}",
                    f"- Demand Level: {mi.market_demand_level}",
                ])
            if rubric.hrRecruiterLens:
                hr = rubric.hrRecruiterLens
                lines.extend([
                    "",
                    "## Recruiter Green Flags",
                    "\n".join([f"- {flag}" for flag in hr.green_flags]),
                    "",
                    "## Recruiter Red Flags",
                    "\n".join([f"- {flag}" for flag in hr.red_flags]),
                ])
            
            Clipboard.copy("\n".join(lines))
            instance.text = "[Copied!]"
            Clock.schedule_once(lambda dt: setattr(instance, 'text', '[Summary]'), 2)

    def _create_auto_label(self, text, font_size='13sp', color=COLOR_TEXT_PRIMARY, markup=False):
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

    def display_results(self, output: Stage1Output):
        self.current_output = output
        self.content_box.clear_widgets()
        
        rubric = output.rubric
        parsed_jd = output.parsed_jd
        search_context = output.search_context

        # ── 1. ROLE PROFILE & EXECUTION TELEMETRY CARD ──
        profile_card = GlassCard(
            bg_color=(0.10, 0.12, 0.20, 1),
            border_color=(0.28, 0.32, 0.52, 1),
            radius=12,
            orientation='vertical',
            padding=14,
            spacing=8,
            size_hint_y=None
        )

        seniority_val = getattr(parsed_jd, 'target_seniority', 'Senior')
        role_str = f"[b]{parsed_jd.role}[/b]   [size=13sp][color=8B5CF6]at[/color] [color=10B981]{parsed_jd.company}[/color][/size]   [size=11sp][color=F59E0B]({seniority_val})[/color][/size]"
        profile_title = Label(
            text=role_str,
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

        time_val = f"{output.execution_time_seconds:.2f}s" if output.execution_time_seconds else "N/A"
        cache_badge = "[*] SQLite Cached (0ms API)" if output.cached else "[>] Live Tavily 3-Vector Search"
        telemetry_str = f"[color=8888AA]Status:[/color] [color=10B981]{cache_badge}[/color]   |   [color=8888AA]Latency:[/color] [color=F59E0B]{time_val}[/color]"
        telemetry_label = Label(
            text=telemetry_str,
            markup=True,
            font_size='11sp',
            size_hint_y=None,
            height=20,
            halign='left'
        )
        telemetry_label.bind(size=telemetry_label.setter('text_size'))
        profile_card.add_widget(telemetry_label)

        profile_card.height = 92
        self.content_box.add_widget(profile_card)

        # ── 2. MARKET & SALARY INTELLIGENCE CARD ──
        if rubric.marketIntelligence:
            mi = rubric.marketIntelligence
            sb = mi.salary_benchmark

            market_card = GlassCard(
                bg_color=(0.09, 0.13, 0.22, 1),
                border_color=(0.20, 0.40, 0.65, 1),
                radius=12,
                orientation='vertical',
                padding=16,
                spacing=10,
                size_hint_y=None
            )

            mkt_title = Label(
                text=f"[b]Market & Salary Intelligence (2026 Benchmarks)[/b]   [size=11sp][color=10B981]• Demand: {mi.market_demand_level}[/color][/size]",
                markup=True,
                font_size='15sp',
                color=(0.4, 0.85, 1, 1),
                size_hint_y=None,
                height=26,
                halign='left'
            )
            mkt_title.bind(size=mkt_title.setter('text_size'))
            market_card.add_widget(mkt_title)

            # Salary Bands Row
            salary_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=44, spacing=12)

            usd_card = GlassCard(
                bg_color=(0.06, 0.16, 0.14, 1),
                border_color=(0.10, 0.60, 0.40, 1),
                radius=8,
                padding=[12, 6]
            )
            usd_lbl = Label(
                text=f"[color=10B981][USD Base Range]:[/color] {sb.usd_range}",
                markup=True,
                font_size='12sp',
                color=(0.85, 1.0, 0.9, 1),
                halign='left',
                valign='middle'
            )
            usd_lbl.bind(size=usd_lbl.setter('text_size'))
            usd_card.add_widget(usd_lbl)

            inr_card = GlassCard(
                bg_color=(0.18, 0.12, 0.08, 1),
                border_color=(0.70, 0.40, 0.15, 1),
                radius=8,
                padding=[12, 6]
            )
            inr_lbl = Label(
                text=f"[color=F59E0B][INR CTC Range]:[/color] {sb.inr_range}",
                markup=True,
                font_size='12sp',
                color=(1.0, 0.9, 0.8, 1),
                halign='left',
                valign='middle'
            )
            inr_lbl.bind(size=inr_lbl.setter('text_size'))
            inr_card.add_widget(inr_lbl)

            salary_box.add_widget(usd_card)
            salary_box.add_widget(inr_card)
            market_card.add_widget(salary_box)

            notes_lbl = self._create_auto_label(
                f"[color=8888AA]Compensation Drivers:[/color] {sb.compensation_notes}\n[color=8888AA]Hiring Landscape:[/color] {mi.hiring_landscape}",
                font_size='12sp',
                color=(0.85, 0.88, 0.95, 1),
                markup=True
            )
            market_card.add_widget(notes_lbl)

            if mi.top_hiring_company_types:
                comp_types = "  •  ".join(mi.top_hiring_company_types)
                comp_lbl = Label(
                    text=f"[color=8888AA]Top Hiring Sectors:[/color]  [color=F59E0B]{comp_types}[/color]",
                    markup=True,
                    font_size='11sp',
                    size_hint_y=None,
                    height=20,
                    halign='left'
                )
                comp_lbl.bind(size=comp_lbl.setter('text_size'))
                market_card.add_widget(comp_lbl)

            Clock.schedule_once(lambda dt: setattr(market_card, 'height', 120 + notes_lbl.height))
            self.content_box.add_widget(market_card)

        # ── 3. HR RECRUITER SCREENING LENS CARD ──
        if rubric.hrRecruiterLens:
            hr = rubric.hrRecruiterLens

            hr_card = GlassCard(
                bg_color=(0.11, 0.10, 0.17, 1),
                border_color=(0.40, 0.25, 0.60, 1),
                radius=12,
                orientation='vertical',
                padding=16,
                spacing=10,
                size_hint_y=None
            )

            hr_title = Label(
                text="[b]HR & Recruiter Screening Signals[/b]",
                markup=True,
                font_size='15sp',
                color=(0.8, 0.65, 1, 1),
                size_hint_y=None,
                height=26,
                halign='left'
            )
            hr_title.bind(size=hr_title.setter('text_size'))
            hr_card.add_widget(hr_title)

            # Green Flags & Red Flags
            flags_box = BoxLayout(orientation='vertical', spacing=8, size_hint_y=None)

            green_str = "\n".join([f"  [+] {flag}" for flag in hr.green_flags])
            green_lbl = self._create_auto_label(
                f"[b][color=10B981][+ Green Flags (Positive Indicators)]:[/color][/b]\n{green_str}",
                font_size='12sp',
                color=(0.85, 0.96, 0.90, 1),
                markup=True
            )
            flags_box.add_widget(green_lbl)

            red_str = "\n".join([f"  [-] {flag}" for flag in hr.red_flags])
            red_lbl = self._create_auto_label(
                f"[b][color=EF4444][- Red Flags (Warning Indicators)]:[/color][/b]\n{red_str}",
                font_size='12sp',
                color=(1.0, 0.88, 0.88, 1),
                markup=True
            )
            flags_box.add_widget(red_lbl)

            def update_hr_height(dt):
                flags_box.height = green_lbl.height + red_lbl.height + 12
                hr_card.height = 50 + flags_box.height

            Clock.schedule_once(update_hr_height)
            hr_card.add_widget(flags_box)
            self.content_box.add_widget(hr_card)

        # ── 4. SKILL REQUIREMENTS & SOFT SKILLS MATRIX CARD ──
        if rubric.skillRequirements:
            sr = rubric.skillRequirements

            skills_card = GlassCard(
                bg_color=(0.09, 0.12, 0.18, 1),
                border_color=(0.22, 0.35, 0.55, 1),
                radius=12,
                orientation='vertical',
                padding=16,
                spacing=10,
                size_hint_y=None
            )

            sk_title = Label(
                text="[b]Skill Requirements & Soft Skills Matrix[/b]",
                markup=True,
                font_size='15sp',
                color=(0.5, 0.8, 1, 1),
                size_hint_y=None,
                height=26,
                halign='left'
            )
            sk_title.bind(size=sk_title.setter('text_size'))
            skills_card.add_widget(sk_title)

            must_haves = "  •  ".join(sr.must_have_hard_skills) if sr.must_have_hard_skills else "N/A"
            nice_haves = "  •  ".join(sr.nice_to_have_hard_skills) if sr.nice_to_have_hard_skills else "N/A"

            hard_skills_lbl = self._create_auto_label(
                f"[b][color=10B981]Must-Have Technical:[/color][/b]  [color=E0F8FF]{must_haves}[/color]\n"
                f"[b][color=F59E0B]Nice-to-Have Technical:[/color][/b]  [color=D0D5EE]{nice_haves}[/color]",
                font_size='12sp',
                markup=True
            )
            skills_card.add_widget(hard_skills_lbl)

            if sr.critical_soft_skills:
                soft_lines = []
                for ss in sr.critical_soft_skills:
                    soft_lines.append(f"  * [b]{ss.skill}:[/b] {ss.why_it_matters}\n     [color=8888AA]Evaluation:[/color] {ss.evaluation_method}")
                soft_str = "\n\n".join(soft_lines)
                soft_lbl = self._create_auto_label(
                    f"[b][color=8B5CF6]Critical Soft Skills Matrix:[/color][/b]\n{soft_str}",
                    font_size='12sp',
                    markup=True
                )
                skills_card.add_widget(soft_lbl)
                Clock.schedule_once(lambda dt: setattr(skills_card, 'height', 50 + hard_skills_lbl.height + soft_lbl.height))
            else:
                Clock.schedule_once(lambda dt: setattr(skills_card, 'height', 50 + hard_skills_lbl.height))

            self.content_box.add_widget(skills_card)

        # ── 5. ROLE OVERVIEW CARD ──
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
            text="[b]Role Overview & Target Candidate Profile[/b]",
            markup=True,
            font_size='15sp',
            color=(0.6, 0.82, 1, 1),
            size_hint_y=None,
            height=24,
            halign='left'
        )
        overview_title.bind(size=overview_title.setter('text_size'))
        overview_card.add_widget(overview_title)

        overview_text = self._create_auto_label(rubric.roleOverview, font_size='13sp', color=(0.90, 0.92, 0.98, 1))
        overview_card.add_widget(overview_text)

        Clock.schedule_once(lambda dt: setattr(overview_card, 'height', 50 + overview_text.height))
        self.content_box.add_widget(overview_card)

        # ── 6. KEY TECHNICAL PILLARS CARD ──
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
            text="[b]Core Technical Assessment Pillars[/b]",
            markup=True,
            font_size='15sp',
            color=(0.6, 0.82, 1, 1),
            size_hint_y=None,
            height=24,
            halign='left'
        )
        pillars_title.bind(size=pillars_title.setter('text_size'))
        pillars_card.add_widget(pillars_title)

        pillars_str = "\n".join([f"  •  {pillar}" for pillar in rubric.keyTechnicalPillars])
        pillars_text = self._create_auto_label(pillars_str, font_size='13sp', color=(0.75, 0.92, 0.82, 1))
        pillars_card.add_widget(pillars_text)

        Clock.schedule_once(lambda dt: setattr(pillars_card, 'height', 50 + pillars_text.height))
        self.content_box.add_widget(pillars_card)

        # ── 7. INTERVIEW TOPICS & MARKET-SOURCED QUESTIONS ──
        section_label = Label(
            text="[b]Categorized Topics & Market-Sourced Questions[/b]",
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
            "Junior": "[color=10B981][Junior Level][/color]",
            "Mid": "[color=F59E0B][Mid Level][/color]",
            "Senior": "[color=EF4444][Senior Level][/color]",
            "Lead": "[color=8B5CF6][Lead Level][/color]",
            "Staff": "[color=3B82F6][Staff Level][/color]"
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
            q_label = self._create_auto_label(q_text_str, font_size='13sp', color=(0.88, 0.89, 0.95, 1), markup=True)
            topic_card.add_widget(q_label)

            Clock.schedule_once(lambda dt, card=topic_card, lbl=q_label: setattr(card, 'height', 48 + lbl.height))
            self.content_box.add_widget(topic_card)

        # ── 8. LIVE WEB INTELLIGENCE SOURCES CARD ──
        intel_section_label = Label(
            text="[b]Retrieved Live Market Web Intelligence Sources[/b]",
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
                vector_name = item.get("vector", "")

                badge_text = "[Web Source]"
                for domain_key, (tag, _color) in DOMAIN_COLORS.items():
                    if domain_key in url.lower():
                        badge_text = tag
                        break

                if vector_name:
                    badge_text = f"{badge_text} [size=10sp][color=8888AA]({vector_name})[/color][/size]"

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
                    size_hint_x=0.68,
                    halign='left',
                    valign='middle'
                )
                source_title.bind(size=source_title.setter('text_size'))

                domain_badge = Label(
                    text=badge_text,
                    markup=True,
                    font_size='11sp',
                    size_hint_x=0.32,
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
                snippet_label = self._create_auto_label(f'"{clean_snippet}..."', font_size='12sp', color=COLOR_TEXT_MUTED)
                source_card.add_widget(snippet_label)

                Clock.schedule_once(lambda dt, card=source_card, lbl=snippet_label: setattr(card, 'height', 56 + lbl.height))
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
            msg = "[*] SQLite Cached / Gemini Baseline mode — Web search skipped for cached JD text." if output.cached else "[i] Operating in fallback mode using LLM domain baseline knowledge."
            no_intel_label = Label(
                text=msg,
                font_size='12sp',
                color=COLOR_TEXT_MUTED,
                halign='left'
            )
            no_intel_card.add_widget(no_intel_label)
            self.content_box.add_widget(no_intel_card)


class NetranResearchApp(App):
    def build(self):
        self.title = "Netran AI — Stage 1: Market & Role Intelligence Dashboard"
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
