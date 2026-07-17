import threading
import time
from datetime import datetime
from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout

# Import the functional blocks we created in this exact folder
from brain import generate_eva_response
from listener import listen_and_transcribe
from speaker import speak_text

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

    ScrollView:
        size_hint_y: 0.7
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

    def start_interview(self):
        self.ids.start_btn.disabled = True
        self.ids.stop_btn.disabled = False
        self.is_running = True
        self.conversation_history = []

        # Write clean session start to log file
        with open(self.log_filename, "w", encoding="utf-8") as f:
            f.write(
                f"=== AI INTERVIEW LOG: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n\n"
            )

        self.update_status("Eva is initializing speech channels...")
        self.append_ui_text("\n[System]: Voice pipeline connected.\n")

        # Start processing inside background thread
        self.interview_thread = threading.Thread(
            target=self._run_interview_pipeline, daemon=True
        )
        self.interview_thread.start()

    def stop_interview(self):
        self.is_running = False
        self.ids.start_btn.disabled = False
        self.ids.stop_btn.disabled = True
        self.update_status("Interview Stopped.")
        self.append_ui_text("\n[System]: Log file finalized successfully.")

    def update_status(self, text):
        Clock.schedule_once(lambda dt: setattr(self.ids.status_label, "text", text))

    def append_ui_text(self, text):
        def _update(dt):
            self.ids.transcript_display.text += f"{text}\n"

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
            # --- TURN 1: EVA INITIATES CONVERSATION ---
            initial_greeting = "Hello! Welcome to your technical interview today. [Clears Throat] Could you please start by describing your core frontend stack?"
            self.log_and_display_turn("Eva", initial_greeting)
            self.conversation_history.append(
                {"role": "assistant", "content": initial_greeting}
            )

            self.update_status("Eva is speaking...")
            speak_text(initial_greeting)

            # --- MAIN CYCLE LOOP ---
            while self.is_running:
                # 1. LISTENING STAGE
                self.update_status("Listening to your response...")
                user_transcript = listen_and_transcribe()

                if not user_transcript.strip() or not self.is_running:
                    continue

                # Add a realistic environment noise token to the user output text log
                user_text_with_noise = f"{user_transcript} [Paper Rustling]"
                self.log_and_display_turn("You", user_text_with_noise)
                self.conversation_history.append(
                    {"role": "user", "content": user_text_with_noise}
                )

                # 2. GENERATION & THINKING STAGE
                self.update_status("Eva is evaluating...")
                brain_generator = generate_eva_response(self.conversation_history)

                # 3. TEXT-TO-SPEECH STREAMING STAGE
                full_eva_reply = ""
                sentence_buffer = ""

                for token in brain_generator:
                    if not self.is_running:
                        break

                    full_eva_reply += token
                    sentence_buffer += token

                    # Sentence boundaries checking[cite: 1]
                    if token in [".", "!", "?", "\n"] and len(sentence_buffer) > 12:
                        self.update_status("Eva is speaking...")
                        # Run native hardware speech output on the collected sentence frame
                        speak_text(sentence_buffer)
                        sentence_buffer = ""

                # Flush any left over tokens in the buffer
                if sentence_buffer.strip() and self.is_running:
                    speak_text(sentence_buffer)

                # Append whole historical log context block to state history matrix
                self.log_and_display_turn("Eva", full_eva_reply)
                self.conversation_history.append(
                    {"role": "assistant", "content": full_eva_reply}
                )

        except Exception as e:
            self.update_status(f"Pipeline Error: {str(e)}")


class AIInterviewerApp(App):

    def build(self):
        Builder.load_string(KV)
        return InterviewWindow()


if __name__ == "__main__":
    # Run the application
    AIInterviewerApp().run()