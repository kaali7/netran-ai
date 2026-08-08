"""
Netran AI — Workflow Orchestrator
Module: front.py
Description: Main 5-screen Kivy Desktop Application (`SetupScreen` -> `ResearchScreen`
             -> `QuestionScreen` -> `InterviewScreen` -> `ReportScreen`) integrating all 4 interview stages.
"""

import json
import os
import shutil
import threading

try:
    from . import config
    from .orchestrator import run_full_pipeline
    from .sample_data import (
        SAMPLE_JD_PATH,
        SAMPLE_RESUME_PATH,
        get_sample_jd_text,
        get_sample_resume_text,
    )
except ImportError:
    try:
        from model.workflow.model import config
        from model.workflow.model.orchestrator import run_full_pipeline
        from model.workflow.model.sample_data import (
            SAMPLE_JD_PATH,
            SAMPLE_RESUME_PATH,
            get_sample_jd_text,
            get_sample_resume_text,
        )
    except ImportError:
        from orchestrator import run_full_pipeline
        from sample_data import (
            SAMPLE_JD_PATH,
            SAMPLE_RESUME_PATH,
            get_sample_jd_text,
        )

from kivy.app import App
from kivy.clock import Clock
from kivy.graphics import Color, RoundedRectangle
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import FadeTransition, Screen, ScreenManager
from kivy.uix.scrollview import ScrollView

