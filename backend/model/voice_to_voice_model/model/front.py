"""
Netran AI — Stage 3: Live Voice-to-Voice Loop
Module: front.py
Description: Standalone Kivy Desktop GUI client for testing live voice interviews and Script Calibration Mode.
"""

import threading
import time
import re
import os
import json
import difflib
from datetime import datetime
from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout

# Import the functional blocks we created in this exact folder
try:
    from .brain import generate_eva_response, preload as preload_brain
    from .listener import listen_and_transcribe, ContinuousMicWriter
    from .speaker import speak_text, preload_models as preload_speaker
    from .session_logger import SessionLogger
    from .benchmark import Benchmark
except ImportError:
    try:
        from model.voice_to_voice_model.model.brain import generate_eva_response, preload as preload_brain
        from model.voice_to_voice_model.model.listener import listen_and_transcribe, ContinuousMicWriter
        from model.voice_to_voice_model.model.speaker import speak_text, preload_models as preload_speaker
        from model.voice_to_voice_model.model.session_logger import SessionLogger
        from model.voice_to_voice_model.model.benchmark import Benchmark
    except ImportError:
        from brain import generate_eva_response, preload as preload_brain
        from listener import listen_and_transcribe, ContinuousMicWriter
        from speaker import speak_text, preload_models as preload_speaker
        from session_logger import SessionLogger
        from benchmark import Benchmark

# Clean visual layout utilizing a modern dark visual palette
KV = """
<InterviewWindow>:
    orientation: 'horizontal'
    padding: 20
    spacing: 20
    canvas.before:
        Color:
            rgba: 0.1, 0.1, 0.12, 1
        Rectangle:
            pos: self.pos
            size: self.size

    # LEFT PANE: SCRIPT CALIBRATION COMPONENT
    BoxLayout:
        orientation: 'vertical'
        size_hint_x: 0.5
        spacing: 15
        padding: 10
        canvas.before:
            Color:
                rgba: 0.13, 0.13, 0.15, 1
            RoundedRectangle:
                pos: self.pos
                size: self.size
                radius: [10]

        Label:
            text: "Script Calibration Mode"
            font_size: '18sp'
            bold: True
            size_hint_y: None
            height: '40dp'
            color: 0.3, 0.6, 0.8, 1

        ToggleButton:
            id: mode_toggle
            text: 'LLM Engine: ACTIVE'
            state: 'down'
            size_hint_y: None
            height: '40dp'
            background_color: 0.2, 0.4, 0.6, 1
            on_press: root.toggle_llm_mode(self)

        Spinner:
            id: limit_selector
            text: 'Fast Testing (5 Questions)'
            values: ('Fast Testing (5 Questions)', 'Real-Time Live (15 Questions)', 'Extended Live (10 Questions)')
            size_hint_y: None
            height: '40dp'
            on_text: root.on_limit_select(self.text)

        Spinner:
            id: script_selector
            text: 'Select Interview Track'
            values: ('React.js Core', 'Next.js & Server Architecture', 'TypeScript Essentials', 'Frontend Build Tools', 'CSS & Tailwind UI')
            size_hint_y: None
            height: '40dp'
            disabled: True
            on_text: root.on_track_select(self.text)

        ScrollView:
            size_hint_y: 0.7
            canvas.before:
                Color:
                    rgba: 0.08, 0.08, 0.1, 1
                RoundedRectangle:
                    pos: self.pos
                    size: self.size
                    radius: [8]
            
            Label:
                id: target_script_label
                text: "[Select a track and toggle Script Mode to begin calibration.]"
                text_size: self.width - 20, None
                size_hint_y: None
                height: max(self.texture_size[1], self.parent.height)
                halign: 'left'
                valign: 'top'
                padding: [10, 10]
                markup: True

    # RIGHT PANE: LIVE INTERVIEW TEST PIPELINE
    BoxLayout:
        orientation: 'vertical'
        size_hint_x: 0.5
        spacing: 15

        Label:
            id: status_label
            text: "System Online"
            font_size: '20sp'
            size_hint_y: None
            height: '40dp'
            color: 0.6, 0.3, 0.8, 1  # Professional purple accent

        Label:
            id: question_label
            text: "Question: 0 / 15"
            font_size: '16sp'
            size_hint_y: None
            height: '30dp'
            color: 0.8, 0.8, 0.8, 1

        BoxLayout:
            orientation: 'vertical'
            size_hint_y: None
            height: '60dp'
            canvas.before:
                Color:
                    rgba: 0.15, 0.15, 0.15, 1
                RoundedRectangle:
                    pos: self.pos
                    size: self.size
                    radius: [5]
            padding: 5
            
            Label:
                id: vad_state_label
                text: "Mic: Offline"
                font_size: '14sp'
                color: 0.8, 0.8, 0.8, 1
                size_hint_y: 0.5
                
            ProgressBar:
                id: volume_bar
                max: 1.0
                value: 0.0
                size_hint_y: 0.5

        ScrollView:
            size_hint_y: 0.65
            canvas.before:
                Color:
                    rgba: 0.15, 0.15, 0.18, 1
                RoundedRectangle:
                    pos: self.pos
                    size: self.size
                    radius: [10]
            
            TextInput:
                id: transcript_display
                text: "--- Live Interview Panel ---\\n"
                readonly: True
                background_color: 0, 0, 0, 0
                foreground_color: 1, 1, 1, 1
                font_size: '16sp'
                size_hint_y: None
                height: max(self.minimum_height, self.parent.height)
                padding: [15, 15]

        BoxLayout:
            orientation: 'horizontal'
            spacing: 20
            size_hint_y: None
            height: '60dp'

            Button:
                id: start_btn
                text: "Start Interview"
                background_normal: ''
                background_color: 0.2, 0.6, 0.3, 1
                on_press: root.start_interview()

            Button:
                id: send_btn
                text: "⚡ Done Speaking"
                background_normal: ''
                background_color: 0.6, 0.4, 0.9, 1
                on_press: root.submit_answer_now()

            Button:
                id: stop_btn
                text: "Stop & Save Log"
                background_normal: ''
                background_color: 0.8, 0.3, 0.3, 1
                disabled: True
                on_press: root.stop_interview()

            Button:
                id: restart_btn
                text: "Restart Interview"
                background_normal: ''
                background_color: 0.3, 0.5, 0.8, 1
                on_press: root.restart_interview()
"""


