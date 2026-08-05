"""
Netran AI — Stage 3: Live Voice-to-Voice Loop
Module: front.py
Description: Multi-screen Kivy Desktop GUI application featuring:
             1. InterviewScreen: Live voice interview engine with preset loader and real-time VAD.
             2. SessionHistoryScreen: Dedicated full-page output inspector, telemetry breakdown,
                header Back-to-Interview button, and real-time audio playback engine with progress bar.
"""

import difflib
import json
import os
import threading
import time
import wave
from datetime import datetime, timezone

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.uix.button import Button
from kivy.uix.screenmanager import FadeTransition, Screen, ScreenManager

# Set compact, well-proportioned desktop window dimensions
Window.size = (1120, 700)
Window.minimum_width = 1000
Window.minimum_height = 620

try:
    from .benchmark import Benchmark
    from .brain import TextSanitizer, generate_eva_response
    from .brain import preload as preload_brain
    from .listener import BargeInWatcher, ContinuousMicWriter, listen_and_transcribe
    from .question_manager import QuestionManager
    from .schemas import load_stage2_bundle
    from .session_logger import SessionLogger
    from .session_state import SessionState
    from .speaker import (
        PersistentSpeaker,
        force_stop_all,
        get_default_player,
        init_speaker_compat,
        speak_text,
    )
    from .speaker import preload_models as preload_speaker
except ImportError:
    try:
        from model.voice_to_voice_model.model.benchmark import Benchmark
        from model.voice_to_voice_model.model.brain import (
            TextSanitizer,
            generate_eva_response,
        )
        from model.voice_to_voice_model.model.brain import preload as preload_brain
        from model.voice_to_voice_model.model.listener import (
            BargeInWatcher,
            ContinuousMicWriter,
            listen_and_transcribe,
        )
        from model.voice_to_voice_model.model.question_manager import QuestionManager
        from model.voice_to_voice_model.model.schemas import load_stage2_bundle
        from model.voice_to_voice_model.model.session_logger import SessionLogger
        from model.voice_to_voice_model.model.session_state import SessionState
        from model.voice_to_voice_model.model.speaker import (
            PersistentSpeaker,
            force_stop_all,
            get_default_player,
            init_speaker_compat,
            speak_text,
        )
        from model.voice_to_voice_model.model.speaker import (
            preload_models as preload_speaker,
        )
    except ImportError:
        from benchmark import Benchmark
        from brain import generate_eva_response
        from brain import preload as preload_brain
        from listener import BargeInWatcher, ContinuousMicWriter, listen_and_transcribe
        from question_manager import QuestionManager
        from schemas import load_stage2_bundle
        from session_logger import SessionLogger
        from session_state import SessionState
        from speaker import (
            force_stop_all,
            get_default_player,
            init_speaker_compat,
            speak_text,
        )
        from speaker import preload_models as preload_speaker