# Styling & Layout KV Definition
KV = """
<PrimaryButton@Button>:
    background_color: 0, 0, 0, 0
    background_normal: ''
    canvas.before:
        Color:
            rgba: (0.2, 0.5, 0.7, 1) if self.state == 'normal' else (0.15, 0.4, 0.6, 1)
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [8]

<SuccessButton@Button>:
    background_color: 0, 0, 0, 0
    background_normal: ''
    canvas.before:
        Color:
            rgba: (0.2, 0.6, 0.4, 1) if self.state == 'normal' else (0.15, 0.5, 0.3, 1)
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [8]

<DangerButton@Button>:
    background_color: 0, 0, 0, 0
    background_normal: ''
    canvas.before:
        Color:
            rgba: (0.7, 0.25, 0.25, 1) if self.state == 'normal' else (0.55, 0.2, 0.2, 1)
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [8]

<SecondaryButton@Button>:
    background_color: 0, 0, 0, 0
    background_normal: ''
    canvas.before:
        Color:
            rgba: (0.22, 0.35, 0.50, 1) if self.state == 'normal' else (0.18, 0.28, 0.40, 1)
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [8]

<DemoButton@Button>:
    background_color: 0, 0, 0, 0
    background_normal: ''
    canvas.before:
        Color:
            rgba: (0.25, 0.45, 0.35, 1) if self.state == 'normal' else (0.2, 0.35, 0.28, 1)
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [8]

<ActionBtn@Button>:
    background_color: 0, 0, 0, 0
    background_normal: ''
    canvas.before:
        Color:
            rgba: (0.50, 0.30, 0.80, 1) if self.state == 'normal' else (0.40, 0.20, 0.70, 1)
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [8]

<TabButton@Button>:
    is_active: False
    background_color: 0, 0, 0, 0
    background_normal: ''
    canvas.before:
        Color:
            rgba: (0.2, 0.5, 0.7, 1) if self.is_active else (0.22, 0.35, 0.50, 1)
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [8]

<SetupScreen>:
    name: 'setup'
    BoxLayout:
        orientation: 'vertical'
        padding: 30
        spacing: 20
        canvas.before:
            Color:
                rgba: 0.08, 0.08, 0.10, 1
            Rectangle:
                pos: self.pos
                size: self.size

        # Header Title
        BoxLayout:
            size_hint_y: None
            height: '50dp'
            spacing: 15
            DemoButton:
                size_hint_x: None
                width: '160dp'
                text: "🎯 Use Demo Data"
                on_press: root.fill_demo_data()
            BoxLayout:
                orientation: 'vertical'
                Label:
                    text: "NETRAN AI — UNIFIED INTERVIEW WORKFLOW"
                    font_size: '20sp'
                    bold: True
                    color: 0.30, 0.60, 0.80, 1
                    text_size: self.size
                    valign: 'middle'
                Label:
                    text: "End-to-End Multimodal AI Technical Interview Platform"
                    font_size: '12sp'
                    color: 0.60, 0.65, 0.70, 1
                    text_size: self.size
                    valign: 'middle'

        ScrollView:
            BoxLayout:
                orientation: 'vertical'
                size_hint_y: None
                height: self.minimum_height
                spacing: 15
                padding: [0, 10, 0, 10]

                # Section 1: Candidate Meta
                BoxLayout:
                    orientation: 'vertical'
                    size_hint_y: None
                    height: '90dp'
                    spacing: 8
                    canvas.before:
                        Color:
                            rgba: 0.15, 0.18, 0.25, 0.8
                        RoundedRectangle:
                            pos: self.pos
                            size: self.size
                            radius: [10]
                    padding: 12
                    Label:
                        text: "1. Candidate Information"
                        font_size: '15sp'
                        bold: True
                        color: 0.30, 0.60, 0.80, 1
                        size_hint_y: None
                        height: '24dp'
                    BoxLayout:
                        spacing: 15
                        TextInput:
                            id: candidate_name
                            hint_text: "Candidate Full Name (e.g. Arjun Sharma)"
                            multiline: False
                            background_color: 0.18, 0.18, 0.22, 1
                            foreground_color: 1, 1, 1, 1
                        Spinner:
                            id: seniority_spinner
                            text: 'Mid'
                            values: ('Junior', 'Mid', 'Senior')
                            size_hint_x: 0.35
                            background_color: 0.20, 0.40, 0.60, 1

                # Section 2: Job Description Input (Upload OR Paste)
                BoxLayout:
                    orientation: 'vertical'
                    size_hint_y: None
                    height: '240dp'
                    spacing: 8
                    padding: 12
                    canvas.before:
                        Color:
                            rgba: 0.12, 0.12, 0.16, 1
                        RoundedRectangle:
                            pos: self.pos
                            size: self.size
                            radius: [8]
                    Label:
                        text: "2. Job Description (Upload File OR Paste Text)"
                        font_size: '15sp'
                        bold: True
                        color: 0.30, 0.60, 0.80, 1
                        size_hint_y: None
                        height: '24dp'
                    BoxLayout:
                        size_hint_y: None
                        height: '36dp'
                        spacing: 10
                        SecondaryButton:
                            text: "📁 Choose JD File (PDF/DOCX/TXT)"
                            on_press: root.open_file_picker('jd')
                        Label:
                            id: jd_file_label
                            text: "No file selected"
                            color: 0.60, 0.65, 0.70, 1
                            text_size: self.size
                            valign: 'middle'
                    Label:
                        text: "— OR Paste JD Text Below —"
                        font_size: '12sp'
                        color: 0.50, 0.55, 0.60, 1
                        size_hint_y: None
                        height: '18dp'
                    TextInput:
                        id: jd_text_input
                        hint_text: "Paste raw Job Description text here..."
                        background_color: 0.18, 0.18, 0.22, 1
                        foreground_color: 1, 1, 1, 1
                        on_text: root.on_jd_text_changed(self.text)

                # Section 3: Candidate Resume (File Picker)
                BoxLayout:
                    orientation: 'vertical'
                    size_hint_y: None
                    height: '90dp'
                    spacing: 8
                    padding: 12
                    canvas.before:
                        Color:
                            rgba: 0.12, 0.12, 0.16, 1
                        RoundedRectangle:
                            pos: self.pos
                            size: self.size
                            radius: [8]
                    Label:
                        text: "3. Candidate Resume File (PDF / DOCX / TXT)"
                        font_size: '15sp'
                        bold: True
                        color: 0.30, 0.60, 0.80, 1
                        size_hint_y: None
                        height: '24dp'
                    BoxLayout:
                        size_hint_y: None
                        height: '36dp'
                        spacing: 10
                        SecondaryButton:
                            text: "📁 Choose Resume File"
                            on_press: root.open_file_picker('resume')
                        Label:
                            id: resume_file_label
                            text: "No file selected"
                            color: 0.60, 0.65, 0.70, 1
                            text_size: self.size
                            valign: 'middle'

        BoxLayout:
            size_hint_y: None
            height: '50dp'
            SuccessButton:
                text: "▶ Start Full Interview Workflow"
                bold: True
                on_press: root.start_workflow()

<ResearchScreen>:
    name: 'research'
    BoxLayout:
        orientation: 'vertical'
        padding: 25
        spacing: 15
        canvas.before:
            Color:
                rgba: 0.08, 0.08, 0.10, 1
            Rectangle:
                pos: self.pos
                size: self.size

        Label:
            text: "Stage 1: Market Intelligence & JD Research"
            font_size: '20sp'
            bold: True
            color: 0.30, 0.60, 0.80, 1
            size_hint_y: None
            height: '36dp'

        ProgressBar:
            id: progress_bar
            max: 100
            value: 15
            size_hint_y: None
            height: '16dp'

        Label:
            id: status_label
            text: "Analyzing Job Description with Gemini & searching market intelligence..."
            font_size: '14sp'
            color: 0.80, 0.85, 0.90, 1
            size_hint_y: None
            height: '24dp'

        ScrollView:
            canvas.before:
                Color:
                    rgba: 0.15, 0.18, 0.25, 0.8
                RoundedRectangle:
                    pos: self.pos
                    size: self.size
                    radius: [10]
            padding: 15
            Label:
                id: log_output
                text: "Initializing Stage 1 Research Pipeline...\\n"
                font_name: 'Roboto'
                font_size: '13sp'
                color: 0.70, 0.80, 0.70, 1
                size_hint_y: None
                height: self.texture_size[1]
                text_size: self.width, None

<QuestionScreen>:
    name: 'question'
    BoxLayout:
        orientation: 'vertical'
        padding: 25
        spacing: 12
        canvas.before:
            Color:
                rgba: 0.08, 0.08, 0.10, 1
            Rectangle:
                pos: self.pos
                size: self.size

        Label:
            text: "Stage 2: Candidate Evaluation & Question Tree"
            font_size: '20sp'
            bold: True
            color: 0.30, 0.60, 0.80, 1
            size_hint_y: None
            height: '36dp'

        ProgressBar:
            id: progress_bar
            max: 100
            value: 50
            size_hint_y: None
            height: '14dp'

        Label:
            id: status_label
            text: "Switch tabs below to inspect Detailed Resume Analysis or Question Tree."
            font_size: '13sp'
            color: 0.80, 0.85, 0.90, 1
            size_hint_y: None
            height: '22dp'

        # Tab Toggle Bar
        BoxLayout:
            size_hint_y: None
            height: '42dp'
            spacing: 10
            TabButton:
                id: tab_resume_btn
                text: "📄 Resume Analysis"
                bold: True
                is_active: True
                on_press: root.show_tab('resume')
            TabButton:
                id: tab_question_btn
                text: "❓ Question Tree (15 Questions)"
                bold: True
                is_active: False
                on_press: root.show_tab('question')

        # Swappable Tab Content Area
        BoxLayout:
            id: tab_content_area
            orientation: 'vertical'

        # Action Buttons at Bottom
        BoxLayout:
            size_hint_y: None
            height: '50dp'
            spacing: 15
            DangerButton:
                text: "❌ Cancel & Return to Setup"
                on_press: root.cancel_interview()
            SuccessButton:
                id: start_interview_btn
                text: "▶ Start Live Interview"
                bold: True
                on_press: root.confirm_start_interview()

<InterviewScreen>:
    name: 'interview'
    orientation: 'vertical'
    padding: 16
    spacing: 12
    canvas.before:
        Color:
            rgba: 0.07, 0.07, 0.08, 1
        Rectangle:
            pos: self.pos
            size: self.size

    BoxLayout:
        orientation: 'vertical'
        spacing: 12
        size_hint_y: 1.0

        # TOP BAR
        BoxLayout:
            orientation: 'horizontal'
            size_hint_y: None
            height: '42dp'
            spacing: 12
            padding: [0, 0]

            Label:
                text: "Stage 3: Live Voice-to-Voice Interview"
                font_size: '18sp'
                bold: True
                color: 0.30, 0.60, 0.80, 1
                halign: 'left'
                valign: 'middle'

            Label:
                id: turn_counter_label
                text: "Turn 1 / 15"
                font_size: '14sp'
                bold: True
                color: 0.90, 0.70, 0.20, 1
                size_hint_x: 0.3
                halign: 'right'
                valign: 'middle'

        # STATUS BADGE (Mic: Standby)
        BoxLayout:
            orientation: 'vertical'
            size_hint_y: None
            height: '52dp'
            canvas.before:
                Color:
                    rgba: 0.12, 0.12, 0.14, 1
                RoundedRectangle:
                    pos: self.pos
                    size: self.size
                    radius: [10]
            padding: 8

            Label:
                id: state_label
                text: "Mic: Standby"
                font_size: '12sp'
                color: 0.6, 0.6, 0.65, 1
                size_hint_y: 0.5
            
            ProgressBar:
                id: volume_bar
                max: 1.0
                value: 0.0
                size_hint_y: 0.5

        # SCROLLABLE LIVE TRANSCRIPT DISPLAY
        ScrollView:
            size_hint_y: 1.0
            canvas.before:
                Color:
                    rgba: 0.12, 0.12, 0.14, 1
                RoundedRectangle:
                    pos: self.pos
                    size: self.size
                    radius: [12]

            Label:
                id: transcript_log
                text: "--- Netran AI Live Voice Panel ---\\n\\n[color=00ffcc][System]:[/color] Voice pipeline connected.\\n\\n"
                markup: True
                font_size: '14sp'
                color: 0.9, 0.9, 0.9, 1
                size_hint_y: None
                height: max(self.texture_size[1], self.parent.height)
                text_size: self.width - 32, None
                halign: 'left'
                valign: 'top'
                padding: [16, 16]

        # CONTROL BUTTONS BAR
        BoxLayout:
            orientation: 'horizontal'
            spacing: 12
            size_hint_y: None
            height: '46dp'

            Button:
                id: restart_btn
                text: "🔄 Restart Interview"
                font_size: '13sp'
                bold: True
                size_hint_x: 0.5
                background_normal: ''
                background_color: 0.15, 0.65, 0.45, 1
                on_press: root.restart_interview()

            Button:
                id: stop_btn
                text: "Final Stop & Output"
                font_size: '13sp'
                bold: True
                size_hint_x: 0.5
                background_normal: ''
                background_color: 0.8, 0.25, 0.3, 1
                on_press: root.stop_interview()

<ReportProcessingScreen>:
    name: 'report_processing'
    orientation: 'vertical'
    padding: 24
    spacing: 16
    canvas.before:
        Color:
            rgba: 0.07, 0.07, 0.08, 1
        Rectangle:
            pos: self.pos
            size: self.size

    BoxLayout:
        orientation: 'horizontal'
        size_hint_y: None
        height: '40dp'
        
        Label:
            text: "Stage 4: Multimodal Report Generation"
            font_size: '18sp'
            bold: True
            color: 0.0, 1.0, 0.8, 1
            halign: 'left'

    BoxLayout:
        orientation: 'vertical'
        padding: 20
        spacing: 12
        size_hint_y: None
        height: '140dp'
        canvas.before:
            Color:
                rgba: 0.12, 0.12, 0.14, 1
            RoundedRectangle:
                pos: self.pos
                size: self.size
                radius: [12]

        Label:
            id: track_status_label
            text: "Initializing Audio Track Evaluation..."
            font_size: '16sp'
            bold: True
            color: 1, 1, 1, 1

        ProgressBar:
            id: track_progress_bar
            max: 100
            value: 0
            size_hint_y: None
            height: '16dp'

        Label:
            id: track_counter_label
            text: "Processing Track 1 of Total Tracks"
            font_size: '13sp'
            color: 0.7, 0.7, 0.7, 1

    BoxLayout:
        orientation: 'vertical'
        padding: 16
        canvas.before:
            Color:
                rgba: 0.10, 0.10, 0.12, 1
            RoundedRectangle:
                pos: self.pos
                size: self.size
                radius: [12]

        ScrollView:
            Label:
                id: processing_log
                text: "--- Report Generation Engine ---\\n\\n[color=00ffcc][System]:[/color] Interview voice recording captured. Beginning multimodal audio track analysis...\\n\\n"
                markup: True
                font_size: '13sp'
                color: 0.85, 0.85, 0.85, 1
                size_hint_y: None
                height: max(self.texture_size[1], self.parent.height)
                text_size: self.width - 32, None
                halign: 'left'
                valign: 'top'

<ReportScreen>:
    name: 'report'
    BoxLayout:
        orientation: 'vertical'
        padding: 25
        spacing: 15
        canvas.before:
            Color:
                rgba: 0.08, 0.08, 0.10, 1
            Rectangle:
                pos: self.pos
                size: self.size

        Label:
            text: "Stage 4: Candidate Evaluation Report"
            font_size: '22sp'
            bold: True
            color: 0.30, 0.60, 0.80, 1
            size_hint_y: None
            height: '40dp'

        # Hiring Signal Card
        BoxLayout:
            size_hint_y: None
            height: '70dp'
            spacing: 15
            padding: 10
            canvas.before:
                Color:
                    rgba: 0.15, 0.20, 0.28, 0.9
                RoundedRectangle:
                    pos: self.pos
                    size: self.size
                    radius: [10]
            Label:
                id: hiring_signal_label
                text: "HIRING SIGNAL: STRONG HIRE"
                font_size: '18sp'
                bold: True
                color: 0.20, 0.80, 0.40, 1
            Label:
                id: technical_score_label
                text: "Technical: 85 / 100"
                font_size: '15sp'
                bold: True
                color: 1, 1, 1, 1
            Label:
                id: vocal_score_label
                text: "Vocal Confidence: 80 / 100"
                font_size: '15sp'
                bold: True
                color: 1, 1, 1, 1

        ScrollView:
            BoxLayout:
                id: report_details_container
                orientation: 'vertical'
                size_hint_y: None
                height: self.minimum_height
                spacing: 15
                padding: 10

        BoxLayout:
            size_hint_y: None
            height: '50dp'
            spacing: 15
            PrimaryButton:
                text: "💾 Export Report Artifacts"
                on_press: root.export_report()
            SuccessButton:
                text: "🔄 Start New Interview"
                on_press: root.restart_workflow()
"""

