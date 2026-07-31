"""
Netran AI — Stage 3: Live Voice-to-Voice Loop
Module: front.py
Description: Multi-screen Kivy Desktop GUI application featuring:
             1. InterviewScreen: Live voice interview engine with preset loader and real-time VAD.
             2. SessionHistoryScreen: Dedicated full-page output inspector, telemetry breakdown,
                header Back-to-Interview button, and real-time audio playback engine with progress bar.
"""

import difflib
from datetime import datetime, timezone
import json
import os
import re
import threading
import time
import wave

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.screenmanager import FadeTransition, Screen, ScreenManager

# Set compact, well-proportioned desktop window dimensions
Window.size = (1120, 700)
Window.minimum_width = 1000
Window.minimum_height = 620

try:
    from .benchmark import Benchmark
    from .brain import TextSanitizer, generate_eva_response
    from .brain import preload as preload_brain
    from .listener import ContinuousMicWriter, listen_and_transcribe
    from .question_manager import QuestionManager
    from .schemas import load_stage2_bundle
    from .session_logger import SessionLogger
    from .speaker import preload_models as preload_speaker
    from .speaker import speak_text, init_speaker_compat, StreamingTTSPlayer
    from .session_state import SessionState
except ImportError:
    try:
        from model.voice_to_voice_model.model.benchmark import Benchmark
        from model.voice_to_voice_model.model.brain import (
            TextSanitizer,
            generate_eva_response,
        )
        from model.voice_to_voice_model.model.brain import preload as preload_brain
        from model.voice_to_voice_model.model.listener import (
            ContinuousMicWriter,
            listen_and_transcribe,
        )
        from model.voice_to_voice_model.model.question_manager import QuestionManager
        from model.voice_to_voice_model.model.schemas import load_stage2_bundle
        from model.voice_to_voice_model.model.session_logger import SessionLogger
        from model.voice_to_voice_model.model.speaker import (
            preload_models as preload_speaker,
        )
        from model.voice_to_voice_model.model.speaker import speak_text, init_speaker_compat, StreamingTTSPlayer
        from model.voice_to_voice_model.model.session_state import SessionState
    except ImportError:
        from benchmark import Benchmark
        from brain import TextSanitizer, generate_eva_response
        from brain import preload as preload_brain
        from listener import ContinuousMicWriter, listen_and_transcribe
        from question_manager import QuestionManager
        from schemas import load_stage2_bundle
        from session_logger import SessionLogger
        from speaker import preload_models as preload_speaker
        from speaker import speak_text, init_speaker_compat, StreamingTTSPlayer
        from session_state import SessionState


