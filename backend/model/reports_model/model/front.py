"""
Netran AI — Stage 4: Post-Session Multimodal Evaluation & Report Generation Engine
Module: front.py
Description: Interactive Kivy desktop application for testing Stage 4 multimodal report generation.
"""

import sys
import threading
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parents[3]
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView

# Set window dimensions
Window.size = (950, 700)

from model.reports_model.model.report_builder import build_report
from model.reports_model.model.report_schema import CandidateReportPayload


class ReportEngineApp(App):
    def build(self):
        self.title = "Netran AI — Stage 4 Multimodal Evaluation Engine"
        
        # Locate target session directory dynamically
        target_dir = backend_dir / "model" / "reports_model" / "test" / "input" / "sample_session"
        
        if not target_dir.exists():
            v2v_out_dir = backend_dir / "model" / "voice_to_voice_model" / "test" / "output"
            if v2v_out_dir.exists():
                existing = [d for d in v2v_out_dir.iterdir() if d.is_dir()]
                if existing:
                    existing.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                    target_dir = existing[0]

        self.session_dir = target_dir

        # Main Root Layout
        root = BoxLayout(orientation="vertical", padding=15, spacing=12)

        # Header
        header = BoxLayout(orientation="vertical", size_hint_y=None, height=60, spacing=4)
        title_label = Label(
            text="[b]Netran AI (SAMWINI) — Report Engine Test Desk[/b]",
            markup=True,
            font_size="20sp",
            color=(0.12, 0.53, 0.90, 1)
        )
        session_label = Label(
            text=f"Target Session: {self.session_dir.name}",
            font_size="13sp",
            color=(0.6, 0.6, 0.6, 1)
        )
        header.add_widget(title_label)
        header.add_widget(session_label)
        root.add_widget(header)

        # Controls Section
        controls = BoxLayout(orientation="horizontal", size_hint_y=None, height=45, spacing=10)
        self.btn_run = Button(
            text="▶  Run Report Pipeline (Gemini Multimodal)",
            background_color=(0.12, 0.53, 0.90, 1),
            font_size="14sp",
            bold=True
        )
        self.btn_run.bind(on_press=self.start_pipeline_thread)
        controls.add_widget(self.btn_run)
        root.add_widget(controls)

        # Content Split Layout (Log Panel | Report Panel)
        content_split = BoxLayout(orientation="horizontal", spacing=12)

        # Left Panel: Live Execution Log
        log_box = BoxLayout(orientation="vertical", spacing=5)
        log_title = Label(
            text="[b]Pipeline Execution Telemetry Log[/b]",
            markup=True,
            size_hint_y=None,
            height=25,
            color=(0.8, 0.8, 0.8, 1),
            halign="left"
        )
        log_box.add_widget(log_title)

        self.log_label = Label(
            text="Ready. Click 'Run Report Pipeline' to start testing.",
            markup=True,
            font_size="12sp",
            size_hint_y=None,
            color=(0.2, 0.9, 0.3, 1),
            halign="left",
            valign="top"
        )
        self.log_label.bind(texture_size=self._update_log_height)
        
        log_scroll = ScrollView(bar_width=6)
        log_scroll.add_widget(self.log_label)
        log_box.add_widget(log_scroll)
        content_split.add_widget(log_box)

        # Right Panel: Synthesized Report Display Card
        report_box = BoxLayout(orientation="vertical", spacing=5)
        report_title = Label(
            text="[b]Synthesized Evaluation Artifact Preview[/b]",
            markup=True,
            size_hint_y=None,
            height=25,
            color=(0.8, 0.8, 0.8, 1),
            halign="left"
        )
        report_box.add_widget(report_title)

        self.report_label = Label(
            text="No evaluation report generated yet.",
            markup=True,
            font_size="13sp",
            size_hint_y=None,
            color=(0.9, 0.9, 0.9, 1),
            halign="left",
            valign="top"
        )
        self.report_label.bind(texture_size=self._update_report_height)

        report_scroll = ScrollView(bar_width=6)
        report_scroll.add_widget(self.report_label)
        report_box.add_widget(report_scroll)
        content_split.add_widget(report_box)

        root.add_widget(content_split)
        return root

    def _update_log_height(self, instance, size):
        instance.height = size[1]
        instance.text_size = (instance.width, None)

    def _update_report_height(self, instance, size):
        instance.height = size[1]
        instance.text_size = (instance.width, None)

    def append_log(self, text: str):
        def _update(dt):
            self.log_label.text += f"\n> {text}"
        Clock.schedule_once(_update)

    def start_pipeline_thread(self, instance):
        self.btn_run.disabled = True
        self.log_label.text = "> Initiating Stage 4 Evaluation Pipeline..."
        self.report_label.text = "Synthesizing report via Gemini..."

        threading.Thread(target=self.run_pipeline_background, daemon=True).start()

    def run_pipeline_background(self):
        try:
            self.append_log("Parsing session manifest and audio recording...")
            self.append_log("Slicing continuous audio into per-turn WAV clips...")
            
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            out_session_dir = backend_dir / "model" / "reports_model" / "test" / "output" / f"sess_{timestamp}"

            report: CandidateReportPayload = build_report(
                session_dir=self.session_dir,
                model_name="gemini-3.6-flash",
                output_dir=out_session_dir
            )

            self.append_log("Gemini Multimodal Audio Branch: COMPLETED ✓")
            self.append_log("Gemini Technical Evaluation Branch: COMPLETED ✓")
            self.append_log("Fused Combine Synthesis Branch: COMPLETED ✓")
            self.append_log(f"Saved artifacts to {out_session_dir.name}: report.json & evaluation_summary.md ✓")

            # Update UI on main thread
            Clock.schedule_once(lambda dt: self.display_report(report))

        except Exception as e:
            err_msg = str(e)
            self.append_log(f"[ERROR] Pipeline Failed: {err_msg}")
            Clock.schedule_once(lambda dt: self._show_error(err_msg))

        finally:
            Clock.schedule_once(lambda dt: setattr(self.btn_run, 'disabled', False))

    def display_report(self, report: CandidateReportPayload):
        signal_color = "00FF00" if "Hire" in report.overall_hiring_signal else "FF5555"
        
        lines = []
        lines.append(f"[b]Session ID:[/b] {report.session_id}")
        lines.append(f"[b]Hiring Signal:[/b] [{color_tag(signal_color)}]{report.overall_hiring_signal}[/color]")
        lines.append(f"[b]Overall Technical Score:[/b] {report.overall_technical_score} / 100")
        lines.append(f"[b]Vocal Confidence Score:[/b] {report.overall_vocal_confidence_score} / 100\n")
        
        lines.append("[b]Executive Summary:[/b]")
        lines.append(f"{report.executive_summary}\n")

        lines.append("[b]Core Technical Pillars:[/b]")
        for pillar in report.technical_pillars:
            lines.append(f"• [b]{pillar.pillar_name}[/b] ({pillar.score}/100): {pillar.summary}")

        lines.append("\n[b]Turn Evaluations:[/b]")
        for turn in report.turn_evaluations:
            lines.append(f"[b]Turn {turn.turn_id}:[/b] {turn.question_text}")
            lines.append(f"  [i]Original Transcript:[/i] \"{turn.candidate_transcript}\"")
            lines.append(f"  [i]Gemini Verified:[/i] \"{turn.gemini_verified_transcript}\"")
            lines.append(f"  Technical: {turn.technical_score}/10 | Vocal Confidence: {turn.vocal_confidence_score}/10")
            lines.append(f"  Emotion: {turn.emotional_state} | Hesitation: {turn.hesitation_level} | Fillers: {turn.filler_word_count}")
            lines.append(f"  Audio Notes: {turn.audio_notes}")
            if turn.missing_concepts:
                lines.append(f"  Missing Concepts: {', '.join(turn.missing_concepts)}")

        self.report_label.text = "\n".join(lines)

    def _show_error(self, err_msg: str):
        self.report_label.text = f"[color=FF3333][b]Error during report generation:[/b]\n{err_msg}[/color]"


def color_tag(hex_code: str) -> str:
    return f"color={hex_code}"


if __name__ == "__main__":
    ReportEngineApp().run()