Builder.load_string(KV)


class SetupScreen(Screen):
    selected_jd_path = ""
    selected_resume_path = ""

    def open_file_picker(self, target_type: str):
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        filechooser = FileChooserListView(path=os.path.expanduser("~"))
        content.add_widget(filechooser)
        
        btn_layout = BoxLayout(size_hint_y=None, height='40dp', spacing=10)
        select_btn = Button(text="Select", background_color=(0.2, 0.6, 0.4, 1))
        cancel_btn = Button(text="Cancel", background_color=(0.6, 0.2, 0.2, 1))
        btn_layout.add_widget(select_btn)
        btn_layout.add_widget(cancel_btn)
        content.add_widget(btn_layout)

        popup = Popup(title=f"Select {target_type.upper()} File", content=content, size_hint=(0.9, 0.9))
        
        def on_select(instance):
            if filechooser.selection:
                path = filechooser.selection[0]
                if target_type == 'jd':
                    self.selected_jd_path = path
                    self.ids.jd_file_label.text = os.path.basename(path)
                    self.ids.jd_text_input.text = "" # Clear text input
                elif target_type == 'resume':
                    self.selected_resume_path = path
                    self.ids.resume_file_label.text = os.path.basename(path)
                popup.dismiss()

        select_btn.bind(on_press=on_select)
        cancel_btn.bind(on_press=popup.dismiss)
        popup.open()

    def on_jd_text_changed(self, text: str):
        if text.strip():
            self.selected_jd_path = ""
            self.ids.jd_file_label.text = "(Using pasted text below)"

    def fill_demo_data(self):
        self.ids.candidate_name.text = "Arjun Sharma"
        self.ids.seniority_spinner.text = "Senior"
        self.selected_resume_path = SAMPLE_RESUME_PATH
        self.ids.resume_file_label.text = os.path.basename(SAMPLE_RESUME_PATH)
        self.selected_jd_path = SAMPLE_JD_PATH
        self.ids.jd_file_label.text = os.path.basename(SAMPLE_JD_PATH)
        self.ids.jd_text_input.text = ""

    def start_workflow(self):
        candidate_name = self.ids.candidate_name.text.strip() or "Candidate"
        seniority = self.ids.seniority_spinner.text
        max_q = 15
        
        jd_text = self.ids.jd_text_input.text.strip()
        if not jd_text and self.selected_jd_path and os.path.exists(self.selected_jd_path):
            with open(self.selected_jd_path, "r", encoding="utf-8", errors="ignore") as f:
                if self.selected_jd_path.endswith(".json"):
                    try:
                        data = json.load(f)
                        jd_text = data.get("jd_text", "")
                    except Exception:
                        f.seek(0)
                        jd_text = f.read()
                else:
                    jd_text = f.read()
                
        if not jd_text:
            jd_text = get_sample_jd_text()
            
        resume_path = self.selected_resume_path
        if not resume_path or not os.path.exists(resume_path):
            resume_path = SAMPLE_RESUME_PATH

        app = App.get_running_app()
        app.workflow_data = {
            "candidate_name": candidate_name,
            "seniority": seniority,
            "max_questions": max_q,
            "jd_text": jd_text,
            "resume_path": resume_path
        }
        
        app.root.current = 'research'
        app.run_workflow_pipeline()