# Multi-Screen KV layout definition with responsive proportions
KV = """
<InterviewScreen>:
    name: 'interview_screen'
    orientation: 'vertical'
    padding: 16
    spacing: 12
    canvas.before:
        Color:
            rgba: 0.07, 0.07, 0.08, 1
        Rectangle:
            pos: self.pos
            size: self.size

    # MAIN SPLIT CONTENT AREA
    BoxLayout:
        orientation: 'horizontal'
        spacing: 16
        size_hint_y: 1.0

        # LEFT PANE: CONFIGURATION & STAGE 2 PRESETS
        BoxLayout:
            orientation: 'vertical'
            size_hint_x: 0.36
            spacing: 12
            padding: 16
            canvas.before:
                Color:
                    rgba: 0.12, 0.12, 0.14, 1
                RoundedRectangle:
                    pos: self.pos
                    size: self.size
                    radius: [12]

            Label:
                text: "Session & Input Controls"
                font_size: '16sp'
                bold: True
                size_hint_y: None
                height: '28dp'
                color: 0.2, 0.6, 1, 1

            Label:
                text: "Stage 2 Preset Bundle:"
                font_size: '13sp'
                size_hint_y: None
                height: '18dp'
                halign: 'left'
                color: 0.6, 0.6, 0.65, 1

            Spinner:
                id: preset_selector
                text: 'Preset: sample_backend'
                values: ('Preset: sample_backend', 'Preset: sample_frontend', 'Preset: sample_fullstack')
                size_hint_y: None
                height: '40dp'
                font_size: '13sp'
                background_normal: ''
                background_color: 0.16, 0.16, 0.2, 1
                color: 0.9, 0.9, 0.9, 1
                on_text: root.on_preset_select(self.text)

            Spinner:
                id: limit_selector
                text: '5 Questions (Fast Test)'
                values: ('5 Questions (Fast Test)', '10 Questions (Standard)', '15 Questions (Full Tree)', 'All Available Questions')
                size_hint_y: None
                height: '40dp'
                font_size: '13sp'
                background_normal: ''
                background_color: 0.16, 0.16, 0.2, 1
                on_text: root.on_limit_select(self.text)

            ScrollView:
                size_hint_y: 1.0
                canvas.before:
                    Color:
                        rgba: 0.08, 0.08, 0.1, 1
                    RoundedRectangle:
                        pos: self.pos
                        size: self.size
                        radius: [8]

                Label:
                    id: target_script_label
                    text: "[Loaded Stage 2 Input Bundle details will appear here.]"
                    font_size: '13sp'
                    color: 0.8, 0.8, 0.8, 1
                    text_size: self.width - 24, None
                    size_hint_y: None
                    height: max(self.texture_size[1], self.parent.height)
                    halign: 'left'
                    valign: 'top'
                    padding: [12, 12]
                    markup: True

        # RIGHT PANE: LIVE INTERVIEW PANEL, TOP HISTORY BAR & AUDIO VISUALIZER
        BoxLayout:
            orientation: 'vertical'
            size_hint_x: 0.64
            spacing: 12

            # TOP ACTION BAR IN RIGHT PANE: PROMINENT HISTORY BUTTON & STATUS BADGE
            BoxLayout:
                orientation: 'horizontal'
                size_hint_y: None
                height: '42dp'
                spacing: 12
                padding: [0, 0]

                Button:
                    id: history_btn
                    text: "📜 View Session Output History"
                    font_size: '13sp'
                    bold: True
                    background_normal: ''
                    background_color: 0.2, 0.45, 0.7, 1
                    on_press: root.open_history_screen()

                Label:
                    id: header_status_badge
                    text: "System Ready"
                    font_size: '14sp'
                    bold: True
                    size_hint_x: 0.35
                    halign: 'right'
                    valign: 'middle'
                    color: 0.2, 0.8, 0.5, 1

            Label:
                id: status_label
                text: "System Online"
                font_size: '16sp'
                bold: True
                size_hint_y: None
                height: '24dp'
                color: 0.5, 0.4, 0.9, 1

            Label:
                id: question_label
                text: "Question Progress: 0 / 5"
                font_size: '14sp'
                bold: True
                size_hint_y: None
                height: '24dp'
                color: 0.9, 0.9, 0.9, 1

            # VAD DIAGNOSTICS & VOLUME BAR
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
                    id: vad_state_label
                    text: "Mic: Offline"
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
                    id: transcript_display
                    text: "--- Netran AI Live Voice Panel ---\\n"
                    markup: True
                    font_size: '14sp'
                    color: 0.9, 0.9, 0.9, 1
                    size_hint_y: None
                    height: max(self.texture_size[1], self.parent.height)
                    text_size: self.width - 32, None
                    halign: 'left'
                    valign: 'top'
                    padding: [16, 16]

            # CONTROL BUTTONS BAR (CLEAN 3 BUTTONS ONLY)
            BoxLayout:
                orientation: 'horizontal'
                spacing: 12
                size_hint_y: None
                height: '46dp'

                Button:
                    id: start_btn
                    text: "Start Interview"
                    font_size: '13sp'
                    bold: True
                    size_hint_x: 0.33
                    background_normal: ''
                    background_color: 0.15, 0.65, 0.45, 1
                    on_press: root.start_interview()

                Button:
                    id: stop_btn
                    text: "Final Stop & Output"
                    font_size: '13sp'
                    bold: True
                    size_hint_x: 0.33
                    background_normal: ''
                    background_color: 0.8, 0.25, 0.3, 1
                    disabled: True
                    on_press: root.stop_interview()

                Button:
                    id: restart_btn
                    text: "Restart Session"
                    font_size: '13sp'
                    bold: True
                    size_hint_x: 0.33
                    background_normal: ''
                    background_color: 0.2, 0.5, 0.8, 1
                    on_press: root.restart_interview()


<SessionHistoryScreen>:
    name: 'history_screen'
    orientation: 'vertical'
    padding: 16
    spacing: 12
    canvas.before:
        Color:
            rgba: 0.07, 0.07, 0.08, 1
        Rectangle:
            pos: self.pos
            size: self.size

    # TOP APPLICATION HEADER BAR WITH PROMINENT BACK BUTTON
    BoxLayout:
        orientation: 'horizontal'
        size_hint_y: None
        height: '52dp'
        padding: [12, 6]
        spacing: 12
        canvas.before:
            Color:
                rgba: 0.12, 0.12, 0.14, 1
            RoundedRectangle:
                pos: self.pos
                size: self.size
                radius: [10]

        Button:
            text: "⬅️ Back to Live Interview"
            font_size: '13sp'
            bold: True
            size_hint_x: 0.35
            background_normal: ''
            background_color: 0.2, 0.5, 0.8, 1
            on_press: root.go_back_to_interview()

        Label:
            text: "[b]Netran AI[/b] — Session Output & History Inspector"
            markup: True
            font_size: '16sp'
            halign: 'left'
            valign: 'middle'
            size_hint_x: 0.45
            color: 0.3, 0.75, 1, 1

        Label:
            text: "Stage 3 Output Data"
            font_size: '14sp'
            bold: True
            halign: 'right'
            valign: 'middle'
            size_hint_x: 0.2
            color: 0.2, 0.8, 0.5, 1

    # MAIN SPLIT CONTENT AREA
    BoxLayout:
        orientation: 'horizontal'
        spacing: 16
        size_hint_y: 1.0

        # LEFT PANE: PAST SESSIONS LIST WITH HEADER BACK BUTTON
        BoxLayout:
            orientation: 'vertical'
            size_hint_x: 0.34
            spacing: 12
            padding: 12
            canvas.before:
                Color:
                    rgba: 0.12, 0.12, 0.14, 1
                RoundedRectangle:
                    pos: self.pos
                    size: self.size
                    radius: [12]

            # LEFT PANE HEADER: COMPACT BACK BUTTON & TITLE
            BoxLayout:
                orientation: 'horizontal'
                size_hint_y: None
                height: '36dp'
                spacing: 8

                Button:
                    text: "⬅️ Back"
                    font_size: '12sp'
                    bold: True
                    size_hint_x: 0.38
                    background_normal: ''
                    background_color: 0.3, 0.35, 0.4, 1
                    on_press: root.go_back_to_interview()

                Label:
                    text: "Past Sessions:"
                    font_size: "14sp"
                    bold: True
                    size_hint_x: 0.62
                    halign: "left"
                    valign: "middle"
                    color: 0.9, 0.9, 0.9, 1

            ScrollView:
                size_hint_y: 1.0
                BoxLayout:
                    id: sessions_list_layout
                    orientation: 'vertical'
                    spacing: 8
                    size_hint_y: None
                    padding: [0, 4]

        # RIGHT PANE: SELECTED SESSION DETAIL & AUDIO PLAYER
        BoxLayout:
            orientation: 'vertical'
            size_hint_x: 0.66
            spacing: 12

            # AUDIO PLAYER BAR WITH PROGRESS & TIME TRACKING
            BoxLayout:
                orientation: 'vertical'
                size_hint_y: None
                height: '80dp'
                padding: 10
                spacing: 6
                canvas.before:
                    Color:
                        rgba: 0.12, 0.12, 0.14, 1
                    RoundedRectangle:
                        pos: self.pos
                        size: self.size
                        radius: [10]

                BoxLayout:
                    orientation: 'horizontal'
                    spacing: 12
                    size_hint_y: 0.6

                    Button:
                        id: play_audio_btn
                        text: "Play Audio Recording"
                        font_size: "13sp"
                        bold: True
                        disabled: True
                        size_hint_x: 0.5
                        background_normal: ""
                        background_color: 0.15, 0.65, 0.45, 1
                        on_press: root.play_selected_audio()

                    Button:
                        id: stop_audio_btn
                        text: "Stop Audio"
                        font_size: "13sp"
                        bold: True
                        disabled: True
                        size_hint_x: 0.3
                        background_normal: ""
                        background_color: 0.8, 0.25, 0.3, 1
                        on_press: root.stop_selected_audio()

                    Label:
                        id: audio_time_label
                        text: "0:00 / 0:00"
                        font_size: "13sp"
                        bold: True
                        size_hint_x: 0.2
                        color: 0.4, 0.8, 1, 1

                ProgressBar:
                    id: audio_progress_bar
                    max: 1.0
                    value: 0.0
                    size_hint_y: 0.4

            # DETAIL TRANSCRIPT SCROLLVIEW
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
                    id: detail_label
                    text: "[Select a session folder from the left pane to inspect generated outputs.]"
                    markup: True
                    font_size: "14sp"
                    color: 0.9, 0.9, 0.9, 1
                    text_size: self.width - 40, None
                    size_hint_y: None
                    height: max(self.texture_size[1] + 40, self.parent.height)
                    halign: "left"
                    valign: "top"
                    padding: [20, 20]
"""