class InterviewWindow(BoxLayout):

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

        # State variables for Script Calibration Mode
        self.llm_enabled = True
        self.calibration_scripts = {}
        self.active_track = None
        self.current_track_data = []
        self._load_calibration_scripts()

    def _load_calibration_scripts(self):
        script_dir = os.path.dirname(__file__)
        json_path = os.path.join(script_dir, "interview_scripts.json")
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                self.calibration_scripts = json.load(f)
        except Exception as e:
            print(f"[Error loading scripts] {e}")

    def on_limit_select(self, text):
        if "5" in text:
            self.MAX_QUESTIONS = 5
        elif "15" in text:
            self.MAX_QUESTIONS = 15
        elif "10" in text:
            self.MAX_QUESTIONS = 10
        self.update_question_label(self.question_count)

    def toggle_llm_mode(self, toggle_btn):
        if toggle_btn.state == 'down':
            self.llm_enabled = True
            toggle_btn.text = 'LLM Engine: ACTIVE'
            self.ids.script_selector.disabled = True
            self.ids.target_script_label.text = "[Running in dynamic live mode via Qwen LLM.]"
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

    def _update_script_display(self):
        if self.llm_enabled:
            self.ids.target_script_label.text = "[Running in dynamic live mode via Qwen LLM.]"
            return
        
        if not self.active_track or not self.current_track_data:
            self.ids.target_script_label.text = "[Select a track from the dropdown above to view the script.]"
            return
        
        idx = self.question_count
        if idx < len(self.current_track_data):
            q_data = self.current_track_data[idx]
            self.ids.target_script_label.text = (
                f"[b]TRACK:[/b] {self.active_track}\n"
                f"[b]QUESTION {idx + 1}:[/b] {q_data['question']}\n\n"
                f"[b]TARGET ANSWER TO READ ALOUD:[/b]\n"
                f"[color=00ff00]{q_data['answer']}[/color]"
            )
        else:
            self.ids.target_script_label.text = "[Calibration track complete! Click Restart or select a new track.]"

    def _reset_buttons(self):
        self.ids.start_btn.disabled = False
        self.ids.stop_btn.disabled = True
        self.ids.restart_btn.disabled = False

    def update_question_label(self, count):
        Clock.schedule_once(lambda dt: setattr(self.ids.question_label, "text", f"Question: {count} / {self.MAX_QUESTIONS}"))

    def start_interview(self):
        self.ids.start_btn.disabled = True
        self.ids.stop_btn.disabled = False
        self.is_running = True
        self.conversation_history = []
        self.question_count = 0
        self.update_question_label(0)

        # Initialize Session Logger & Continuous Mic Writer inside test/output/
        session_id = f"sess_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        model_root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        test_out_dir = os.path.join(model_root_dir, "test", "output")
        self.session_dir = os.path.join(test_out_dir, session_id)
        os.makedirs(self.session_dir, exist_ok=True)

        # Write clean session start to log file
        with open(self.log_filename, "w", encoding="utf-8") as f:
            f.write(
                f"=== AI INTERVIEW LOG: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n\n"
            )

        self.session_logger = SessionLogger(session_id=session_id, session_dir=self.session_dir)
        mic_wav_path = os.path.join(self.session_dir, "recording.wav")
        self.mic_writer = ContinuousMicWriter(filepath=mic_wav_path)
        self.mic_writer.start()

        self.update_status("Initializing AI Models... (Please wait)")
        self.append_ui_text("\n[System]: Pre-heating AI pipelines...\n")

        # Start processing inside background thread
        self.interview_thread = threading.Thread(
            target=self._run_interview_pipeline, daemon=True
        )
        self.interview_thread.start()

    def submit_answer_now(self):
        """Forces immediate speech endpointing when candidate finishes speaking."""
        try:
            from .listener import trigger_speech_done
            trigger_speech_done()
        except Exception:
            try:
                from listener import trigger_speech_done
                trigger_speech_done()
            except Exception:
                pass
        self.update_status("⚡ Processing answer immediately...")

    def stop_interview(self):
        self.is_running = False
        if self.mic_writer:
            self.mic_writer.stop()
            self.mic_writer = None
        if self.session_dir and os.path.exists(os.path.join(self.session_dir, "recording.wav")):
            try:
                import shutil
                shutil.copyfile(
                    os.path.join(self.session_dir, "recording.wav"),
                    os.path.join(self.session_dir, "continuous_mic_input.wav")
                )
            except Exception:
                pass
        if self.session_logger:
            self.session_logger.finalize()
            self.session_logger = None
        Clock.schedule_once(lambda dt: self._reset_buttons())
        self.update_status("Interview Stopped.")
        self.append_ui_text("\n[System]: Log file finalized successfully.")

    def restart_interview(self):
        self.stop_interview()
        # Clear transcript display
        Clock.schedule_once(lambda dt: setattr(self.ids.transcript_display, "text", "--- Live Interview Panel ---\n\n"))
        # Give the previous thread a tiny moment to exit before starting a new one
        Clock.schedule_once(lambda dt: self.start_interview(), 0.5)

    def update_status(self, text):
        Clock.schedule_once(lambda dt: setattr(self.ids.status_label, "text", text))

    def append_ui_text(self, text):
        def _update(dt):
            self.ids.transcript_display.text += f"{text}\n"

        Clock.schedule_once(_update)

    def update_audio_diagnostics(self, data):
        def _update(dt):
            self.ids.vad_state_label.text = data.get("state", "")
            # Scale RMS up for visibility in the progress bar (RMS is typically small)
            rms = data.get("rms", 0.0)
            self.ids.volume_bar.value = min(rms * 10, 1.0)
        Clock.schedule_once(_update)

    def log_and_display_turn(self, speaker, text):
        """Saves turn directly to file system log and logs live onto UI panel screen."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_line = f"[{timestamp}] {speaker}: {text}"

        with open(self.log_filename, "a", encoding="utf-8") as f:
            f.write(formatted_line + "\n")

        self.append_ui_text(formatted_line)

    def _run_interview_pipeline(self):
        """Main automated hardware pipeline loop linking components."""
        try:
            # --- PRELOAD STAGE ---
            preload_speaker()
            if self.llm_enabled:
                preload_brain()
            self.update_status("Eva is initializing speech channels...")
            self.append_ui_text("[System]: Voice pipeline connected.\n")

            # --- TURN 1: EVA INITIATES CONVERSATION ---
            if self.llm_enabled:
                initial_greeting = "Hello! Welcome to your technical interview today. [Clears Throat] Could you please start by describing your core frontend stack?"
                self.current_question_text = initial_greeting
                self.log_and_display_turn("Eva", initial_greeting)
                self.conversation_history.append(
                    {"role": "assistant", "content": initial_greeting}
                )
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
                
                # Fetch Question 1
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
                # 1. LISTENING STAGE
                self.update_status("Listening to your response...")
                turn_start_sec = self.session_logger.elapsed_sec() if self.session_logger else 0.0
                user_transcript = listen_and_transcribe(ui_callback=self.update_audio_diagnostics, mic_writer=self.mic_writer)
                turn_end_sec = self.session_logger.elapsed_sec() if self.session_logger else 0.0
                silence_gap_sec = max(0.0, turn_start_sec - self.last_eva_speech_end_sec)

                if not user_transcript.strip() or not self.is_running:
                    continue

                clean_transcript = user_transcript.strip()

                if self.llm_enabled:
                    # Standard operation:
                    self.log_and_display_turn("You", f"{clean_transcript} [Paper Rustling]")
                    self.conversation_history.append(
                        {"role": "user", "content": clean_transcript}
                    )

                    # 2. GENERATION & THINKING STAGE
                    self.update_status("Eva is evaluating...")
                    Benchmark.start("ttft")
                    brain_generator = generate_eva_response(self.conversation_history)

                    # 3. TEXT-TO-SPEECH STREAMING STAGE
                    full_eva_reply = ""
                    sentence_buffer = ""
                    ttft_logged = False
                    ttfa_logged = False
                    current_ttft = 0.0
                    current_ttfa = 0.0

                    for token in brain_generator:
                        if not self.is_running:
                            break

                        if not ttft_logged:
                            current_ttft = Benchmark.end("ttft")
                            ttft_logged = True

                        full_eva_reply += token
                        sentence_buffer += token

                        # Advanced regex splitting for streaming sentence chunks
                        sentences = re.split(r'(?<=[.!?\n])\s+', sentence_buffer)
                        if len(sentences) > 1:
                            new_buffer = []
                            for sentence in sentences[:-1]:
                                sentence = sentence.strip()
                                if len(sentence) > 15 and not any(sentence.lower().endswith(abbr) for abbr in ["mr.", "dr.", "ms.", "mrs.", "prof.", "e.g.", "i.e.", "vs."]):
                                    self.update_status(f"Eva is speaking... (Q {self.question_count + 1}/{self.MAX_QUESTIONS})")
                                    if not ttfa_logged:
                                        current_ttfa = Benchmark.end("ttfa")
                                        ttfa_logged = True
                                    speak_text(sentence)
                                else:
                                    # It's an abbreviation or too short, keep it in the buffer
                                    new_buffer.append(sentence)
                            
                            new_buffer.append(sentences[-1])
                            sentence_buffer = " ".join(new_buffer)

                    # Flush any leftover tokens in the buffer
                    if sentence_buffer.strip() and self.is_running:
                        if not ttfa_logged:
                            current_ttfa = Benchmark.end("ttfa")
                            ttfa_logged = True
                        speak_text(sentence_buffer.strip())

                    if self.session_logger:
                        self.last_eva_speech_end_sec = self.session_logger.elapsed_sec()

                    # Append whole historical log context block to state history matrix
                    self.log_and_display_turn("Eva", full_eva_reply)
                    self.conversation_history.append(
                        {"role": "assistant", "content": full_eva_reply}
                    )

                    # Log metrics to CSV
                    stt_ms = getattr(Benchmark, "last_stt_ms", 0.0)
                    if ttft_logged and ttfa_logged:
                        Benchmark.log_metrics(stt_ms, current_ttft, current_ttfa)

                    # Log manifest turn entry
                    if self.session_logger:
                        self.session_logger.log_turn(
                            turn_id=self.question_count,
                            topic="Frontend Engineering",
                            question_text=self.current_question_text,
                            candidate_transcript=clean_transcript,
                            audio_start_sec=turn_start_sec,
                            audio_end_sec=turn_end_sec,
                            silence_duration_before_answer_sec=silence_gap_sec,
                            stt_latency_ms=stt_ms,
                            ttft_ms=current_ttft
                        )
                    # Prepare question text for next turn log
                    self.current_question_text = full_eva_reply

                    self.question_count += 1
                    self.update_question_label(self.question_count)

                    # Auto-close check after Q15 response has been completed and spoken
                    if self.question_count >= self.MAX_QUESTIONS:
                        self.update_status("Interview Complete — 15/15 Questions Done")
                        self.append_ui_text("\n[System]: Interview completed (15/15). Stopping session...")
                        self.stop_interview()
                        break
                else:
                    # Calibration mode:
                    # We evaluate the user transcript against the expected answer
                    q_data = self.current_track_data[self.question_count]
                    expected_answer = q_data['answer']

                    # Word-by-word matching
                    spoken_clean = clean_transcript.lower().strip().replace(".", "").replace(",", "")
                    expected_clean = expected_answer.lower().strip().replace(".", "").replace(",", "")
                    accuracy = difflib.SequenceMatcher(None, expected_clean.split(), spoken_clean.split()).ratio() * 100

                    self.log_and_display_turn("You", f"{clean_transcript}")
                    self.log_and_display_turn("System", f"[Accuracy Check] Match Score: {accuracy:.2f}%")

                    self.question_count += 1

                    if self.question_count < len(self.current_track_data):
                        # Show next question target details on UI
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
                                ttft_ms=0.0
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
                                ttft_ms=0.0
                            )
                        self.update_status("Calibration Complete!")
                        self.append_ui_text("\n[System]: Calibration complete! Final match analytics calculated.")
                        Clock.schedule_once(lambda dt: self._update_script_display())
                        self.stop_interview()
                        break
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.update_status(f"Pipeline Error: {str(e)}")


class AIInterviewerApp(App):

    def build(self):
        Builder.load_string(KV)
        return InterviewWindow()


if __name__ == "__main__":
    # Run the application
    AIInterviewerApp().run()