class ResearchScreen(Screen):
    def update_log(self, text: str):
        self.ids.log_output.text += f"{text}\n"

    def set_progress(self, val: int, status_text: str):
        self.ids.progress_bar.value = val
        self.ids.status_label.text = status_text


class AnalysisCard(BoxLayout):
    def __init__(self, bg_color=(0.15, 0.20, 0.28, 0.9), **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint_y = None
        self.padding = 12
        self.spacing = 6
        with self.canvas.before:
            Color(*bg_color)
            self.rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[10])
        self.bind(pos=self._update_rect, size=self._update_rect)

    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size


class QuestionScreen(Screen):
    current_tab = 'resume'
    resume_scroll = None
    questions_scroll = None
    resume_container = None
    questions_container = None

    def on_kv_post(self, base_widget):
        self._init_tab_scrollviews()

    def _init_tab_scrollviews(self):
        if self.resume_scroll is not None:
            return

        self.resume_container = BoxLayout(orientation='vertical', size_hint_y=None, spacing=12, padding=10)
        self.resume_container.bind(minimum_height=self.resume_container.setter('height'))
        self.resume_scroll = ScrollView()
        self.resume_scroll.add_widget(self.resume_container)

        self.questions_container = BoxLayout(orientation='vertical', size_hint_y=None, spacing=12, padding=10)
        self.questions_container.bind(minimum_height=self.questions_container.setter('height'))
        self.questions_scroll = ScrollView()
        self.questions_scroll.add_widget(self.questions_container)

        area = self.ids.tab_content_area
        area.clear_widgets()
        area.add_widget(self.resume_scroll)

    def show_tab(self, tab_name: str):
        self._init_tab_scrollviews()
        self.current_tab = tab_name
        area = self.ids.tab_content_area
        area.clear_widgets()

        if tab_name == 'resume':
            area.add_widget(self.resume_scroll)
            self.ids.tab_resume_btn.is_active = True
            self.ids.tab_question_btn.is_active = False
        else:
            area.add_widget(self.questions_scroll)
            self.ids.tab_question_btn.is_active = True
            self.ids.tab_resume_btn.is_active = False

    def populate_stage2_data(self, questions_data: list, resume_analysis: dict | None = None):
        self._init_tab_scrollviews()
        self.populate_questions(questions_data)
        if resume_analysis:
            self.populate_resume_analysis(resume_analysis)

    def populate_questions(self, questions_data: list):
        self._init_tab_scrollviews()
        container = self.questions_container
        container.clear_widgets()

        for q in questions_data:
            q_id = q.get("id", 1)
            topic = q.get("topic", "General")
            difficulty = q.get("difficulty", "Mid")
            text = q.get("question_text", "")
            
            box = AnalysisCard(bg_color=(0.15, 0.18, 0.25, 0.8), height='90dp', padding=10, spacing=4)
            hdr = Label(
                text=f"Q{q_id}. [{topic}] ({difficulty})",
                font_size='13sp', bold=True, color=(0.3, 0.6, 0.8, 1),
                size_hint_y=None, height='20dp'
            )
            body = Label(
                text=text, font_size='14sp', color=(1, 1, 1, 1),
                size_hint_y=None, height='50dp', text_size=(self.width - 60, None)
            )
            box.add_widget(hdr)
            box.add_widget(body)
            container.add_widget(box)

    def populate_resume_analysis(self, r: dict):
        self._init_tab_scrollviews()
        container = self.resume_container
        container.clear_widgets()

        profile = r.get("candidate_profile", {})
        scoring = r.get("role_fit_scoring", {})
        skills = r.get("extracted_skill_overlap", [])
        projects = r.get("detailed_project_analysis", [])
        gaps_flags = r.get("experience_gaps_and_red_flags", {})

        # 1. CANDIDATE PROFILE & SCORES CARD
        c_name = profile.get("candidate_name", "Candidate")
        c_role = profile.get("target_role", "Target Role")
        c_yoe = profile.get("years_of_experience", 0.0)
        c_status = profile.get("current_company_or_status", "N/A")
        c_summary = profile.get("core_identity_summary", "")

        fit_score = scoring.get("overall_jd_match_score", 85)
        depth_score = scoring.get("technical_depth_score", 85)
        sen_score = scoring.get("experience_seniority_score", 85)
        proj_score = scoring.get("project_relevance_score", 85)

        card1 = AnalysisCard(bg_color=(0.15, 0.20, 0.28, 0.9), height='210dp')
        card1.add_widget(Label(
            text=f"👤 {c_name} — {c_role} ({c_yoe} YOE, {c_status})",
            font_size='16sp', bold=True, color=(0.3, 0.6, 0.8, 1), size_hint_y=None, height='24dp'
        ))
        
        scores_str = f"Overall Fit: {fit_score}% | Tech Depth: {depth_score}% | Seniority: {sen_score}% | Project Fit: {proj_score}%"
        card1.add_widget(Label(
            text=scores_str, font_size='13sp', bold=True, color=(0.9, 0.7, 0.2, 1), size_hint_y=None, height='22dp'
        ))

        card1.add_widget(Label(
            text=f"Core Profile: {c_summary}", font_size='13sp', color=(1, 1, 1, 1),
            size_hint_y=None, height='45dp', text_size=(self.width - 60, None)
        ))

        traits = profile.get("personal_traits_and_hobbies", {})
        if isinstance(traits, dict):
            probe = traits.get("icebreaker_probe_topic", "")
            if probe:
                card1.add_widget(Label(
                    text=f"💡 Icebreaker Probe: {probe}", font_size='12sp', color=(0.5, 0.8, 0.9, 1),
                    size_hint_y=None, height='25dp', text_size=(self.width - 60, None)
                ))

        container.add_widget(card1)

        # 2. IDENTIFIED TECHNICAL GAPS & MISSING SKILLS CARD
        tech_gaps = gaps_flags.get("technical_gaps", []) if isinstance(gaps_flags, dict) else []
        if tech_gaps:
            gap_card = AnalysisCard(bg_color=(0.35, 0.20, 0.12, 0.9), height=f"{50 + len(tech_gaps) * 65}dp")
            gap_card.add_widget(Label(
                text="⚠️ Identified Technical Gaps & Missing Skills",
                font_size='15sp', bold=True, color=(1, 0.6, 0.2, 1), size_hint_y=None, height='24dp'
            ))

            for g in tech_gaps:
                if isinstance(g, dict):
                    m_skill = g.get("missing_skill", "")
                    imp = g.get("jd_importance", "Critical")
                    strategy = g.get("probing_strategy", "")
                    gap_card.add_widget(Label(
                        text=f"• [{imp.upper()}] {m_skill}\n  Probing Strategy: {strategy}",
                        font_size='13sp', color=(1, 0.9, 0.8, 1), size_hint_y=None, height='55dp',
                        text_size=(self.width - 60, None)
                    ))
            container.add_widget(gap_card)

        # 3. RESUME RED FLAGS & CLAIM VERIFICATION CARD
        red_flags = gaps_flags.get("resume_red_flags", []) if isinstance(gaps_flags, dict) else []
        if red_flags:
            flag_card = AnalysisCard(bg_color=(0.35, 0.12, 0.12, 0.9), height=f"{50 + len(red_flags) * 75}dp")
            flag_card.add_widget(Label(
                text="🚨 Resume Red Flags & Claim Verification Probes",
                font_size='15sp', bold=True, color=(1, 0.3, 0.3, 1), size_hint_y=None, height='24dp'
            ))

            for rf in red_flags:
                if isinstance(rf, dict):
                    f_type = rf.get("flag_type", "Warning")
                    desc = rf.get("description", "")
                    probe_q = rf.get("probe_question", "")
                    flag_card.add_widget(Label(
                        text=f"• [{f_type}] {desc}\n  Direct Challenge Probe: \"{probe_q}\"",
                        font_size='13sp', color=(1, 0.8, 0.8, 1), size_hint_y=None, height='65dp',
                        text_size=(self.width - 60, None)
                    ))
            container.add_widget(flag_card)

        # 4. EXTRACTED SKILLS MATRIX CARD
        if skills:
            skills_card = AnalysisCard(bg_color=(0.15, 0.18, 0.25, 0.8), height=f"{50 + min(len(skills), 6) * 45}dp")
            skills_card.add_widget(Label(
                text="✅ Matched Technical Skills & Evidence",
                font_size='15sp', bold=True, color=(0.3, 0.6, 0.8, 1), size_hint_y=None, height='24dp'
            ))

            for s in skills[:6]:
                if isinstance(s, dict):
                    sk_name = s.get("skill", "")
                    tier = s.get("proficiency_tier", "")
                    req = s.get("jd_requirement_level", "")
                    ev = s.get("resume_evidence", "")
                    skills_card.add_widget(Label(
                        text=f"• {sk_name} [{tier} | {req}]: {ev}",
                        font_size='12sp', color=(0.85, 0.9, 0.95, 1), size_hint_y=None, height='38dp',
                        text_size=(self.width - 60, None)
                    ))
            container.add_widget(skills_card)

        # 5. DETAILED PROJECTS ANALYSIS CARD
        if projects:
            proj_card = AnalysisCard(bg_color=(0.15, 0.18, 0.25, 0.8), height=f"{50 + len(projects) * 85}dp")
            proj_card.add_widget(Label(
                text="🏗️ Detailed Project Relevance & Scale",
                font_size='15sp', bold=True, color=(0.3, 0.6, 0.8, 1), size_hint_y=None, height='24dp'
            ))

            for p in projects:
                if isinstance(p, dict):
                    p_name = p.get("project_name", "")
                    rel = p.get("relevance_score", 8)
                    arch = p.get("architecture_type", "")
                    scale = p.get("quantifiable_scale", "")
                    probes = ", ".join(p.get("suggested_interview_probes", []))
                    proj_card.add_widget(Label(
                        text=f"• {p_name} (Relevance: {rel}/10, {arch}, Scale: {scale})\n  Suggested Probes: {probes}",
                        font_size='12sp', color=(0.85, 0.9, 0.95, 1), size_hint_y=None, height='75dp',
                        text_size=(self.width - 60, None)
                    ))
            container.add_widget(proj_card)

    def confirm_start_interview(self):
        app = App.get_running_app()
        app.confirm_interview_start(should_start=True)

    def cancel_interview(self):
        app = App.get_running_app()
        app.confirm_interview_start(should_start=False)