class InterviewScreen(Screen):
    """
    Main live interview screen hosting hardware controls, preset bundles,
    live VAD diagnostics, and question pipeline thread.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.is_running = False
        self.interview_thread = None
        self.log_filename = os.path.join(os.path.dirname(__file__), "_interview_log.txt")
        self.conversation_history = []
        self.question_count = 0
        self.MAX_QUESTIONS = 5  # Default to 5 questions during testing time

        # Session artifacts tracking
        self.session_logger = None
        self.mic_writer = None
        self.session_dir = None
        self.current_question_text = ""
        self.last_eva_speech_end_sec = 0.0

        # State variables for Stage 2 Bundle & Execution
        self.llm_enabled = True
        self.stage2_bundle = None
        self.question_manager = None
        self.selected_preset_name = "sample_backend"

        self.session_state = SessionState()
        self.session_state.pause_tolerance_ms = 800   # 0.8s Fast Response
        self.session_state.selected_voice = "af_bella" # Kokoro Female American Voice
        self.session_state.input_mode = "VAD"          # Auto-VAD
        self.tts_player = None
        self.candidate_project_anchor = ""

        self._load_selected_preset(self.selected_preset_name)

    def _load_selected_preset(self, preset_name: str):
        model_root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        preset_dir = os.path.join(model_root_dir, "test", "input", preset_name)
        if os.path.exists(preset_dir):
            try:
                bundle = load_stage2_bundle(preset_dir)
                self.stage2_bundle = bundle
                self.question_manager = QuestionManager(bundle.questions)
                self._update_preset_display()
                print(f"[GUI] Successfully loaded preset bundle: {preset_name}", flush=True)
            except Exception as e:
                print(f"[GUI Error] Failed to load preset {preset_name}: {e}", flush=True)

    def open_history_screen(self):
        if self.manager:
            history_screen = self.manager.get_screen('history_screen')
            history_screen.refresh_history()
            self.manager.current = 'history_screen'

    def on_preset_select(self, text):
        preset_key = text.replace("Preset: ", "").strip()
        self.selected_preset_name = preset_key
        self._load_selected_preset(preset_key)

    def on_limit_select(self, text):
        if "5" in text:
            self.MAX_QUESTIONS = 5
        elif "10" in text:
            self.MAX_QUESTIONS = 10
        elif "15" in text:
            self.MAX_QUESTIONS = 15
        elif "All" in text and self.stage2_bundle:
            self.MAX_QUESTIONS = len(self.stage2_bundle.questions)
        else:
            self.MAX_QUESTIONS = 5
        self.update_question_label(self.question_count)

    def toggle_llm_mode(self, toggle_btn):
        if toggle_btn.state == 'down':
            self.llm_enabled = True
            toggle_btn.text = 'LLM Engine: ACTIVE'
            self.ids.script_selector.disabled = True
            self._update_preset_display()
        else:
            self.llm_enabled = False
            toggle_btn.text = 'SCRIPT CALIBRATION MODE'
            self.ids.script_selector.disabled = False
            self._update_script_display()

        self.update_question_label(self.question_count if self.llm_enabled else self.question_count + 1)

    def on_track_select(self, text):
        if text in self.calibration_scripts:
            self.active_track = text
            self.current_track_data = self.calibration_scripts[text]
            self._update_script_display()

    def _update_preset_display(self):
        if self.llm_enabled and self.stage2_bundle:
            b = self.stage2_bundle
            info = (
                f"[b]LOADED STAGE 2 PRESET:[/b] {self.selected_preset_name}\n"
                f"[b]Persona:[/b] {b.behavior.persona}\n"
                f"[b]Target Role:[/b] {b.behavior.target_role or 'Engineer'}\n"
                f"[b]Total Questions:[/b] {len(b.questions)} items\n\n"
                f"[b]SYSTEM PROMPT EXCERPT:[/b]\n"
                f"[color=00ffcc]{b.system_prompt[:180]}...[/color]"
            )
            if "target_script_label" in self.ids:
                self.ids.target_script_label.text = info
        elif self.llm_enabled:
            if "target_script_label" in self.ids:
                self.ids.target_script_label.text = "[Running in dynamic live mode via Qwen LLM.]"

    def _update_script_display(self):
        if self.llm_enabled:
            self._update_preset_display()
            return

        if not self.active_track or not self.current_track_data:
            if "target_script_label" in self.ids:
                self.ids.target_script_label.text = "[Select a track from the dropdown above to view the script.]"
            return

        idx = self.question_count
        if idx < len(self.current_track_data):
            q_data = self.current_track_data[idx]
            if "target_script_label" in self.ids:
                self.ids.target_script_label.text = (
                    f"[b]TRACK:[/b] {self.active_track}\n"
                    f"[b]QUESTION {idx + 1}:[/b] {q_data['question']}\n\n"
                    f"[b]TARGET ANSWER TO READ ALOUD:[/b]\n"
                    f"[color=00ff00]{q_data['answer']}[/color]"
                )
        else:
            if "target_script_label" in self.ids:
                self.ids.target_script_label.text = "[Calibration track complete! Click Restart or select a new track.]"

    def _reset_buttons(self):
        if "start_btn" in self.ids:
            self.ids.start_btn.disabled = False
        if "stop_btn" in self.ids:
            self.ids.stop_btn.disabled = True
        if "restart_btn" in self.ids:
            self.ids.restart_btn.disabled = False

    def update_question_label(self, count):
        def _update(dt):
            if "question_label" in self.ids:
                clamped_count = min(count, self.MAX_QUESTIONS)
                self.ids.question_label.text = f"Question Progress: {clamped_count} / {self.MAX_QUESTIONS}"
        Clock.schedule_once(_update)

    def start_interview(self):
        if "start_btn" in self.ids:
            self.ids.start_btn.disabled = True
        if "stop_btn" in self.ids:
            self.ids.stop_btn.disabled = False
        self.is_running = True
        self.conversation_history = []
        self.question_count = 0
        self.update_question_label(0)

        if self.stage2_bundle:
            selected_qs = self.stage2_bundle.questions[:self.MAX_QUESTIONS] if self.MAX_QUESTIONS > 0 else self.stage2_bundle.questions
            self.question_manager = QuestionManager(selected_qs)

        session_id = f"sess_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
        model_root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        test_out_dir = os.path.join(model_root_dir, "test", "output")
        self.session_dir = os.path.join(test_out_dir, session_id)
        os.makedirs(self.session_dir, exist_ok=True)

        with open(self.log_filename, "w", encoding="utf-8") as f:
            f.write(
                f"=== AI INTERVIEW LOG: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} ===\n\n"
            )

        cand_name = self.stage2_bundle.behavior.candidate_name if (self.stage2_bundle and self.stage2_bundle.behavior and self.stage2_bundle.behavior.candidate_name) else "Candidate"
        target_role = self.stage2_bundle.behavior.target_role if (self.stage2_bundle and self.stage2_bundle.behavior and self.stage2_bundle.behavior.target_role) else "Software Engineer"
        target_company = self.stage2_bundle.behavior.target_company if (self.stage2_bundle and self.stage2_bundle.behavior and self.stage2_bundle.behavior.target_company) else "Netran AI"

        self.session_logger = SessionLogger(
            session_id=session_id,
            session_dir=self.session_dir,
            candidate_name=cand_name,
            target_role=target_role,
            target_company=target_company
        )
        mic_wav_path = os.path.join(self.session_dir, "recording.wav")
        self.mic_writer = ContinuousMicWriter(filepath=mic_wav_path)
        self.mic_writer.start()

        self.update_status("Initializing AI Models... (Please wait)")
        self.append_ui_text("\n[System]: Voice pipeline connected.\n")

        self.interview_thread = threading.Thread(
            target=self._run_interview_pipeline, daemon=True
        )
        self.interview_thread.start()

    def submit_answer_now(self):
        """Forces immediate speech endpointing when candidate finishes speaking."""
        self.session_state.force_speech_done.set()
        self.update_status("⚡ Processing answer immediately...")

    def stop_interview(self):
        """Finalizes audio recording, writes session_manifest.json, and transitions to history screen."""
        self.is_running = False
        self.session_state.should_stop.set()

        # Immediately halt any in-progress TTS audio playback
        try:
            from model.voice_to_voice_model.model.speaker import force_stop_all
            force_stop_all()
        except Exception:
            pass
        if self.mic_writer:
            self.mic_writer.stop()
            self.mic_writer = None

        if self.session_logger:
            self.session_logger.finalize()
            session_dir = self.session_logger.session_dir
            self.session_logger = None

            def _switch_to_history(dt):
                if self.manager:
                    history_screen = self.manager.get_screen('history_screen')
                    history_screen.refresh_history(auto_select_path=session_dir)
                    self.manager.current = 'history_screen'

            Clock.schedule_once(_switch_to_history, 0.5)

        Clock.schedule_once(lambda dt: self._reset_buttons())
        self.update_status("Session Finalized & Saved.")

    def restart_interview(self):
        self.stop_interview()
        def _clear(dt):
            if "transcript_display" in self.ids:
                self.ids.transcript_display.text = "--- Netran AI Live Voice Panel ---\n\n"
        Clock.schedule_once(_clear)
        Clock.schedule_once(lambda dt: self.start_interview(), 0.5)

    def update_status(self, text):
        def _update(dt):
            if "status_label" in self.ids:
                self.ids.status_label.text = text
            if "header_status_badge" in self.ids:
                self.ids.header_status_badge.text = text
        Clock.schedule_once(_update)

    def append_ui_text(self, text):
        def _update(dt):
            if "transcript_display" in self.ids:
                self.ids.transcript_display.text += f"{text}\n"

        Clock.schedule_once(_update)

    def append_ui_chunk(self, text):
        def _update(dt):
            if "transcript_display" in self.ids:
                self.ids.transcript_display.text += text
        Clock.schedule_once(_update)

    def _llm_ui_callback(self, event_type, content):
        if event_type == "speak_start":
            self.append_ui_chunk("[color=3399ff][b]Eva:[/b][/color] ")
            
        elif event_type == "speak_chunk":
            if not getattr(self, "_speak_started", False):
                content = content.lstrip()
                if content:
                    self._speak_started = True
            
            if content:
                self.append_ui_chunk(content)

    def update_audio_diagnostics(self, data):
        def _update(dt):
            if "vad_state_label" in self.ids:
                self.ids.vad_state_label.text = data.get("state", "")
            if "volume_bar" in self.ids:
                # Show VAD probability (the actual speech detection metric) instead of raw RMS.
                # When speech is happening, VAD prob closely tracks speech energy.
                vad_prob = data.get("vad_prob", 0.0)
                rms = data.get("rms", 0.0)
                # Blend: use VAD prob as primary signal, RMS as secondary for visual continuity
                display_val = max(vad_prob, min(rms * 5, 1.0))
                self.ids.volume_bar.value = min(display_val, 1.0)
        Clock.schedule_once(_update)

    def log_and_display_turn(self, speaker, text, skip_ui=False):
        timestamp = datetime.now(timezone.utc).strftime("%H:%M:%S")
        formatted_log = f"[{timestamp}] {speaker}: {text}"
        
        if speaker == "Eva":
            formatted_ui = f"[color=3399ff][b]{speaker}:[/b][/color] {text}"
        elif speaker == "You":
            formatted_ui = f"[color=20c997]{speaker}:[/color] {text}"
        else:
            formatted_ui = f"[color=ffc107][{speaker}]:[/color] {text}"

        with open(self.log_filename, "a", encoding="utf-8") as f:
            f.write(formatted_log + "\n")

        if not skip_ui:
            self.append_ui_text(formatted_ui)

    def _eva_speak_blocking(self, text: str):
        """
        TRUE FULL-DUPLEX BARGE-IN: Speaks text with concurrent mic monitoring.

        Architecture:
          1. Clears stale interrupt flags.
          2. Starts BargeInWatcher — a background daemon thread that opens its
             OWN sounddevice input stream and runs Silero VAD every 32ms.
          3. Calls player.speak_clause() which synthesizes and queues audio
             (non-blocking for playback — _play_loop plays in its own thread).
          4. Waits for audio_queue.join() in a daemon thread — blocks until
             _play_loop has fully processed (task_done()) every queued chunk.
             Polls every 50ms with interrupt_event / should_stop bail-out.
          5. After join completes, waits an additional 150ms post-drain guard
             to let the OS PyAudio hardware buffer physically finish playing
             before opening the microphone. Without this guard, listen_and_
             transcribe() opens the mic while Eva's voice is still audible
             from the speakers, causing acoustic bleed-back to trigger a
             false barge-in → force_stop_all() → session ends with 0 turns.
          6. Stops the watcher, clears agent-speaking flag, and returns.

        This is the ONLY correct way to support barge-in — the mic must be
        monitored concurrently with playback, not sequentially after it.
        """
        import threading as _th
        import time as _t
        player = get_default_player()
        if not player or not self.is_running:
            return

        # Clear stale interrupt flags from previous turn
        self.session_state.interrupt_event.clear()
        self.session_state.interrupt_event.clear()
        player.interrupt_event.clear()

        # Signal that Eva is speaking (BargeInWatcher uses this + its own stop_event)
        self.session_state.is_agent_speaking.set()

        # Start concurrent mic monitoring BEFORE synthesis begins
        watcher = BargeInWatcher(self.session_state, on_barge_in=force_stop_all)
        watcher.start()

        try:
            # Synthesize text and enqueue audio chunks (non-blocking for playback)
            player.speak_clause(text, self.session_state)

            # --- DRAIN FIX ---
            # audio_queue.empty() is unreliable: it returns True between Kokoro synthesis
            # chunks while _play_loop is still mid-write to PyAudio. This caused the old
            # drain loop to exit prematurely, opening the mic while Eva was still speaking.
            #
            # Solution: audio_queue.join() — blocks until every item's task_done() has been
            # called by _play_loop, guaranteeing all chunks were fully dequeued and written.
            # Run join() in a daemon thread so we can poll with interrupt bail-out.
            _join_done = _th.Event()

            def _wait_for_queue_join():
                try:
                    player.audio_queue.join()
                except Exception:
                    pass
                finally:
                    _join_done.set()

            _join_thread = _th.Thread(target=_wait_for_queue_join, daemon=True)
            _join_thread.start()

            # Poll every 50ms with interrupt and stop bail-out
            while (
                not _join_done.is_set()
                and not self.session_state.interrupt_event.is_set()
                and self.is_running
            ):
                _t.sleep(0.05)

            # Post-drain OS hardware buffer guard: PyAudio OS buffer holds ~21ms at
            # 512 frames_per_buffer. Even after Python queue is empty, the OS driver
            # buffer still needs time to physically play out. 150ms provides safe
            # clearance for the speaker audio to fully finish before the mic opens,
            # preventing acoustic bleed-back from triggering a false barge-in.
            if not self.session_state.interrupt_event.is_set() and self.is_running:
                _t.sleep(0.15)

        finally:
            watcher.stop()
            self.session_state.is_agent_speaking.clear()

        if self.session_logger:
            self.last_eva_speech_end_sec = self.session_logger.elapsed_sec()

    def _run_interview_pipeline(self):
        """Main automated hardware pipeline loop linking components."""

        try:
            preload_speaker()
            if self.llm_enabled:
                preload_brain(custom_system_prompt=self.stage2_bundle.system_prompt if self.stage2_bundle else None)
            
            init_speaker_compat(self.session_state)
            self.session_state.should_stop.clear()
            self.session_state.force_speech_done.clear()

            self.update_status("Eva is initializing speech channels...")
            self.append_ui_text("[color=ffcc00]⚙️ [System]:[/color] Voice pipeline connected.\n")

            # --- TURN 1: INITIATE CONVERSATION ---
            if self.llm_enabled:
                if self.question_manager and self.question_manager.get_current_question():
                    q1 = self.question_manager.get_current_question()
                    initial_greeting = f"Hello! I am Eva, your technical interviewer today. {q1.question_text}"
                    self.current_question_text = q1.question_text
                else:
                    initial_greeting = (
                        "Hello! I am Eva, your technical interviewer today. "
                        "Before we dive into technical questions, could you briefly introduce yourself and tell me what you've been working on recently?"
                    )
                    self.current_question_text = initial_greeting

                self.log_and_display_turn("Eva", initial_greeting)
                turn1_history = f"TONE: warm\nSPEAK: {initial_greeting}"
                self.conversation_history.append({"role": "assistant", "content": turn1_history})
                self.question_count = 0
                self.update_question_label(self.question_count)
                self.update_status("Eva is speaking...")
                # TRUE FULL-DUPLEX: _eva_speak_blocking starts BargeInWatcher concurrently
                self._eva_speak_blocking(initial_greeting)

            else:
                if not self.current_track_data:
                    self.update_status("Error: No track selected")
                    self.append_ui_text("[System]: Please select an interview track before starting calibration.\n")
                    self.stop_interview()
                    return

                q_data = self.current_track_data[0]
                self.current_question_text = q_data['question']
                initial_greeting = f"Welcome to the {self.active_track} calibration. Here is your first question: {q_data['question']}"
                self.log_and_display_turn("Eva", q_data['question'])
                self.question_count = 0
                self.update_question_label(self.question_count + 1)
                Clock.schedule_once(lambda dt: self._update_script_display())
                self.update_status("Eva is speaking...")
                # TRUE FULL-DUPLEX: _eva_speak_blocking starts BargeInWatcher concurrently
                self._eva_speak_blocking(initial_greeting)
                
                turn1_history = f"TONE: warm\nSPEAK: {initial_greeting}"
                self.conversation_history.append({"role": "assistant", "content": turn1_history})

            # --- MAIN CYCLE LOOP ---
            while self.is_running:
                self.update_status("Listening to your response...")
                turn_start_sec = self.session_logger.elapsed_sec() if self.session_logger else 0.0
                user_transcript = listen_and_transcribe(
                    ui_callback=self.update_audio_diagnostics, 
                    mic_writer=self.mic_writer,
                    state=self.session_state
                )
                turn_end_sec = self.session_logger.elapsed_sec() if self.session_logger else 0.0
                silence_gap_sec = max(0.0, turn_start_sec - self.last_eva_speech_end_sec)

                if user_transcript is None or not user_transcript.strip() or not self.is_running:
                    continue

                clean_transcript = user_transcript.strip()

                if self.llm_enabled:
                    branch_taken = "next_topic"
                    prompt_ctx = clean_transcript
                    if self.question_manager:
                        branch_taken = self.question_manager.evaluate_transcript(clean_transcript)
                        
                        if branch_taken == "icebreaker_response":
                            self.candidate_project_anchor = f"CANDIDATE BACKGROUND: {clean_transcript}"

                        llm_prompt, target_question = self.question_manager.format_prompt_context(branch_taken, clean_transcript)
                        prompt_ctx = llm_prompt

                    self.log_and_display_turn("You", clean_transcript)
                    
                    self.conversation_history.append({"role": "user", "content": clean_transcript})

                    self.update_status("Eva is evaluating...")

                    # Clear barge-in flags before this LLM turn
                    self.session_state.interrupt_event.clear()
                    self._speak_started = False
                    self._speak_chunk_buffer = ""
                    
                    _player = get_default_player()
                    if _player:
                        _player.interrupt_event.clear()

                    # TRUE FULL-DUPLEX: Start BargeInWatcher BEFORE LLM streaming begins.
                    self.session_state.is_agent_speaking.set()
                    _barge_watcher = BargeInWatcher(self.session_state, on_barge_in=force_stop_all)
                    _barge_watcher.start()

                    Benchmark.start("ttft")
                    from model.voice_to_voice_model.model.prompts import (
                        get_system_prompt,
                    )
                    sys_prompt_dict = get_system_prompt(self.stage2_bundle.system_prompt if self.stage2_bundle else None)
                    base_sys_prompt = sys_prompt_dict["content"]
                    
                    sys_prompt = f"{base_sys_prompt}\n\n{self.candidate_project_anchor}" if self.candidate_project_anchor else base_sys_prompt

                    MAX_HISTORY_MESSAGES = 8
                    if len(self.conversation_history) > MAX_HISTORY_MESSAGES:
                        trimmed_history = self.conversation_history[:2] + self.conversation_history[-(MAX_HISTORY_MESSAGES-2):]
                    else:
                        trimmed_history = list(self.conversation_history)

                    messages_for_llm = [dict(m) for m in trimmed_history]
                    if messages_for_llm:
                        messages_for_llm[-1]["content"] = prompt_ctx

                    Benchmark.start("ttft")
                    Benchmark.start("ttfa")
                    try:
                        think_text, speak_content = generate_eva_response(
                            messages_for_llm,
                            custom_system_prompt=sys_prompt,
                            speaker_player=get_default_player(),
                            session_state=self.session_state,
                            ui_callback=self._llm_ui_callback
                        )
                    finally:
                        # Always drain audio queue + stop watcher, even on exception
                        _player2 = get_default_player()
                        if _player2:
                            import time as _t
                            import threading as _th
                            
                            _join_done = _th.Event()
                            def _wait_for_queue_join():
                                try:
                                    _player2.audio_queue.join()
                                except Exception:
                                    pass
                                finally:
                                    _join_done.set()
                                    
                            _join_thread = _th.Thread(target=_wait_for_queue_join, daemon=True)
                            _join_thread.start()
                            
                            while (
                                not _join_done.is_set()
                                and not self.session_state.interrupt_event.is_set()
                                and self.is_running
                            ):
                                _t.sleep(0.05)
                                
                            # Post-drain OS hardware buffer guard
                            if not self.session_state.interrupt_event.is_set() and self.is_running:
                                _t.sleep(0.15)
                        _barge_watcher.stop()
                        self.session_state.is_agent_speaking.clear()

                    was_barge_in = self.session_state.interrupt_event.is_set()
                    active_tone = getattr(self.session_state, "current_tone", "direct")
                    active_speed = getattr(self.session_state, "tts_speed", 1.0)
                    
                    current_ttft = getattr(Benchmark, 'last_ttft_ms', 0.0)
                    current_ttfa = getattr(Benchmark, 'last_ttfa_ms', 0.0)

                    full_eva_reply = speak_content
                    # Log to file, but skip UI append since ui_callback handled it
                    self.log_and_display_turn("Eva", speak_content, skip_ui=True)
                    self.append_ui_chunk("\n") # Add final newline for the speak block
                    
                    self.append_ui_text(
                        f"[color=ff8800]📊 [Branch Taken]:[/color] {branch_taken}  |  "
                        f"[color=00ccff]🎭 [Tone]:[/color] {active_tone} ({active_speed:.2f}x)"
                    )
                    if was_barge_in:
                        self.append_ui_text("[color=ff3333]⚡ [Candidate Barged In — Hardware Flush][/color]")

                    if self.session_logger:
                        self.last_eva_speech_end_sec = self.session_logger.elapsed_sec()

                    self.conversation_history.append({"role": "assistant", "content": speak_content})

                    stt_ms = getattr(Benchmark, "last_stt_ms", 0.0)
                    Benchmark.log_metrics(stt_ms, current_ttft, current_ttfa)

                    if self.session_logger:
                        current_q_topic = self.question_manager.get_current_question().topic if (self.question_manager and self.question_manager.get_current_question()) else "Technical Interview"
                        turn_seq = len(self.session_logger.turns) + 1
                        self.session_logger.log_turn(
                            turn_id=turn_seq,
                            topic=current_q_topic,
                            question_text=self.current_question_text,
                            candidate_transcript=clean_transcript,
                            audio_start_sec=turn_start_sec,
                            audio_end_sec=turn_end_sec,
                            silence_duration_before_answer_sec=silence_gap_sec,
                            stt_latency_ms=stt_ms,
                            ttft_ms=current_ttft,
                            tts_ttfa_ms=current_ttfa if 'current_ttfa' in locals() else 0.0,
                            evaluation_branch_taken=branch_taken,
                            eva_reasoning="N/A - CoT Disabled for Low Latency",
                            eva_tone_used=active_tone,
                            eva_reply=speak_content if 'speak_content' in locals() else full_eva_reply,
                            was_barge_in=was_barge_in
                        )

                    self.current_question_text = target_question if 'target_question' in locals() else full_eva_reply

                    if self.question_manager:
                        displayed_q = min(self.question_manager.current_index + 1, self.MAX_QUESTIONS)
                        self.question_count = displayed_q
                        self.update_question_label(self.question_count)

                    if branch_taken == "interview_completed" or (self.question_manager and self.question_manager.is_finished()):
                        self.update_status("Interview Complete — Wrapping Up")
                        if branch_taken != "interview_completed":
                            closing = (
                                "That concludes our technical evaluation for today. "
                                "Thank you for your time, and we will follow up with detailed feedback shortly."
                            )
                            self.log_and_display_turn("Eva", closing)
                            self.conversation_history.append({"role": "assistant", "content": closing})
                            # TRUE FULL-DUPLEX: use _eva_speak_blocking for closing message too
                            self.update_status("Eva is concluding...")
                            self._eva_speak_blocking(closing)
                        total_qs = len(self.question_manager.questions) if self.question_manager else self.MAX_QUESTIONS
                        self.append_ui_text(f"\n[System]: Session complete. All {total_qs} questions covered.")
                        self.stop_interview()
                        break

                else:
                    q_data = self.current_track_data[self.question_count]
                    expected_answer = q_data['answer']

                    spoken_clean = clean_transcript.lower().strip().replace(".", "").replace(",", "")
                    expected_clean = expected_answer.lower().strip().replace(".", "").replace(",", "")
                    accuracy = difflib.SequenceMatcher(None, expected_clean.split(), spoken_clean.split()).ratio() * 100

                    self.log_and_display_turn("You", f"{clean_transcript}")
                    self.log_and_display_turn("System", f"[Accuracy Check] Match Score: {accuracy:.2f}%")

                    self.question_count += 1

                    if self.question_count < len(self.current_track_data):
                        Clock.schedule_once(lambda dt: self._update_script_display())
                        self.update_question_label(self.question_count + 1)

                        next_q_data = self.current_track_data[self.question_count]
                        next_q = next_q_data['question']

                        self.log_and_display_turn("Eva", next_q)
                        self.update_status("Eva is speaking...")
                        speak_text(next_q)
                        if self.session_logger:
                            self.last_eva_speech_end_sec = self.session_logger.elapsed_sec()

                        if self.session_logger:
                            stt_ms = getattr(Benchmark, "last_stt_ms", 0.0)
                            turn_seq = len(self.session_logger.turns) + 1
                            self.session_logger.log_turn(
                                turn_id=turn_seq,
                                topic=self.active_track or "Calibration",
                                question_text=self.current_question_text,
                                candidate_transcript=clean_transcript,
                                audio_start_sec=turn_start_sec,
                                audio_end_sec=turn_end_sec,
                                silence_duration_before_answer_sec=silence_gap_sec,
                                stt_latency_ms=stt_ms,
                                ttft_ms=0.0,
                                evaluation_branch_taken="next_topic",
                                eva_tone_used="direct"
                            )
                        self.current_question_text = next_q
                    else:
                        if self.session_logger:
                            stt_ms = getattr(Benchmark, "last_stt_ms", 0.0)
                            turn_seq = len(self.session_logger.turns) + 1
                            self.session_logger.log_turn(
                                turn_id=turn_seq,
                                topic=self.active_track or "Calibration",
                                question_text=self.current_question_text,
                                candidate_transcript=clean_transcript,
                                audio_start_sec=turn_start_sec,
                                audio_end_sec=turn_end_sec,
                                silence_duration_before_answer_sec=silence_gap_sec,
                                stt_latency_ms=stt_ms,
                                ttft_ms=0.0,
                                evaluation_branch_taken="next_topic",
                                eva_tone_used="direct"
                            )
                        self.update_status("Calibration Complete!")
                        self.append_ui_text("\n[System]: Calibration complete!")
                        Clock.schedule_once(lambda dt: self._update_script_display())
                        self.stop_interview()
                        break

        except Exception as e:
            import traceback
            traceback.print_exc()
            self.update_status(f"Pipeline Error: {e!s}")


class SessionHistoryScreen(Screen):
    """
    Dedicated full-page screen displaying historical session output directories,
    manifest telemetry, turn dialogue transcripts, and an interactive audio player
    with real-time progress bar and a compact Back-to-Interview button in the left pane header.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.active_audio_path = None
        self.active_duration = 0.0
        self.is_audio_playing = False
        self.audio_thread = None

    def on_enter(self):
        self.refresh_history()

    def go_back_to_interview(self):
        self.stop_selected_audio()
        if self.manager:
            self.manager.current = 'interview_screen'

    def refresh_history(self, auto_select_path=None):
        layout = self.ids.sessions_list_layout
        layout.clear_widgets()

        base_model_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        output_dir = os.path.join(base_model_dir, "test", "output")
        backend_root = os.path.abspath(os.path.join(base_model_dir, "..", ".."))
        sessions_dir = os.path.join(backend_root, "sessions")

        found_sessions = []

        for target_dir in [output_dir, sessions_dir]:
            if os.path.exists(target_dir):
                for folder_name in os.listdir(target_dir):
                    fpath = os.path.join(target_dir, folder_name)
                    if os.path.isdir(fpath) and folder_name.startswith("sess_"):
                        manifest_file = os.path.join(fpath, "transcript.json")
                        if not os.path.exists(manifest_file):
                            manifest_file = os.path.join(fpath, "session_manifest.json")
                        rec_file = os.path.join(fpath, "recording.wav")
                        mtime = os.path.getmtime(fpath)
                        found_sessions.append({
                            "folder_name": folder_name,
                            "path": fpath,
                            "manifest_file": manifest_file,
                            "rec_file": rec_file,
                            "mtime": mtime
                        })

        found_sessions.sort(key=lambda s: s["mtime"], reverse=True)

        if not found_sessions:
            no_s_btn = Button(
                text="No past session outputs found.",
                disabled=True,
                size_hint_y=None,
                height="40dp"
            )
            layout.add_widget(no_s_btn)
            return

        target_to_select = None
        for s_info in found_sessions:
            has_rec = "[REC]" if os.path.exists(s_info["rec_file"]) else "[NO-REC]"
            has_man = "[DATA]" if os.path.exists(s_info["manifest_file"]) else "[NO-DATA]"
            btn_text = f"{s_info['folder_name']} {has_rec}{has_man}"

            btn = Button(
                text=btn_text,
                font_size="12sp",
                size_hint_y=None,
                height="38dp",
                background_normal="",
                background_color=(0.18, 0.22, 0.3, 1)
            )
            btn.bind(on_press=lambda inst, info=s_info: self.display_session_details(info))
            layout.add_widget(btn)

            if auto_select_path and os.path.abspath(s_info["path"]) == os.path.abspath(auto_select_path):
                target_to_select = s_info

        if target_to_select:
            self.display_session_details(target_to_select)
        elif found_sessions:
            self.display_session_details(found_sessions[0])

    def display_session_details(self, s_info):
        self.stop_selected_audio()
        fpath = s_info["path"]
        rec_path = s_info["rec_file"]
        man_path = s_info["manifest_file"]

        rec_exists = os.path.exists(rec_path)
        man_exists = os.path.exists(man_path)

        if rec_exists:
            self.active_audio_path = rec_path
            self.ids.play_audio_btn.disabled = False
            try:
                with wave.open(rec_path, 'rb') as wf:
                    n_frames = wf.getnframes()
                    framerate = wf.getframerate()
                    duration = n_frames / float(framerate) if framerate > 0 else 0.0
                    self.active_duration = duration
                    dur_str = f"{int(duration // 60)}:{int(duration % 60):02d}"
                    self.ids.audio_time_label.text = f"0:00 / {dur_str}"
            except Exception:
                self.active_duration = 0.0
                self.ids.audio_time_label.text = "Ready to Play"
        else:
            self.active_audio_path = None
            self.active_duration = 0.0
            self.ids.play_audio_btn.disabled = True
            self.ids.audio_time_label.text = "0:00 / 0:00"

        self.ids.audio_progress_bar.value = 0.0

        details = [
            "[b][color=00ffcc]📂 SESSION OUTPUT DIRECTORY:[/color][/b]",
            f"[color=aaaaaa]{fpath}[/color]\n",
            "[b][color=ffcc00]📄 OUTPUT ARTIFACTS STATUS:[/color][/b]",
            f"  • [b]recording.wav:[/b] {'[color=00ff88]🟢 Created & Ready for Playback[/color]' if rec_exists else '[color=ff5555]🔴 Missing[/color]'}",
            f"  • [b]session_manifest.json:[/b] {'[color=00ff88]🟢 Created & Saved[/color]' if man_exists else '[color=ff5555]🔴 Missing[/color]'}\n"
        ]

        if man_exists:
            try:
                with open(man_path, "r", encoding="utf-8") as f:
                    manifest = json.load(f)

                turns = manifest.get("turns", [])
                total_turns = manifest.get("total_turns", len(turns))
                session_start = manifest.get("session_start_iso", "N/A")

                strong_cnt = sum(1 for t in turns if t.get("evaluation_branch_taken") == "strong_followup")
                weak_cnt = sum(1 for t in turns if t.get("evaluation_branch_taken") == "weak_followup")
                next_cnt = total_turns - strong_cnt - weak_cnt

                details.append("[b][color=00ff88]📊 TELEMETRY & BRANCHING BREAKDOWN:[/color][/b]")
                details.append(f"  • [b]Session Start ISO:[/b] [color=cccccc]{session_start}[/color]")
                details.append(f"  • [b]Total Interview Turns:[/b] [color=ffffff]{total_turns}[/color]")
                details.append(f"  • [b]Branching:[/b] [color=00ff88]{strong_cnt} Strong Follow-ups[/color] | [color=ffcc00]{weak_cnt} Weak Probes[/color] | [color=66ccff]{next_cnt} Next Topics[/color]\n")

                if turns:
                    details.append("[b][color=ffffff]💬 TURN-BY-TURN DIALOGUE TRANSCRIPT:[/color][/b]\n")
                    for t in turns:
                        t_id = t.get("turn_id", 0)
                        topic = t.get("topic", "General")
                        q_text = t.get("question_text", "")
                        ans_text = t.get("candidate_transcript", "")
                        branch = t.get("evaluation_branch_taken", "next_topic")
                        stt_ms = t.get("stt_latency_ms", 0.0)
                        ttft_ms = t.get("ttft_ms", 0.0)
                        start_s = round(t.get("audio_start_sec", 0.0), 1)
                        end_s = round(t.get("audio_end_sec", 0.0), 1)

                        branch_color = "00ff88" if branch == "strong_followup" else ("ffcc00" if branch == "weak_followup" else "66ccff")

                        details.append(
                            f"[b][color=ff8800]Turn {t_id}[/color] [{topic}][/b] ({start_s}s → {end_s}s)\n"
                            f"  [b]Branch:[/b] [color={branch_color}]{branch}[/color]\n"
                            f"  [b][color=66ccff]Eva Question:[/color][/b] {q_text}\n"
                            f"  [b][color=00ff88]Candidate Response:[/color][/b] \"{ans_text}\"\n"
                            f"  [color=888888]⚡ Performance: STT {stt_ms:.0f}ms | TTFT {ttft_ms:.0f}ms[/color]\n"
                        )
            except Exception as e:
                details.append(f"[color=ff5555]Error parsing session_manifest.json: {e}[/color]")

        self.ids.detail_label.text = "\n".join(details)

    def play_selected_audio(self):
        if not self.active_audio_path or not os.path.exists(self.active_audio_path):
            return

        self.is_audio_playing = True
        self.ids.play_audio_btn.disabled = True
        self.ids.stop_audio_btn.disabled = False

        def _play_loop():
            try:
                import sounddevice as sd
                import soundfile as sf
                data, fs = sf.read(self.active_audio_path, dtype='float32')
                duration = len(data) / float(fs) if fs > 0 else 0.0
                sd.play(data, fs)

                start_time = time.time()
                while self.is_audio_playing:
                    elapsed = time.time() - start_time
                    if elapsed >= duration:
                        elapsed = duration
                        progress = 1.0
                        Clock.schedule_once(lambda dt, e=elapsed, d=duration, p=progress: self._update_audio_ui(e, d, p))
                        break
                    progress = min(elapsed / duration, 1.0) if duration > 0 else 0.0
                    Clock.schedule_once(lambda dt, e=elapsed, d=duration, p=progress: self._update_audio_ui(e, d, p))
                    time.sleep(0.1)

            except Exception as e:
                print(f"[Audio Player Error] {e}", flush=True)
            finally:
                self.is_audio_playing = False
                Clock.schedule_once(lambda dt: self._reset_audio_ui())

        self.audio_thread = threading.Thread(target=_play_loop, daemon=True)
        self.audio_thread.start()

    def stop_selected_audio(self):
        self.is_audio_playing = False
        try:
            import sounddevice as sd
            sd.stop()
        except Exception:
            pass
        self._reset_audio_ui()

    def _update_audio_ui(self, elapsed, duration, progress):
        if "audio_progress_bar" in self.ids:
            self.ids.audio_progress_bar.value = progress
        if "audio_time_label" in self.ids:
            el_str = f"{int(elapsed // 60)}:{int(elapsed % 60):02d}"
            dur_str = f"{int(duration // 60)}:{int(duration % 60):02d}"
            self.ids.audio_time_label.text = f"{el_str} / {dur_str}"

    def _reset_audio_ui(self):
        if hasattr(self, "ids"):
            if "play_audio_btn" in self.ids:
                self.ids.play_audio_btn.disabled = False if (self.active_audio_path and os.path.exists(self.active_audio_path)) else True
            if "stop_audio_btn" in self.ids:
                self.ids.stop_audio_btn.disabled = True
            if "audio_progress_bar" in self.ids:
                self.ids.audio_progress_bar.value = 0.0


class AIInterviewerApp(App):

    def build(self):
        Builder.load_string(KV)
        sm = ScreenManager(transition=FadeTransition())
        sm.add_widget(InterviewScreen(name='interview_screen'))
        sm.add_widget(SessionHistoryScreen(name='history_screen'))
        return sm


if __name__ == "__main__":
    AIInterviewerApp().run()