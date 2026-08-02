"""
Netran AI — Stage 4: Post-Session Multimodal Evaluation & Report Generation Engine
Module: front.py
Description: Interactive Kivy desktop GUI application for testing Stage 4 multimodal report generation,
             featuring rich dark-theme aesthetics, interactive session picker, output artifact selector,
             and clean visual markup rendering.
"""

import json
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
from kivy.graphics import Color, RoundedRectangle
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner

# Set modern dark Window background & dimensions
Window.clearcolor = (0.07, 0.09, 0.15, 1)  # #121726 Deep Slate Dark
Window.size = (1180, 820)

try:
    from model.reports_model.model.pipeline import (
        Stage4Pipeline,
        render_markdown_report,
    )
    from model.reports_model.model.schemas import CandidateReportPayload
except ImportError:
    from pipeline import Stage4Pipeline
    from schemas import CandidateReportPayload


class CardBoxLayout(BoxLayout):
    """Custom BoxLayout with rounded dark card background for modern UI aesthetics."""
    def __init__(self, bg_color=(0.11, 0.14, 0.22, 1), radius=8, **kwargs):
        super().__init__(**kwargs)
        self.bg_color = bg_color
        self.radius = radius
        with self.canvas.before:
            Color(*self.bg_color)
            self.rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[self.radius])
        self.bind(pos=self._update_rect, size=self._update_rect)

    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size