class ReportCard(BoxLayout):
    def __init__(self, title: str, score: int | None, summary: str, is_summary: bool = False, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint_y = None
        self.padding = [15, 12]
        self.spacing = 6
        
        with self.canvas.before:
            Color(0.15, 0.20, 0.28, 0.9) if is_summary else Color(0.15, 0.18, 0.25, 0.8)
            self.rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[10])
        self.bind(pos=self._update_rect, size=self._update_rect)

        hdr_text = f"🔹 {title}" if not is_summary else title
        if score is not None:
            hdr_text += f" ({score}/100)"
            
        title_lbl = Label(
            text=hdr_text,
            font_size='15sp' if is_summary else '14sp',
            bold=True,
            color=(0.3, 0.6, 0.9, 1) if is_summary else (0.2, 0.8, 0.4, 1),
            size_hint_y=None,
            height='24dp',
            halign='left',
            valign='middle'
        )
        title_lbl.bind(size=title_lbl.setter('text_size'))
        
        desc_lbl = Label(
            text=summary,
            font_size='13sp',
            color=(0.85, 0.85, 0.90, 1),
            size_hint_y=None,
            halign='left',
            valign='top'
        )
        desc_lbl.bind(width=lambda instance, val: setattr(instance, 'text_size', (val, None)))
        desc_lbl.bind(texture_size=lambda instance, val: setattr(instance, 'height', val[1]))
        
        self.add_widget(title_lbl)
        self.add_widget(desc_lbl)
        self.bind(children=self._update_height)

    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size

    def _update_height(self, *args):
        total_h = self.padding[1] + self.padding[3]
        for child in self.children:
            total_h += child.height + self.spacing
        self.height = total_h


