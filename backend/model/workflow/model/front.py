"""
Netran AI — Workflow Orchestrator
Module: front.py
Description: Main 5-screen Kivy Desktop Application (`SetupScreen` -> `ResearchScreen`
             -> `QuestionScreen` -> `InterviewScreen` -> `ReportScreen`) integrating all 4 interview stages.
"""

import os
import sys
import threading
import json
import shutil
from datetime import datetime

try:
    from . import config
    from .sample_data import get_sample_resume_text, get_sample_jd_text, SAMPLE_RESUME_PATH, SAMPLE_JD_PATH
    from .orchestrator import run_full_pipeline
except ImportError:
    try:
        from model.workflow.model import config
        from model.workflow.model.sample_data import get_sample_resume_text, get_sample_jd_text, SAMPLE_RESUME_PATH, SAMPLE_JD_PATH
        from model.workflow.model.orchestrator import run_full_pipeline
    except ImportError:
        import config
        from sample_data import get_sample_resume_text, get_sample_jd_text, SAMPLE_RESUME_PATH, SAMPLE_JD_PATH
        from orchestrator import run_full_pipeline

from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.progressbar import ProgressBar
from kivy.uix.spinner import Spinner
from kivy.graphics import Color, RoundedRectangle, Rectangle

# Styling & Layout KV Definition
KV = """
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
            height: '60dp'
            orientation: 'vertical'
            Label:
                text: "NETRAN AI — UNIFIED INTERVIEW WORKFLOW"
                font_size: '22sp'
                bold: True
                color: 0.30, 0.60, 0.80, 1
            Label:
                text: "End-to-End Multimodal AI Technical Interview Platform"
                font_size: '13sp'
                color: 0.60, 0.65, 0.70, 1

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
                            rgba: 0.12, 0.12, 0.16, 1
                        RoundedRectangle:
                            pos: self.pos
                            size: self.size
                            radius: [8]
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
                            size_hint_x: 0.25
                            background_color: 0.20, 0.40, 0.60, 1
                        Spinner:
                            id: limit_spinner
                            text: 'Fast Testing (5 Questions)'
                            values: ('Fast Testing (5 Questions)', 'Real-Time Live (15 Questions)', 'Extended Live (10 Questions)')
                            size_hint_x: 0.45
                            background_color: 0.25, 0.35, 0.55, 1

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
                        Button:
                            text: "📁 Choose JD File (PDF/DOCX/TXT)"
                            background_color: 0.22, 0.35, 0.50, 1
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
                        Button:
                            text: "📁 Choose Resume File"
                            background_color: 0.22, 0.35, 0.50, 1
                            on_press: root.open_file_picker('resume')
                        Label:
                            id: resume_file_label
                            text: "No file selected"
                            color: 0.60, 0.65, 0.70, 1
                            text_size: self.size
                            valign: 'middle'

        # Bottom Action Bar
        BoxLayout:
            size_hint_y: None
            height: '50dp'
            spacing: 15
            Button:
                text: "🎯 Use Demo Data"
                background_color: 0.25, 0.45, 0.35, 1
                on_press: root.fill_demo_data()
            Button:
                text: "▶ Start Full Interview Workflow"
                background_color: 0.20, 0.60, 0.40, 1
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
                    rgba: 0.12, 0.12, 0.16, 1
                RoundedRectangle:
                    pos: self.pos
                    size: self.size
                    radius: [8]
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
        spacing: 15
        canvas.before:
            Color:
                rgba: 0.08, 0.08, 0.10, 1
            Rectangle:
                pos: self.pos
                size: self.size

        Label:
            text: "Stage 2: Question Tree & System Prompt Generation"
            font_size: '20sp'
            bold: True
            color: 0.30, 0.60, 0.80, 1
            size_hint_y: None
            height: '36dp'

        ProgressBar:
            id: progress_bar
            max: 100
            value: 45
            size_hint_y: None
            height: '16dp'

        Label:
            id: status_label
            text: "Cross-matching Resume and JD skills to construct 15-question tree..."
            font_size: '14sp'
            color: 0.80, 0.85, 0.90, 1
            size_hint_y: None
            height: '24dp'

        ScrollView:
            BoxLayout:
                id: questions_container
                orientation: 'vertical'
                size_hint_y: None
                height: self.minimum_height
                spacing: 10
                padding: 10

<InterviewScreen>:
    name: 'interview'
    BoxLayout:
        orientation: 'vertical'
        padding: 20
        spacing: 15
        canvas.before:
            Color:
                rgba: 0.08, 0.08, 0.10, 1
            Rectangle:
                pos: self.pos
                size: self.size

        # Top Bar
        BoxLayout:
            size_hint_y: None
            height: '40dp'
            Label:
                text: "Stage 3: Live Voice-to-Voice Interview"
                font_size: '18sp'
                bold: True
                color: 0.30, 0.60, 0.80, 1
            Label:
                id: turn_counter_label
                text: "Turn 1 / 15"
                font_size: '16sp'
                bold: True
                color: 0.90, 0.70, 0.20, 1
                size_hint_x: 0.3

        # State Indicator Box
        BoxLayout:
            size_hint_y: None
            height: '40dp'
            canvas.before:
                Color:
                    rgba: 0.16, 0.22, 0.30, 1
                RoundedRectangle:
                    pos: self.pos
                    size: self.size
                    radius: [6]
            Label:
                id: state_label
                text: "STATUS: INITIALIZING VOICE ENGINE"
                font_size: '14sp'
                bold: True
                color: 0.40, 0.80, 1, 1

        # Current Question Display Card
        BoxLayout:
            orientation: 'vertical'
            size_hint_y: 0.35
            padding: 15
            spacing: 8
            canvas.before:
                Color:
                    rgba: 0.14, 0.15, 0.20, 1
                RoundedRectangle:
                    pos: self.pos
                    size: self.size
                    radius: [8]
            Label:
                id: question_topic_label
                text: "TOPIC: Technical Assessment"
                font_size: '13sp'
                bold: True
                color: 0.30, 0.60, 0.80, 1
                size_hint_y: None
                height: '20dp'
            Label:
                id: current_question_label
                text: "Preparing question..."
                font_size: '16sp'
                bold: True
                color: 1, 1, 1, 1
                text_size: self.width, None

        # Candidate Response Transcript View
        ScrollView:
            size_hint_y: 0.45
            canvas.before:
                Color:
                    rgba: 0.10, 0.10, 0.14, 1
                RoundedRectangle:
                    pos: self.pos
                    size: self.size
                    radius: [8]
            padding: 12
            Label:
                id: transcript_log
                text: "Candidate voice transcript will appear here live...\\n"
                font_size: '14sp'
                color: 0.80, 0.90, 0.80, 1
                size_hint_y: None
                height: self.texture_size[1]
                text_size: self.width, None

        # Bottom Controls
        BoxLayout:
            size_hint_y: None
            height: '45dp'
            Button:
                text: "⏹ End Interview & Generate Report"
                background_color: 0.70, 0.25, 0.25, 1
                bold: True
                on_press: root.stop_interview()

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
                    rgba: 0.14, 0.16, 0.22, 1
                RoundedRectangle:
                    pos: self.pos
                    size: self.size
                    radius: [8]
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

        # Action Buttons
        BoxLayout:
            size_hint_y: None
            height: '50dp'
            spacing: 15
            Button:
                text: "💾 Export Report Artifacts"
                background_color: 0.20, 0.50, 0.70, 1
                on_press: root.export_report()
            Button:
                text: "🔄 Start New Interview"
                background_color: 0.20, 0.60, 0.40, 1
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
        limit_text = self.ids.limit_spinner.text
        max_q = 5 if "5" in limit_text else (10 if "10" in limit_text else 15)
        
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


class QuestionScreen(Screen):
    def populate_questions(self, questions_data: list):
        container = self.ids.questions_container
        container.clear_widgets()
        
        for q in questions_data:
            q_id = q.get("id", 1)
            topic = q.get("topic", "General")
            difficulty = q.get("difficulty", "Mid")
            text = q.get("question_text", "")
            
            box = BoxLayout(orientation='vertical', size_hint_y=None, height='80dp', padding=10, spacing=4)
            with box.canvas.before:
                Color(0.14, 0.15, 0.20, 1)
                RoundedRectangle(pos=box.pos, size=box.size, radius=[6])
            
            hdr = Label(
                text=f"Q{q_id}. [{topic}] ({difficulty})",
                font_size='13sp', bold=True, color=(0.3, 0.6, 0.8, 1),
                size_hint_y=None, height='20dp'
            )
            body = Label(
                text=text, font_size='14sp', color=(1, 1, 1, 1),
                size_hint_y=None, height='40dp', text_size=(container.width - 40, None)
            )
            box.add_widget(hdr)
            box.add_widget(body)
            container.add_widget(box)


class InterviewScreen(Screen):
    def update_turn(self, turn_idx: int, state_str: str, question: str, candidate_txt: str):
        self.ids.turn_counter_label.text = f"Turn {turn_idx} / 15"
        self.ids.state_label.text = f"STATUS: {state_str}"
        if question:
            self.ids.current_question_label.text = question
        if candidate_txt:
            self.ids.transcript_log.text += f"Candidate: \"{candidate_txt}\"\n\n"

    def stop_interview(self):
        app = App.get_running_app()
        if app.voice_engine_instances:
            for engine in app.voice_engine_instances:
                engine.stop()


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

        # Executive summary block
        summary_box = BoxLayout(orientation='vertical', size_hint_y=None, height='120dp', padding=10, spacing=5)
        with summary_box.canvas.before:
            Color(0.14, 0.15, 0.20, 1)
            RoundedRectangle(pos=summary_box.pos, size=summary_box.size, radius=[6])
            
        summary_title = Label(text="Executive Summary", font_size='15sp', bold=True, color=(0.3, 0.6, 0.8, 1), size_hint_y=None, height='24dp')
        summary_text = Label(text=summary, font_size='13sp', color=(0.9, 0.9, 0.9, 1), size_hint_y=None, height='80dp', text_size=(container.width - 40, None))
        summary_box.add_widget(summary_title)
        summary_box.add_widget(summary_text)
        container.add_widget(summary_box)

        # Pillars
        for pillar in pillars:
            p_name = pillar.get("pillar_name", "Pillar")
            p_score = pillar.get("score", 80)
            p_summary = pillar.get("summary", "")

            p_box = BoxLayout(orientation='vertical', size_hint_y=None, height='90dp', padding=10, spacing=4)
            with p_box.canvas.before:
                Color(0.12, 0.14, 0.18, 1)
                RoundedRectangle(pos=p_box.pos, size=p_box.size, radius=[6])

            p_title = Label(text=f"🔹 {p_name} ({p_score}/100)", font_size='14sp', bold=True, color=(0.2, 0.8, 0.4, 1), size_hint_y=None, height='20dp')
            p_desc = Label(text=p_summary, font_size='12sp', color=(0.8, 0.8, 0.8, 1), size_hint_y=None, height='55dp', text_size=(container.width - 40, None))
            p_box.add_widget(p_title)
            p_box.add_widget(p_desc)
            container.add_widget(p_box)

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

    def build(self):
        self.title = "Netran AI — Unified Technical Interview Platform"
        sm = ScreenManager(transition=FadeTransition())
        sm.add_widget(SetupScreen(name='setup'))
        sm.add_widget(ResearchScreen(name='research'))
        sm.add_widget(QuestionScreen(name='question'))
        sm.add_widget(InterviewScreen(name='interview'))
        sm.add_widget(ReportScreen(name='report'))
        return sm

    def run_workflow_pipeline(self):
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

            try:
                results = run_full_pipeline(
                    jd_text=jd_text,
                    resume_path=resume_path,
                    target_seniority=seniority,
                    max_questions=max_q,
                    status_callback=status_cb,
                    voice_callback=voice_cb,
                    voice_engine_ref=self.voice_engine_instances
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
                question_scr.populate_questions(payload["questions"])
                
        elif "Stage 3" in stage:
            if self.root.current != 'interview':
                self.root.current = 'interview'
                
        elif "Stage 4" in stage:
            if "report" in payload:
                if self.root.current != 'report':
                    self.root.current = 'report'
                report_scr.render_report(payload["report"])

    def _on_voice_update(self, turn_id: int, state_label: str, question: str, candidate_txt: str):
        if self.root:
            if self.root.current != 'interview':
                self.root.current = 'interview'
            interview_scr = self.root.get_screen('interview')
            interview_scr.update_turn(turn_idx=turn_id, state_str=state_label, question=question, candidate_txt=candidate_txt)


if __name__ == '__main__':
    NetranWorkflowApp().run()