# Multi-Screen KV layout definition with responsive proportions
KV = """
<InterviewScreen>:
    name: 'interview_screen'
    orientation: 'vertical'
    padding: 12
    spacing: 10
    canvas.before:
        Color:
            rgba: 0.08, 0.08, 0.1, 1
        Rectangle:
            pos: self.pos
            size: self.size

    # MAIN SPLIT CONTENT AREA
    BoxLayout:
        orientation: 'horizontal'
        spacing: 12
        size_hint_y: 1.0

        # LEFT PANE: CONFIGURATION & STAGE 2 PRESETS
        BoxLayout:
            orientation: 'vertical'
            size_hint_x: 0.36
            spacing: 8
            padding: 8
            canvas.before:
                Color:
                    rgba: 0.11, 0.11, 0.14, 1
                RoundedRectangle:
                    pos: self.pos
                    size: self.size
                    radius: [8]

            Label:
                text: "Session & Input Controls"
                font_size: '15sp'
                bold: True
                size_hint_y: None
                height: '24dp'
                color: 0.3, 0.6, 0.8, 1

            Label:
                text: "Stage 2 Preset Bundle:"
                font_size: '12sp'
                size_hint_y: None
                height: '18dp'
                halign: 'left'
                color: 0.7, 0.7, 0.7, 1

            Spinner:
                id: preset_selector
                text: 'Preset: sample_backend'
                values: ('Preset: sample_backend', 'Preset: sample_frontend', 'Preset: sample_fullstack')
                size_hint_y: None
                height: '34dp'
                font_size: '12sp'
                on_text: root.on_preset_select(self.text)

            ToggleButton:
                id: mode_toggle
                text: 'LLM Engine: ACTIVE'
                state: 'down'
                size_hint_y: None
                height: '34dp'
                font_size: '12sp'
                background_color: 0.2, 0.4, 0.6, 1
                on_press: root.toggle_llm_mode(self)

            Spinner:
                id: limit_selector
                text: '5 Questions (Fast Test)'
                values: ('5 Questions (Fast Test)', '10 Questions (Standard)', '15 Questions (Full Tree)', 'All Available Questions')
                size_hint_y: None
                height: '34dp'
                font_size: '12sp'
                on_text: root.on_limit_select(self.text)

            Spinner:
                id: pause_tolerance
                text: '⚖️ Balanced (1.6s)'
                values: ('⚡ Fast Response (1.0s)', '⚖️ Balanced (1.6s)', '🧠 Deep Thinker (2.2s)')
                size_hint_y: None
                height: '34dp'
                font_size: '12sp'
                on_text: root.on_pause_select(self.text)

            Spinner:
                id: script_selector
                text: 'Select Calibration Track'
                values: ('React.js Core', 'Next.js & Server Architecture', 'TypeScript Essentials', 'Frontend Build Tools', 'CSS & Tailwind UI')
                size_hint_y: None
                height: '34dp'
                font_size: '12sp'
                disabled: True
                on_text: root.on_track_select(self.text)

            ScrollView:
                size_hint_y: 1.0
                canvas.before:
                    Color:
                        rgba: 0.07, 0.07, 0.09, 1
                    RoundedRectangle:
                        pos: self.pos
                        size: self.size
                        radius: [6]

                Label:
                    id: target_script_label
                    text: "[Loaded Stage 2 Input Bundle details will appear here.]"
                    font_size: '12sp'
                    text_size: self.width - 16, None
                    size_hint_y: None
                    height: max(self.texture_size[1], self.parent.height)
                    halign: 'left'
                    valign: 'top'
                    padding: [8, 8]
                    markup: True

        # RIGHT PANE: LIVE INTERVIEW PANEL, TOP HISTORY BAR & AUDIO VISUALIZER
        BoxLayout:
            orientation: 'vertical'
            size_hint_x: 0.64
            spacing: 8

            # TOP ACTION BAR IN RIGHT PANE: PROMINENT HISTORY BUTTON & STATUS BADGE
            BoxLayout:
                orientation: 'horizontal'
                size_hint_y: None
                height: '38dp'
                spacing: 10
                padding: [2, 0]

                Button:
                    id: history_btn
                    text: "📜 View Session Output History"
                    font_size: '13sp'
                    bold: True
                    background_normal: ''
                    background_color: 0.22, 0.45, 0.75, 1
                    on_press: root.open_history_screen()

                Label:
                    id: header_status_badge
                    text: "System Ready"
                    font_size: '13sp'
                    bold: True
                    size_hint_x: 0.35
                    halign: 'right'
                    valign: 'middle'
                    color: 0.3, 0.9, 0.5, 1

            Label:
                id: status_label
                text: "System Online"
                font_size: '15sp'
                bold: True
                size_hint_y: None
                height: '22dp'
                color: 0.6, 0.4, 0.9, 1

            Label:
                id: question_label
                text: "Question Progress: 0 / 5"
                font_size: '14sp'
                bold: True
                size_hint_y: None
                height: '22dp'
                color: 0.8, 0.8, 0.8, 1

            # VAD DIAGNOSTICS & VOLUME BAR
            BoxLayout:
                orientation: 'vertical'
                size_hint_y: None
                height: '46dp'
                canvas.before:
                    Color:
                        rgba: 0.14, 0.14, 0.18, 1
                    RoundedRectangle:
                        pos: self.pos
                        size: self.size
                        radius: [6]
                padding: 4

                Label:
                    id: vad_state_label
                    text: "Mic: Offline"
                    font_size: '12sp'
                    color: 0.8, 0.8, 0.8, 1
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
                        rgba: 0.12, 0.12, 0.15, 1
                    RoundedRectangle:
                        pos: self.pos
                        size: self.size
                        radius: [8]

                Label:
                    id: transcript_display
                    text: "--- Netran AI Live Voice Panel ---\\n"
                    markup: True
                    font_size: '14sp'
                    size_hint_y: None
                    height: max(self.texture_size[1], self.parent.height)
                    text_size: self.width - 20, None
                    halign: 'left'
                    valign: 'top'
                    padding: [10, 10]

            # CONTROL BUTTONS BAR (CLEAN 3 BUTTONS ONLY)
            BoxLayout:
                orientation: 'horizontal'
                spacing: 8
                size_hint_y: None
                height: '44dp'

                Button:
                    id: start_btn
                    text: "Start Interview"
                    font_size: '12sp'
                    bold: True
                    size_hint_x: 0.33
                    background_normal: ''
                    background_color: 0.15, 0.6, 0.3, 1
                    on_press: root.start_interview()

                Button:
                    id: stop_btn
                    text: "Final Stop & Output"
                    font_size: '12sp'
                    bold: True
                    size_hint_x: 0.33
                    background_normal: ''
                    background_color: 0.8, 0.25, 0.25, 1
                    disabled: True
                    on_press: root.stop_interview()

                Button:
                    id: restart_btn
                    text: "Restart Session"
                    font_size: '12sp'
                    bold: True
                    size_hint_x: 0.33
                    background_normal: ''
                    background_color: 0.25, 0.45, 0.75, 1
                    on_press: root.restart_interview()


<SessionHistoryScreen>:
    name: 'history_screen'
    orientation: 'vertical'
    padding: 12
    spacing: 10
    canvas.before:
        Color:
            rgba: 0.08, 0.08, 0.1, 1
        Rectangle:
            pos: self.pos
            size: self.size

    # TOP APPLICATION HEADER BAR WITH PROMINENT BACK BUTTON
    BoxLayout:
        orientation: 'horizontal'
        size_hint_y: None
        height: '46dp'
        padding: [10, 4]
        spacing: 10
        canvas.before:
            Color:
                rgba: 0.12, 0.12, 0.16, 1
            RoundedRectangle:
                pos: self.pos
                size: self.size
                radius: [6]

        Button:
            text: "⬅️ Back to Live Interview"
            font_size: '13sp'
            bold: True
            size_hint_x: 0.35
            background_normal: ''
            background_color: 0.15, 0.55, 0.45, 1
            on_press: root.go_back_to_interview()

        Label:
            text: "[b]Netran AI[/b] — Session Output & History Inspector"
            markup: True
            font_size: '16sp'
            halign: 'left'
            valign: 'middle'
            size_hint_x: 0.45
            color: 0.4, 0.8, 1, 1

        Label:
            text: "Stage 3 Output Data"
            font_size: '13sp'
            bold: True
            halign: 'right'
            valign: 'middle'
            size_hint_x: 0.2
            color: 0.3, 0.9, 0.5, 1

    # MAIN SPLIT CONTENT AREA
    BoxLayout:
        orientation: 'horizontal'
        spacing: 12
        size_hint_y: 1.0

        # LEFT PANE: PAST SESSIONS LIST WITH HEADER BACK BUTTON
        BoxLayout:
            orientation: 'vertical'
            size_hint_x: 0.34
            spacing: 8
            padding: 8
            canvas.before:
                Color:
                    rgba: 0.11, 0.11, 0.14, 1
                RoundedRectangle:
                    pos: self.pos
                    size: self.size
                    radius: [8]

            # LEFT PANE HEADER: COMPACT BACK BUTTON & TITLE
            BoxLayout:
                orientation: 'horizontal'
                size_hint_y: None
                height: '32dp'
                spacing: 6

                Button:
                    text: "⬅️ Back"
                    font_size: '12sp'
                    bold: True
                    size_hint_x: 0.38
                    background_normal: ''
                    background_color: 0.15, 0.55, 0.45, 1
                    on_press: root.go_back_to_interview()

                Label:
                    text: "Past Sessions:"
                    font_size: "13sp"
                    bold: True
                    size_hint_x: 0.62
                    halign: "left"
                    valign: "middle"
                    color: 0.8, 0.8, 0.8, 1

            ScrollView:
                size_hint_y: 1.0
                BoxLayout:
                    id: sessions_list_layout
                    orientation: 'vertical'
                    spacing: 5
                    size_hint_y: None

        # RIGHT PANE: SELECTED SESSION DETAIL & AUDIO PLAYER
        BoxLayout:
            orientation: 'vertical'
            size_hint_x: 0.66
            spacing: 8

            # AUDIO PLAYER BAR WITH PROGRESS & TIME TRACKING
            BoxLayout:
                orientation: 'vertical'
                size_hint_y: None
                height: '70dp'
                padding: 6
                spacing: 4
                canvas.before:
                    Color:
                        rgba: 0.13, 0.15, 0.2, 1
                    RoundedRectangle:
                        pos: self.pos
                        size: self.size
                        radius: [6]

                BoxLayout:
                    orientation: 'horizontal'
                    spacing: 8
                    size_hint_y: 0.5

                    Button:
                        id: play_audio_btn
                        text: "Play Audio Recording"
                        font_size: "12sp"
                        bold: True
                        disabled: True
                        size_hint_x: 0.5
                        background_normal: ""
                        background_color: 0.15, 0.6, 0.35, 1
                        on_press: root.play_selected_audio()

                    Button:
                        id: stop_audio_btn
                        text: "Stop Audio"
                        font_size: "12sp"
                        bold: True
                        disabled: True
                        size_hint_x: 0.3
                        background_normal: ""
                        background_color: 0.8, 0.25, 0.25, 1
                        on_press: root.stop_selected_audio()

                    Label:
                        id: audio_time_label
                        text: "0:00 / 0:00"
                        font_size: "12sp"
                        bold: True
                        size_hint_x: 0.2
                        color: 0.4, 0.8, 1, 1

                ProgressBar:
                    id: audio_progress_bar
                    max: 1.0
                    value: 0.0
                    size_hint_y: 0.5

            # DETAIL TRANSCRIPT SCROLLVIEW
            ScrollView:
                size_hint_y: 1.0
                canvas.before:
                    Color:
                        rgba: 0.12, 0.12, 0.15, 1
                    RoundedRectangle:
                        pos: self.pos
                        size: self.size
                        radius: [8]

                Label:
                    id: detail_label
                    text: "[Select a session folder from the left pane to inspect generated outputs.]"
                    markup: True
                    font_size: "13sp"
                    text_size: self.width - 32, None
                    size_hint_y: None
                    height: max(self.texture_size[1] + 30, self.parent.height)
                    halign: "left"
                    valign: "top"
                    padding: [14, 14]
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
        test_out_dir = os.path.join(os.path.dirname(__file__), "test_output")
        os.makedirs(test_out_dir, exist_ok=True)
        self.log_filename = os.path.join(test_out_dir, "interview_log.txt")
        self.conversation_history = []
        self.question_count = 0
        self.MAX_QUESTIONS = 5  # Default to 5 questions during testing time

        # Session artifacts tracking
        self.session_logger = None
        self.mic_writer = None
        self.session_dir = None
        self.current_question_text = ""
        self.last_eva_speech_end_sec = 0.0

        # State variables for Script Calibration Mode & Stage 2 Bundle
        self.llm_enabled = True
        self.calibration_scripts = {}
        self.active_track = None
        self.current_track_data = []
        self.stage2_bundle = None
        self.question_manager = None
        self.selected_preset_name = "sample_backend"

        self.session_state = SessionState()
        self.tts_player = None

        self._load_calibration_scripts()
        self._load_selected_preset(self.selected_preset_name)

    def on_pause_select(self, text):
        if "1.0s" in text:
            self.session_state.pause_tolerance_ms = 1000
        elif "1.6s" in text:
            self.session_state.pause_tolerance_ms = 1600
        elif "2.2s" in text:
            self.session_state.pause_tolerance_ms = 2200

    def _load_calibration_scripts(self):
        script_dir = os.path.dirname(__file__)
        json_path = os.path.join(script_dir, "interview_scripts.json")
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                self.calibration_scripts = json.load(f)
        except Exception as e:
            print(f"[Error loading scripts] {e}")

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
                self.ids.question_label.text = f"Question Progress: {count} / {self.MAX_QUESTIONS}"
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
            self.question_manager = QuestionManager(self.stage2_bundle.questions)

        session_id = f"sess_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
        model_root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        test_out_dir = os.path.join(model_root_dir, "test", "output")
        self.session_dir = os.path.join(test_out_dir, session_id)
        os.makedirs(self.session_dir, exist_ok=True)

        with open(self.log_filename, "w", encoding="utf-8") as f:
            f.write(
                f"=== AI INTERVIEW LOG: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} ===\n\n"
            )

        self.session_logger = SessionLogger(session_id=session_id, session_dir=self.session_dir)
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

    def update_audio_diagnostics(self, data):
        def _update(dt):
            if "vad_state_label" in self.ids:
                self.ids.vad_state_label.text = data.get("state", "")
            if "volume_bar" in self.ids:
                rms = data.get("rms", 0.0)
                self.ids.volume_bar.value = min(rms * 10, 1.0)
        Clock.schedule_once(_update)

    def log_and_display_turn(self, speaker, text):
        timestamp = datetime.now(timezone.utc).strftime("%H:%M:%S")
        formatted_log = f"[{timestamp}] {speaker}: {text}"
        
        if speaker == "Eva":
            formatted_ui = f"[color=00ccff][b]🎙️ {speaker}:[/b][/color] {text}"
        elif speaker == "You":
            formatted_ui = f"[color=66ff66]🗣️ {speaker}:[/color] {text}"
        else:
            formatted_ui = f"[color=ffcc00]⚙️ [{speaker}]:[/color] {text}"

        with open(self.log_filename, "a", encoding="utf-8") as f:
            f.write(formatted_log + "\n")

        self.append_ui_text(formatted_ui)

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
                    initial_greeting = f"Hello! I am Eva. Let us begin your technical evaluation. Here is your first question: {q1.question_text}"
                    self.current_question_text = q1.question_text
                else:
                    initial_greeting = "Hello! Welcome to your technical interview today. Could you please start by describing your core backend stack?"
                    self.current_question_text = initial_greeting

                self.log_and_display_turn("Eva", initial_greeting)
                turn1_history = f"<think>\nStarting the interview and asking the first question.\n</think>\n<speak>\n{initial_greeting}\n</speak>"
                self.conversation_history.append({"role": "assistant", "content": turn1_history})
                self.question_count = 1
                self.update_question_label(self.question_count)
                self.update_status("Eva is speaking...")
                speak_text(initial_greeting)
                if self.session_logger:
                    self.last_eva_speech_end_sec = self.session_logger.elapsed_sec()

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
                speak_text(initial_greeting)
                if self.session_logger:
                    self.last_eva_speech_end_sec = self.session_logger.elapsed_sec()

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
                    if self.question_manager and not self.question_manager.is_finished():
                        branch_taken = self.question_manager.evaluate_transcript(clean_transcript)
                        llm_prompt, target_question = self.question_manager.format_prompt_context(branch_taken, clean_transcript)
                        prompt_ctx = llm_prompt
                        if branch_taken == "next_topic":
                            self.question_manager.advance_question()

                    self.log_and_display_turn("You", clean_transcript)
                    self.append_ui_text(f"[color=ff8800]📊 [Branch Taken]:[/color] {branch_taken}")
                    self.conversation_history.append({"role": "user", "content": prompt_ctx})
                    
                    import random
                    fillers = ["Okay.", "Right.", "Alright.", "Mmhmm.", "Got it."]
                    filler = random.choice(fillers)
                    speak_text(filler)

                    self.update_status("Eva is evaluating...")
                    Benchmark.start("ttft")
                    from model.voice_to_voice_model.model.prompts import get_system_prompt
                    sys_prompt_dict = get_system_prompt(self.stage2_bundle.system_prompt if self.stage2_bundle else None)
                    sys_prompt = sys_prompt_dict["content"]
                    
                    MAX_HISTORY_MESSAGES = 8
                    if len(self.conversation_history) > MAX_HISTORY_MESSAGES:
                        trimmed_history = self.conversation_history[:2] + self.conversation_history[-(MAX_HISTORY_MESSAGES-2):]
                    else:
                        trimmed_history = self.conversation_history

                    think_text, speak_content = generate_eva_response(trimmed_history, custom_system_prompt=sys_prompt)

                    Benchmark.end("ttft")
                    ttft_logged = True
                    current_ttft = Benchmark.last_ttft_ms if hasattr(Benchmark, 'last_ttft_ms') else 0.0

                    if think_text:
                        safe_think = think_text.replace("[", "&#91;").replace("]", "&#93;").replace("&", "&amp;")
                        grey_italic = f"[i][color=888888]🧠 [Eva thinking...]: {safe_think}[/color][/i]"
                        self.append_ui_text(grey_italic)
                        timestamp = datetime.now(timezone.utc).strftime("%H:%M:%S")
                        with open(self.log_filename, "a", encoding="utf-8") as f:
                            f.write(f"[{timestamp}] [Eva thinking...]: {think_text}\n")

                    full_eva_reply = speak_content
                    self.log_and_display_turn("Eva", speak_content)

                    ttfa_logged = False
                    current_ttfa = 0.0

                    if speak_content.strip() and self.is_running:
                        Benchmark.start("ttfa")
                        clean_speak = TextSanitizer.clean_for_tts(speak_content)
                        if clean_speak:
                            self.update_status(f"Eva is speaking... (Q {self.question_count + 1}/{self.MAX_QUESTIONS})")
                            speak_text(clean_speak)
                            if not self.is_running:
                                break
                        current_ttfa = Benchmark.end("ttfa")
                        ttfa_logged = True

                    if self.session_logger:
                        self.last_eva_speech_end_sec = self.session_logger.elapsed_sec()

                    if think_text:
                        history_content = f"<think>\n{think_text}\n</think>\n<speak>\n{speak_content}\n</speak>"
                    else:
                        history_content = f"<speak>\n{speak_content}\n</speak>"
                    self.conversation_history.append({"role": "assistant", "content": history_content})

                    stt_ms = getattr(Benchmark, "last_stt_ms", 0.0)
                    if ttft_logged and ttfa_logged:
                        Benchmark.log_metrics(stt_ms, current_ttft, current_ttfa)

                    if self.session_logger:
                        self.session_logger.log_turn(
                            turn_id=self.question_count,
                            topic="Technical Interview",
                            question_text=self.current_question_text,
                            candidate_transcript=clean_transcript,
                            audio_start_sec=turn_start_sec,
                            audio_end_sec=turn_end_sec,
                            silence_duration_before_answer_sec=silence_gap_sec,
                            stt_latency_ms=stt_ms,
                            ttft_ms=current_ttft,
                            evaluation_branch_taken=branch_taken,
                            eva_reasoning=think_text if 'think_text' in locals() else None,
                            eva_reply=speak_content if 'speak_content' in locals() else full_eva_reply
                        )

                    # Fix: Ensure the NEXT turn logs the actual question template text,
                    # not Eva's conversational generation.
                    self.current_question_text = target_question if 'target_question' in locals() else full_eva_reply
                    self.question_count += 1
                    self.update_question_label(self.question_count)

                    if self.question_count >= self.MAX_QUESTIONS:
                        self.update_status("Interview Complete — Wrapping Up")
                        closing = (
                            "That concludes our technical evaluation for today. "
                            "Thank you for your time, and we will follow up with detailed feedback shortly."
                        )
                        self.log_and_display_turn("Eva", closing)
                        self.conversation_history.append({"role": "assistant", "content": closing})
                        speak_text(closing)
                        self.append_ui_text(f"\n[System]: Session complete. {self.MAX_QUESTIONS} questions covered.")
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
                            self.session_logger.log_turn(
                                turn_id=self.question_count,
                                topic=self.active_track or "Calibration",
                                question_text=self.current_question_text,
                                candidate_transcript=clean_transcript,
                                audio_start_sec=turn_start_sec,
                                audio_end_sec=turn_end_sec,
                                silence_duration_before_answer_sec=silence_gap_sec,
                                stt_latency_ms=stt_ms,
                                ttft_ms=0.0,
                                evaluation_branch_taken="next_topic"
                            )
                        self.current_question_text = next_q
                    else:
                        if self.session_logger:
                            stt_ms = getattr(Benchmark, "last_stt_ms", 0.0)
                            self.session_logger.log_turn(
                                turn_id=self.question_count,
                                topic=self.active_track or "Calibration",
                                question_text=self.current_question_text,
                                candidate_transcript=clean_transcript,
                                audio_start_sec=turn_start_sec,
                                audio_end_sec=turn_end_sec,
                                silence_duration_before_answer_sec=silence_gap_sec,
                                stt_latency_ms=stt_ms,
                                ttft_ms=0.0,
                                evaluation_branch_taken="next_topic"
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