class InterviewScreen(Screen):
    def update_turn(self, turn_idx: int, state_str: str, question: str, candidate_txt: str, max_turns: int = 15):
        self.ids.turn_counter_label.text = f"Turn {turn_idx} / {max_turns}"
        
        # Dynamic Status Banner
        upper_state = state_str.upper()
        if "SPEAKING" in upper_state:
            self.ids.state_label.text = "Mic: Eva is Speaking"
            if "volume_bar" in self.ids:
                self.ids.volume_bar.value = 0.5
        elif "LISTENING" in upper_state:
            self.ids.state_label.text = "Mic: Listening (Speak Now)"
            if "volume_bar" in self.ids:
                self.ids.volume_bar.value = 1.0
        elif "PROCESSING" in upper_state:
            self.ids.state_label.text = "Mic: Processing & Transcribing..."
            if "volume_bar" in self.ids:
                self.ids.volume_bar.value = 0.0
        else:
            self.ids.state_label.text = f"Mic: {state_str}"
            if "volume_bar" in self.ids:
                self.ids.volume_bar.value = 0.0

        # We append to transcript_log only once per update chunk
        if upper_state == "SPEAKING_QUESTION" and question:
            self.ids.transcript_log.text += f"[color=3399ff][b]Eva:[/b][/color] {question}\n"
        elif "EVA_RESPONDING" in upper_state:
            branch_info = ""
            if "|" in upper_state:
                branch = upper_state.split("|")[1]
                branch_info = f"\n[color=ff8800]📊 [Branch]:[/color] {branch}"
                
            if candidate_txt:
                parts = candidate_txt.split("\n\n[Eva]: ")
                cand_msg = parts[0]
                eva_ack = parts[1] if len(parts) > 1 else ""
                
                # Filter out the LLM's TONE: prefix if it exists in the output
                if "SPEAK:" in eva_ack:
                    tone_part = eva_ack.split("SPEAK:")[0].strip()
                    eva_ack = eva_ack.split("SPEAK:")[1].strip()
                    if tone_part.startswith("TONE:"):
                        tone = tone_part.replace("TONE:", "").strip()
                        branch_info += f"  |  [color=00ccff]🎭 [Tone]:[/color] {tone}"
                        
                self.ids.transcript_log.text += f"[color=20c997]You:[/color] {cand_msg}{branch_info}\n"
                if eva_ack:
                    self.ids.transcript_log.text += f"[color=3399ff][b]Eva:[/b][/color] {eva_ack}\n"

        # Auto-scroll transcript view to bottom
        if self.ids.transcript_log.parent and hasattr(self.ids.transcript_log.parent, 'scroll_y'):
            Clock.schedule_once(lambda dt: setattr(self.ids.transcript_log.parent, 'scroll_y', 0))

    def restart_interview(self):
        """Restarts the voice interview loop by resetting the session state and restarting the pipeline."""
        app = App.get_running_app()
        if app.voice_engine_instances:
            for engine in app.voice_engine_instances:
                try:
                    engine.stop()
                except Exception as e:
                    print(f"Error stopping engine: {e}")
            app.voice_engine_instances.clear()
        
        self.ids.transcript_log.text = "--- Netran AI Live Voice Panel ---\\n\\n[color=00ffcc][System]:[/color] Restarting voice pipeline...\\n\\n"
        self.ids.state_label.text = "Mic: Restarting..."
        
        # Re-run pipeline from Stage 3 with cache
        Clock.schedule_once(lambda dt: app.run_workflow_pipeline(), 0.5)

    def stop_interview(self):
        app = App.get_running_app()
        self.ids.state_label.text = "STATUS: GENERATING_FINAL_REPORT"
        if app.voice_engine_instances:
            for engine in app.voice_engine_instances:
                try:
                    engine.stop()
                except Exception as e:
                    print(f"Error stopping engine: {e}")
        if app.root and app.root.has_screen('report_processing'):
            app.root.current = 'report_processing'


