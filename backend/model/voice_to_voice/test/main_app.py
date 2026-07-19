import threading
import time
import re
from datetime import datetime
from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout

# Import the functional blocks we created in this exact folder
from brain import generate_eva_response, preload as preload_brain
from listener import listen_and_transcribe
from speaker import speak_text, preload_models as preload_speaker

# Clean visual layout utilizing a modern dark visual palette
KV = """
<InterviewWindow>:
    orientation: 'vertical'
    padding: 20
    spacing: 15
    canvas.before:
        Color:
            rgba: 0.1, 0.1, 0.12, 1
        Rectangle:
            pos: self.pos
            size: self.size

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
            id: stop_btn
            text: "Stop & Save Log"
            background_normal: ''
            background_color: 0.8, 0.3, 0.3, 1
            disabled: True
            on_press: root.stop_interview()
"""


class InterviewWindow(BoxLayout):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.is_running = False
        self.interview_thread = None
        self.log_filename = "interview_log.txt"
        self.conversation_history = []
        self.question_count = 0
        self.MAX_QUESTIONS = 15

    def _reset_buttons(self):
        self.ids.start_btn.disabled = False
        self.ids.stop_btn.disabled = True

    def update_question_label(self, count):
        Clock.schedule_once(lambda dt: setattr(self.ids.question_label, "text", f"Question: {count} / {self.MAX_QUESTIONS}"))

    def start_interview(self):
        self.ids.start_btn.disabled = True
        self.ids.stop_btn.disabled = False
        self.is_running = True
        self.conversation_history = []
        self.question_count = 0
        self.update_question_label(0)

        # Write clean session start to log file
        with open(self.log_filename, "w", encoding="utf-8") as f:
            f.write(
                f"=== AI INTERVIEW LOG: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n\n"
            )

        self.update_status("Initializing AI Models... (Please wait)")
        self.append_ui_text("\n[System]: Pre-heating AI pipelines...\n")

        # Start processing inside background thread
        self.interview_thread = threading.Thread(
            target=self._run_interview_pipeline, daemon=True
        )
        self.interview_thread.start()

    def stop_interview(self):
        self.is_running = False
        Clock.schedule_once(lambda dt: self._reset_buttons())
        self.update_status("Interview Stopped.")
        self.append_ui_text("\n[System]: Log file finalized successfully.")

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
            preload_brain()
            self.update_status("Eva is initializing speech channels...")
            self.append_ui_text("[System]: Voice pipeline connected.\n")

            # --- TURN 1: EVA INITIATES CONVERSATION ---
            initial_greeting = "Hello! Welcome to your technical interview today. [Clears Throat] Could you please start by describing your core frontend stack?"
            self.log_and_display_turn("Eva", initial_greeting)
            self.conversation_history.append(
                {"role": "assistant", "content": initial_greeting}
            )
            self.question_count = 1
            self.update_question_label(self.question_count)

            self.update_status("Eva is speaking...")
            speak_text(initial_greeting)

            # --- MAIN CYCLE LOOP ---
            while self.is_running:
                # 1. LISTENING STAGE
                self.update_status("Listening to your response...")
                user_transcript = listen_and_transcribe(ui_callback=self.update_audio_diagnostics)

                if not user_transcript.strip() or not self.is_running:
                    continue

                # Add a realistic environment noise token to the user output text log,
                # but append clean transcript to LLM conversation history to avoid prompt corruption.
                clean_transcript = user_transcript.strip()
                self.log_and_display_turn("You", f"{clean_transcript} [Paper Rustling]")
                self.conversation_history.append(
                    {"role": "user", "content": clean_transcript}
                )

                # 2. GENERATION & THINKING STAGE
                self.update_status("Eva is evaluating...")
                from benchmark import Benchmark
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

                # Append whole historical log context block to state history matrix
                self.log_and_display_turn("Eva", full_eva_reply)
                self.conversation_history.append(
                    {"role": "assistant", "content": full_eva_reply}
                )

                # Log metrics to CSV
                stt_ms = getattr(Benchmark, "last_stt_ms", 0.0)
                if ttft_logged and ttfa_logged:
                    Benchmark.log_metrics(stt_ms, current_ttft, current_ttfa)

                self.question_count += 1
                self.update_question_label(self.question_count)

                # Auto-close check after Q15 response has been completed and spoken
                if self.question_count >= self.MAX_QUESTIONS:
                    self.update_status("Interview Complete — 15/15 Questions Done")
                    self.append_ui_text("\n[System]: Interview completed (15/15). Stopping session...")
                    self.stop_interview()
                    break

        except Exception as e:
            self.update_status(f"Pipeline Error: {str(e)}")


class AIInterviewerApp(App):

    def build(self):
        Builder.load_string(KV)
        return InterviewWindow()


if __name__ == "__main__":
    # Run the application
    AIInterviewerApp().run()