class ReportEngineApp(App):
    def build(self):
        self.title = "Netran AI — Stage 4 Multimodal Evaluation Suite"
        self.input_sessions_map = {}
        self.output_sessions_map = {}
        self.session_dir = None

        # Scan input test sessions & generated output artifacts
        self._scan_available_input_sessions()
        self._scan_available_output_artifacts()

        # Root Layout
        root = BoxLayout(orientation="vertical", padding=16, spacing=12)

        # ---------------------------------------------------------------------
        # 1. HEADER SECTION
        # ---------------------------------------------------------------------
        header_card = CardBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=65,
            padding=[16, 8],
            spacing=10,
            bg_color=(0.13, 0.17, 0.28, 1)
        )

        header_text_box = BoxLayout(orientation="vertical", spacing=2)
        title_label = Label(
            text="[b]Netran AI[/b] — Stage 4 Multimodal Report Engine",
            markup=True,
            font_size="19sp",
            color=(0.22, 0.74, 0.97, 1),  # #38BDF8 Sky Cyan
            halign="left",
            valign="middle"
        )
        title_label.bind(size=title_label.setter('text_size'))

        subtitle_label = Label(
            text="Acoustic Speech Tone Analysis & Technical Depth Synthesis Test Harness",
            font_size="12sp",
            color=(0.6, 0.65, 0.75, 1),
            halign="left",
            valign="middle"
        )
        subtitle_label.bind(size=subtitle_label.setter('text_size'))

        header_text_box.add_widget(title_label)
        header_text_box.add_widget(subtitle_label)
        header_card.add_widget(header_text_box)
        root.add_widget(header_card)

        # ---------------------------------------------------------------------
        # 2. CONTROLS BAR (Input Picker & Pipeline Trigger)
        # ---------------------------------------------------------------------
        input_controls_card = CardBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=50,
            padding=[12, 6],
            spacing=10,
            bg_color=(0.10, 0.13, 0.20, 1)
        )

        # Input Session Spinner Dropdown
        input_spinner_values = list(self.input_sessions_map.keys()) if self.input_sessions_map else ["No Inputs Found"]
        default_input = input_spinner_values[0] if input_spinner_values else ""
        
        input_label = Label(
            text="[b]Input Session:[/b]",
            markup=True,
            font_size="12sp",
            size_hint_x=None,
            width=100,
            color=(0.85, 0.88, 0.95, 1)
        )
        
        self.input_spinner = Spinner(
            text=default_input,
            values=input_spinner_values,
            size_hint_x=0.35,
            background_color=(0.16, 0.22, 0.35, 1),
            color=(1, 1, 1, 1),
            font_size="12sp",
            bold=True
        )
        self.input_spinner.bind(text=self._on_input_session_changed)

        # Context Indicator Label
        self.context_label = Label(
            text="",
            markup=True,
            font_size="12sp",
            size_hint_x=0.35,
            color=(0.7, 0.75, 0.85, 1)
        )

        # Run Button
        self.btn_run = Button(
            text="▶  Run Evaluation",
            size_hint_x=0.30,
            background_color=(0.05, 0.65, 0.90, 1), # #0EA5E9 Vibrant Cyan
            font_size="12sp",
            bold=True
        )
        self.btn_run.bind(on_press=self.start_pipeline_thread)

        input_controls_card.add_widget(input_label)
        input_controls_card.add_widget(self.input_spinner)
        input_controls_card.add_widget(self.context_label)
        input_controls_card.add_widget(self.btn_run)
        root.add_widget(input_controls_card)

        # ---------------------------------------------------------------------
        # 3. PAST OUTPUT ARTIFACT SELECTOR BAR
        # ---------------------------------------------------------------------
        output_controls_card = CardBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=50,
            padding=[12, 6],
            spacing=10,
            bg_color=(0.12, 0.15, 0.25, 1)
        )

        output_label = Label(
            text="[b]Past Outputs:[/b]",
            markup=True,
            font_size="12sp",
            size_hint_x=None,
            width=100,
            color=(0.85, 0.88, 0.95, 1)
        )

        output_spinner_values = list(self.output_sessions_map.keys()) if self.output_sessions_map else ["No Saved Outputs"]
        default_output = output_spinner_values[0] if output_spinner_values else ""

        self.output_spinner = Spinner(
            text="Select Saved Output...",
            values=output_spinner_values,
            size_hint_x=0.60,
            background_color=(0.20, 0.26, 0.40, 1),
            color=(1, 1, 1, 1),
            font_size="12sp",
            bold=True
        )
        self.output_spinner.bind(text=self._on_output_artifact_selected)

        self.btn_refresh_outputs = Button(
            text="🔄 Refresh",
            size_hint_x=0.20,
            background_color=(0.25, 0.32, 0.48, 1),
            font_size="12sp",
            bold=True
        )
        self.btn_refresh_outputs.bind(on_press=lambda inst: self._scan_available_output_artifacts())

        output_controls_card.add_widget(output_label)
        output_controls_card.add_widget(self.output_spinner)
        output_controls_card.add_widget(self.btn_refresh_outputs)
        root.add_widget(output_controls_card)

        # Trigger initial selection state
        if default_input:
            self._on_input_session_changed(self.input_spinner, default_input)

        # ---------------------------------------------------------------------
        # 4. CONTENT SPLIT PANELS (Telemetry Log | Synthesized Report)
        # ---------------------------------------------------------------------
        content_split = BoxLayout(orientation="horizontal", spacing=14)

        # Left Panel: Telemetry Execution Log Card
        log_card = CardBoxLayout(
            orientation="vertical",
            padding=[12, 12],
            spacing=8,
            bg_color=(0.09, 0.11, 0.17, 1)
        )
        log_header = Label(
            text="[b][color=38BDF8]>>[/color] Pipeline Execution Telemetry Log[/b]",
            markup=True,
            size_hint_y=None,
            height=26,
            font_size="13sp",
            color=(0.34, 0.75, 0.95, 1),
            halign="left"
        )
        log_header.bind(size=log_header.setter('text_size'))
        log_card.add_widget(log_header)

        self.log_label = Label(
            text="System Ready. Select an input session and click 'Run Evaluation' or choose a past output from the dropdown above.",
            markup=True,
            font_size="12sp",
            size_hint_y=None,
            color=(0.4, 0.85, 0.5, 1),
            halign="left",
            valign="top"
        )
        self.log_label.bind(texture_size=self._update_log_height)
        
        log_scroll = ScrollView(bar_width=6)
        log_scroll.add_widget(self.log_label)
        log_card.add_widget(log_scroll)
        content_split.add_widget(log_card)

        # Right Panel: Report Artifact Display Card
        report_card = CardBoxLayout(
            orientation="vertical",
            padding=[14, 12],
            spacing=8,
            bg_color=(0.09, 0.11, 0.17, 1)
        )
        report_header = Label(
            text="[b][color=38BDF8]>>[/color] Executive Candidate Assessment Report[/b]",
            markup=True,
            size_hint_y=None,
            height=26,
            font_size="13sp",
            color=(0.34, 0.75, 0.95, 1),
            halign="left"
        )
        report_header.bind(size=report_header.setter('text_size'))
        report_card.add_widget(report_header)

        self.report_label = Label(
            text="Select an input session to run evaluation or choose a past output from the dropdown above.",
            markup=True,
            font_size="13sp",
            size_hint_y=None,
            color=(0.85, 0.88, 0.95, 1),
            halign="left",
            valign="top"
        )
        self.report_label.bind(texture_size=self._update_report_height)

        report_scroll = ScrollView(bar_width=6)
        report_scroll.add_widget(self.report_label)
        report_card.add_widget(report_scroll)
        content_split.add_widget(report_card)

        root.add_widget(content_split)
        return root

    def _scan_available_input_sessions(self):
        """Discovers all valid test sessions in test/input/ and stage3 outputs."""
        self.input_sessions_map.clear()

        # 1. Preset test input sessions
        base_input_dir = backend_dir / "model" / "reports_model" / "test" / "input"
        if base_input_dir.exists():
            for d in base_input_dir.iterdir():
                if d.is_dir():
                    self.input_sessions_map[f"{d.name}  [test/input]"] = d

        # 2. Stage 3 Voice-to-Voice output sessions
        v2v_out_dir = backend_dir / "model" / "voice_to_voice_model" / "test" / "output"
        if v2v_out_dir.exists():
            for d in v2v_out_dir.iterdir():
                if d.is_dir():
                    self.input_sessions_map[f"{d.name}  [stage3/output]"] = d

    def _scan_available_output_artifacts(self):
        """Discovers all generated report output directories in test/output/."""
        self.output_sessions_map.clear()
        out_dir = backend_dir / "model" / "reports_model" / "test" / "output"

        if out_dir.exists():
            sessions = [d for d in out_dir.iterdir() if d.is_dir() and (d / "report.json").exists()]
            sessions.sort(key=lambda x: x.stat().st_mtime, reverse=True)

            for d in sessions:
                # Format friendly display label
                mod_time = d.stat().st_mtime
                import datetime
                time_str = datetime.datetime.fromtimestamp(mod_time).strftime("%Y-%m-%d %H:%M:%S")
                label = f"{d.name}  ({time_str})"
                self.output_sessions_map[label] = d

        # Update output spinner values if widget initialized
        if hasattr(self, "output_spinner"):
            values = list(self.output_sessions_map.keys()) if self.output_sessions_map else ["No Saved Outputs"]
            self.output_spinner.values = values

    def _on_input_session_changed(self, spinner, text):
        """Updates active input session directory and context status labels when selection changes."""
        if not text or text not in self.input_sessions_map:
            return

        self.session_dir = self.input_sessions_map[text]
        has_resume = (self.session_dir / "sample_resume.txt").exists() or (self.session_dir / "sample_resume.json").exists() or (self.session_dir / "resume.txt").exists()
        has_rubric = (self.session_dir / "sample_rubric.json").exists() or (self.session_dir / "sample_job_detail.json").exists() or (self.session_dir / "stage1_rubric.json").exists()

        res_str = "[color=00FF66]Resume ✓[/color]" if has_resume else "[color=FF6666]Resume ✗[/color]"
        rub_str = "[color=00FF66]Rubric ✓[/color]" if has_rubric else "[color=FF6666]Rubric ✗[/color]"
        self.context_label.text = f"Context: {res_str}  |  {rub_str}"

    def _on_output_artifact_selected(self, spinner, text):
        """Loads and renders the selected past output report artifact."""
        if not text or text not in self.output_sessions_map:
            return

        target_dir = self.output_sessions_map[text]
        json_path = target_dir / "report.json"

        try:
            with open(json_path, "r", encoding="utf-8") as f:
                report_data = json.load(f)

            report = CandidateReportPayload.model_validate(report_data)
            self.log_label.text = f"> [Loaded Artifact] Displaying past output session:\n  {target_dir.name}"
            self.display_report(report)
        except Exception as e:
            self._show_error(f"Failed to parse report artifact at {target_dir.name}: {e}")

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
        if not self.session_dir or not self.session_dir.exists():
            self._show_error("Selected session directory does not exist.")
            return

        self.btn_run.disabled = True
        self.log_label.text = f"> Initiating Stage 4 Evaluation for {self.session_dir.name}..."
        self.report_label.text = "[color=38BDF8]Synthesizing executive evaluation report via Gemini API...[/color]"

        threading.Thread(target=self.run_pipeline_background, daemon=True).start()

    def run_pipeline_background(self):
        try:
            self.append_log("Reading session manifest and grounding context files...")
            self.append_log("Slicing continuous audio into per-turn WAV clips...")

            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            out_session_dir = backend_dir / "model" / "reports_model" / "test" / "output" / f"sess_{timestamp}"

            pipeline = Stage4Pipeline()
            report: CandidateReportPayload = pipeline.run(
                session_dir=self.session_dir,
                model_name="gemini-3.6-flash",
                output_dir=out_session_dir
            )

            self.append_log("Gemini Multimodal Audio Branch: COMPLETED ✓")
            self.append_log("Gemini Technical Evaluation Branch: COMPLETED ✓")
            self.append_log("Fused Combine Synthesis Branch: COMPLETED ✓")
            self.append_log(f"Saved artifacts to {out_session_dir.name}: report.json & evaluation_summary.md ✓")

            # Refresh output list on main thread & display
            Clock.schedule_once(lambda dt: self._scan_available_output_artifacts())
            Clock.schedule_once(lambda dt: self.display_report(report))

        except Exception as e:
            err_msg = str(e)
            self.append_log(f"[ERROR] Pipeline Failed: {err_msg}")
            Clock.schedule_once(lambda dt: self._show_error(err_msg))

        finally:
            Clock.schedule_once(lambda dt: setattr(self.btn_run, 'disabled', False))

    def display_report(self, report: CandidateReportPayload):
        signal_color = "00FF66" if "Hire" in report.overall_hiring_signal and "No" not in report.overall_hiring_signal else "FF4444"

        lines = []
        lines.append(f"[b]Session ID:[/b] {report.session_id}")
        lines.append(f"[b]Generated At:[/b] {report.generated_at}")
        lines.append(f"[b]Hiring Signal:[/b] [{color_tag(signal_color)}]{report.overall_hiring_signal.upper()}[/color]")
        lines.append(f"[b]Overall Technical Score:[/b] {report.overall_technical_score} / 100")
        lines.append(f"[b]Vocal Delivery & Confidence:[/b] {report.overall_vocal_confidence_score} / 100\n")

        lines.append("[b]Executive Summary:[/b]")
        lines.append(f"{report.executive_summary}\n")

        # Behavioral Red Flags Section (Clean Kivy Markup formatting)
        if report.behavioral_flags:
            lines.append("[b][color=FF4444]!! Integrity & Behavioral Red Flags:[/color][/b]")
            for flag in report.behavioral_flags:
                sev_color = "FF4444" if flag.severity in ["CRITICAL", "HIGH"] else "F59E0B"
                lines.append(f"  • [[color={sev_color}]{flag.severity}[/color]] Turn #{flag.turn_id} — {flag.type}: {flag.description}")
            lines.append("")

        # Candidate Growth Roadmap Section
        if report.candidate_feedback:
            lines.append("[b][color=38BDF8]>> Candidate Growth & Upskilling Roadmap:[/color][/b]")
            if report.candidate_feedback.key_strengths:
                lines.append("  [b][color=00FF66]Key Strengths:[/color][/b]")
                for s in report.candidate_feedback.key_strengths:
                    lines.append(f"   • {s}")
            if report.candidate_feedback.primary_growth_areas:
                lines.append("  [b][color=F59E0B]Primary Growth Areas:[/color][/b]")
                for g in report.candidate_feedback.primary_growth_areas:
                    lines.append(f"   • {g}")
            if report.candidate_feedback.recommended_topics_to_study:
                lines.append("  [b][color=38BDF8]Recommended Study Topics:[/color][/b]")
                for t in report.candidate_feedback.recommended_topics_to_study:
                    lines.append(f"   • {t}")
            lines.append("")

        # Technical Pillars Section
        lines.append("[b][color=818CF8]> Core Technical Pillars:[/color][/b]")
        for pillar in report.technical_pillars:
            lines.append(f"  • [b]{pillar.pillar_name}[/b] ({pillar.score}/100): {pillar.summary}")

        # Turn Evaluations
        lines.append("\n[b][color=38BDF8]>> Detailed Turn-by-Turn Analysis:[/color][/b]")
        for turn in report.turn_evaluations:
            lines.append(f"\n[b]Turn #{turn.turn_id}:[/b] {turn.question_text}")
            lines.append(f"  [i]Original Transcript:[/i] \"{turn.candidate_transcript}\"")
            lines.append(f"  [i]Gemini Verified:[/i] \"{turn.gemini_verified_transcript}\"")
            
            if getattr(turn, "telemetry", None):
                t = turn.telemetry
                halluc_str = "[color=FF4444]DISCREPANCY DETECTED[/color]" if t.stt_whisper_hallucination_flag else "[color=00FF66]Normal[/color]"
                lines.append(f"  [b]Telemetry:[/b] Latency: {t.initial_silence_latency_ms}ms | Duration: {t.turn_duration_sec}s | STT Discrepancy: {halluc_str}")
            
            lines.append(f"  Technical Score: {turn.technical_score}/10 | Vocal Confidence: {turn.vocal_confidence_score}/10")
            lines.append(f"  Emotion: {turn.emotional_state} | Hesitation: {turn.hesitation_level} | Fillers: {turn.filler_word_count}")
            lines.append(f"  Audio Delivery Notes: {turn.audio_notes}")
            if turn.missing_concepts:
                lines.append(f"  Missing Concepts: {', '.join(turn.missing_concepts)}")
            if getattr(turn, "resume_verification_note", None):
                lines.append(f"  Resume Check: {turn.resume_verification_note}")

        self.report_label.text = "\n".join(lines)

    def _show_error(self, err_msg: str):
        self.report_label.text = f"[color=FF4444][b]Error during report generation:[/b]\n{err_msg}[/color]"


def color_tag(hex_code: str) -> str:
    return f"color={hex_code}"


if __name__ == "__main__":
    ReportEngineApp().run()