class ReportProcessingScreen(Screen):
    def update_track_progress(self, current: int, total: int, msg: str, pct: int):
        self.ids.track_status_label.text = f"Evaluating Audio Track {current} / {total}"
        self.ids.track_counter_label.text = f"Processing Track {current} of {total} total tracks"
        self.ids.track_progress_bar.value = pct
        self.ids.processing_log.text += f"[color=ffc107]⚙️ Track {current}/{total}:[/color] {msg}\n"
        if self.ids.processing_log.parent and hasattr(self.ids.processing_log.parent, 'scroll_y'):
            Clock.schedule_once(lambda dt: setattr(self.ids.processing_log.parent, 'scroll_y', 0))


class ReportScreen(Screen):
    def render_report(self, report_dict: dict):
        signal = report_dict.get("overall_hiring_signal", "HIRE").upper()
        tech_score = report_dict.get("overall_technical_score", 80)
        vocal_score = report_dict.get("overall_vocal_confidence_score", 80)
        summary = report_dict.get("executive_summary", "")
        pillars = report_dict.get("technical_pillars", [])

        self.ids.hiring_signal_label.text = f"HIRING SIGNAL: {signal}"
        self.ids.technical_score_label.text = f"Technical: {tech_score} / 100"
        self.ids.vocal_score_label.text = f"Vocal Confidence: {vocal_score} / 100"

        container = self.ids.report_details_container
        container.clear_widgets()

        # Executive summary card
        summary_card = ReportCard(title="Executive Summary", score=None, summary=summary, is_summary=True)
        container.add_widget(summary_card)

        # Pillars cards
        for pillar in pillars:
            p_name = pillar.get("pillar_name", "Pillar")
            p_score = pillar.get("score", 80)
            p_summary = pillar.get("summary", "")
            p_card = ReportCard(title=p_name, score=p_score, summary=p_summary, is_summary=False)
            container.add_widget(p_card)

    def export_report(self):
        app = App.get_running_app()
        if app.session_dir and os.path.exists(app.session_dir):
            desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
            dest_dir = os.path.join(desktop_path, f"Netran_Report_{os.path.basename(app.session_dir)}")
            try:
                shutil.copytree(app.session_dir, dest_dir)
                print(f"Report exported to {dest_dir}")
            except Exception as e:
                print(f"Export error: {e}")

    def restart_workflow(self):
        app = App.get_running_app()
        app.root.current = 'setup'


class NetranWorkflowApp(App):
    workflow_data = {}
    voice_engine_instances = []
    session_dir = ""
    start_confirm_event = threading.Event()
    should_start_interview = False

    def confirm_interview_start(self, should_start: bool):
        self.should_start_interview = should_start
        self.start_confirm_event.set()
        if not should_start:
            self.root.current = 'setup'

    def build(self):
        self.title = "Netran AI — Unified Technical Interview Platform"
        sm = ScreenManager(transition=FadeTransition())
        sm.add_widget(SetupScreen(name='setup'))
        sm.add_widget(ResearchScreen(name='research'))
        sm.add_widget(QuestionScreen(name='question'))
        sm.add_widget(InterviewScreen(name='interview'))
        sm.add_widget(ReportProcessingScreen(name='report_processing'))
        sm.add_widget(ReportScreen(name='report'))
        return sm

    def run_workflow_pipeline(self):
        self.start_confirm_event.clear()
        self.should_start_interview = False
        self.voice_engine_instances.clear()
        
        def worker():
            jd_text = self.workflow_data.get("jd_text", "")
            resume_path = self.workflow_data.get("resume_path", "")
            seniority = self.workflow_data.get("seniority", "Mid")
            max_q = self.workflow_data.get("max_questions", 15)
            
            def status_cb(stage, msg, pct, payload):
                Clock.schedule_once(lambda dt: self._on_stage_update(stage, msg, pct, payload))

            def voice_cb(turn_id, state_label, question, candidate_txt):
                Clock.schedule_once(lambda dt: self._on_voice_update(turn_id, state_label, question, candidate_txt))

            def confirm_cb():
                self.start_confirm_event.wait()
                return self.should_start_interview

            try:
                results = run_full_pipeline(
                    jd_text=jd_text,
                    resume_path=resume_path,
                    target_seniority=seniority,
                    max_questions=max_q,
                    status_callback=status_cb,
                    voice_callback=voice_cb,
                    voice_engine_ref=self.voice_engine_instances,
                    confirm_start_callback=confirm_cb
                )
                self.session_dir = results.get("session_dir", "")
            except Exception as e:
                print(f"Workflow Pipeline Error: {e}")

        threading.Thread(target=worker, daemon=True).start()

    def _on_stage_update(self, stage: str, msg: str, pct: int, payload: dict):
        research_scr = self.root.get_screen('research')
        question_scr = self.root.get_screen('question')
        interview_scr = self.root.get_screen('interview')
        report_scr = self.root.get_screen('report')

        if "Stage 1" in stage:
            research_scr.set_progress(pct, msg)
            research_scr.update_log(f"[{stage}] {msg}")
            
        elif "Stage 2" in stage:
            if self.root.current != 'question':
                self.root.current = 'question'
            question_scr.ids.progress_bar.value = pct
            question_scr.ids.status_label.text = msg
            if "questions" in payload:
                q_data = payload.get("questions", [])
                r_analysis = payload.get("resume_analysis", None)
                question_scr.populate_stage2_data(q_data, r_analysis)
                
        elif "Stage 3" in stage:
            if self.root.current != 'interview':
                self.root.current = 'interview'
                
        elif "Stage 4" in stage:
            if "report" in payload:
                if self.root.current != 'report':
                    self.root.current = 'report'
                report_scr.render_report(payload["report"])
            else:
                if self.root.current != 'report_processing':
                    self.root.current = 'report_processing'
                report_proc_scr = self.root.get_screen('report_processing')
                track_curr = payload.get("track_current", 1)
                track_tot = payload.get("track_total", 1)
                report_proc_scr.update_track_progress(current=track_curr, total=track_tot, msg=msg, pct=pct)

    def _on_voice_update(self, turn_id: int, state_label: str, question: str, candidate_txt: str):
        if self.root:
            if self.root.current != 'interview':
                self.root.current = 'interview'
            max_q = self.workflow_data.get("max_questions", 5)
            interview_scr = self.root.get_screen('interview')
            interview_scr.update_turn(turn_idx=turn_id, state_str=state_label, question=question, candidate_txt=candidate_txt, max_turns=max_q)


if __name__ == '__main__':
    NetranWorkflowApp().run()
