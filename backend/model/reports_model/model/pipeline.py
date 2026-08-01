"""
Netran AI — Stage 4: Post-Session Multimodal Evaluation & Report Generation Engine
Module: pipeline.py
Description: Master class-based Stage4Pipeline orchestrator executing audio slicing, 3-branch evaluation,
             and exporting dual report artifacts (`report.json` and `evaluation_summary.md`).
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Union, Dict, Any, Optional

try:
    from .config import Stage4Config
    from .schemas import CandidateReportPayload, AudioBranchOutput, TechnicalBranchOutput
    from .audio_slicer import slice_audio
    from .gemini_evaluator import GeminiMultimodalEvaluator
except ImportError:
    try:
        from model.reports_model.model.config import Stage4Config
        from model.reports_model.model.schemas import CandidateReportPayload, AudioBranchOutput, TechnicalBranchOutput
        from model.reports_model.model.audio_slicer import slice_audio
        from model.reports_model.model.gemini_evaluator import GeminiMultimodalEvaluator
    except ImportError:
        from config import Stage4Config
        from schemas import CandidateReportPayload, AudioBranchOutput, TechnicalBranchOutput
        from audio_slicer import slice_audio
        from gemini_evaluator import GeminiMultimodalEvaluator


def render_markdown_report(report: CandidateReportPayload) -> str:
    """
    Renders CandidateReportPayload into a beautifully formatted Markdown string.
    """
    md = []
    md.append("# Netran AI — Technical Candidate Evaluation Summary")
    md.append(f"**Session ID:** `{report.session_id}`  ")
    md.append(f"**Generated At:** {report.generated_at}  ")
    md.append(f"**Overall Hiring Signal:** **{report.overall_hiring_signal.upper()}**  \n")

    md.append("---")
    md.append("## Executive Scorecard")
    md.append("| Metric | Score / Value |")
    md.append("| --- | --- |")
    md.append(f"| **Overall Technical Score** | **{report.overall_technical_score} / 100** |")
    md.append(f"| **Vocal Delivery & Confidence** | **{report.overall_vocal_confidence_score} / 100** |")
    md.append(f"| **Hiring Signal** | `{report.overall_hiring_signal}` |\n")

    md.append("### Executive Summary")
    md.append(f"> {report.executive_summary}\n")

    if report.behavioral_flags:
        md.append("---")
        md.append("## ⚠️ Integrity & Behavioral Red Flags")
        for flag in report.behavioral_flags:
            badge = "🚨" if flag.severity in ["CRITICAL", "HIGH"] else "⚠️"
            md.append(f"> {badge} **[{flag.severity}] Turn #{flag.turn_id} — {flag.type}**  ")
            md.append(f"> {flag.description}\n")

    if report.candidate_feedback:
        md.append("---")
        md.append("## 🚀 Candidate Growth & Learning Roadmap")
        if report.candidate_feedback.key_strengths:
            md.append("### 💪 Key Strengths")
            for s in report.candidate_feedback.key_strengths:
                md.append(f"- {s}")
            md.append("")
        if report.candidate_feedback.primary_growth_areas:
            md.append("### 📈 Primary Growth Areas")
            for g in report.candidate_feedback.primary_growth_areas:
                md.append(f"- {g}")
            md.append("")
        if report.candidate_feedback.recommended_topics_to_study:
            md.append("### 📚 Recommended Study Topics")
            for t in report.candidate_feedback.recommended_topics_to_study:
                md.append(f"- `{t}`")
            md.append("")

    md.append("---")
    md.append("## Core Technical Pillars")
    for pillar in report.technical_pillars:
        md.append(f"### 🔹 {pillar.pillar_name} ({pillar.score}/100)")
        md.append(f"{pillar.summary}\n")

    md.append("---")
    md.append("## Detailed Turn-by-Turn Audio Grounded Analysis")
    for turn in report.turn_evaluations:
        md.append(f"### Turn #{turn.turn_id}: {turn.question_text}")
        md.append(f"- **Original Transcript:** *\"{turn.candidate_transcript}\"*")
        md.append(f"- **Gemini Audio Verified Transcript:** *\"{turn.gemini_verified_transcript}\"*")
        
        # Telemetry metrics
        if getattr(turn, "telemetry", None):
            telem = turn.telemetry
            md.append(f"- **Precision Telemetry:** Latency: `{telem.initial_silence_latency_ms}ms` | Duration: `{telem.turn_duration_sec}s` | STT Hallucination Flag: `{telem.stt_whisper_hallucination_flag}`")
            if telem.stt_whisper_hallucination_flag:
                md.append("> [!CAUTION]")
                md.append("> **STT Audio Discrepancy Flag**: Local STT transcribed text, but raw audio waveform verification detected silence, whisper, or a completely different response.\n")
        
        md.append(f"- **Scores:** Technical: `{turn.technical_score}/10` | Vocal Confidence: `{turn.vocal_confidence_score}/10`")
        md.append(f"- **Speech Characteristics:** Emotion: `{turn.emotional_state}` | Hesitation: `{turn.hesitation_level}` | Filler Count: `{turn.filler_word_count}`")
        if turn.missing_concepts:
            missing_str = ", ".join([f"`{m}`" for m in turn.missing_concepts])
            md.append(f"- **Missing/Weak Concepts:** {missing_str}")
        if getattr(turn, "resume_verification_note", None):
            md.append(f"- **Resume Claim Verification:** {turn.resume_verification_note}")
        md.append(f"- **Audio & Delivery Notes:** {turn.audio_notes}")
        
        # Acoustic vs Technical Correlation Flag
        if turn.vocal_confidence_score >= 8 and turn.technical_score <= 4:
            md.append("> [!WARNING]")
            md.append("> **Correlation Flag**: High vocal confidence but low technical accuracy detected. Candidate may be overstating knowledge.\n")
        elif turn.vocal_confidence_score <= 4 and turn.technical_score >= 8:
            md.append("> [!NOTE]")
            md.append("> **Correlation Flag**: High technical accuracy but low vocal confidence detected. Candidate is skilled but may be nervous.\n")
        else:
            md.append("\n")

    md.append("---\n*Report generated automatically by Netran AI Stage 4 Evaluation Engine.*")
    return "\n".join(md)


class Stage4Pipeline:
    """Master pipeline execution class for Stage 4 (Post-Session Multimodal Evaluation & Report Generation)."""

    def __init__(self, config: Optional[Stage4Config] = None):
        self.config = config or Stage4Config.from_env()

    @staticmethod
    def _resolve_audio_file(session_dir: Path) -> Path:
        """Finds valid recording WAV file in session_dir."""
        wav_path = session_dir / "continuous_mic_input.wav"
        if wav_path.exists():
            return wav_path
        alt_wav_path = session_dir / "recording.wav"
        if alt_wav_path.exists():
            return alt_wav_path
        raise FileNotFoundError(f"Audio file missing at {wav_path} or {alt_wav_path}")

    @staticmethod
    def _load_session_context(session_dir: Path) -> tuple[str, str]:
        """Auto-reads resume and jd rubric from the session directory if available."""
        resume_text = "Not Provided"
        rubric_text = "Not Provided"
        
        resume_path = session_dir / "sample_resume.txt"
        if not resume_path.exists():
            resume_path = session_dir / "resume.txt"
        if resume_path.exists():
            with open(resume_path, "r", encoding="utf-8") as f:
                resume_text = f.read()

        rubric_path = session_dir / "sample_rubric.json"
        if not rubric_path.exists():
            rubric_path = session_dir / "stage1_rubric.json"
        if rubric_path.exists():
            with open(rubric_path, "r", encoding="utf-8") as f:
                rubric_text = f.read()
                
        return resume_text, rubric_text

    @staticmethod
    def _evaluate_turns(
        evaluator: GeminiMultimodalEvaluator,
        turns: list[dict[str, Any]],
        turn_clips: dict[int, Path],
        resume_text: str = "",
        rubric_text: str = ""
    ) -> tuple[list[AudioBranchOutput], list[TechnicalBranchOutput]]:
        """Runs audio and technical branch evaluations per turn."""
        import time
        audio_outputs = []
        technical_outputs = []

        for turn in turns:
            t_id = turn.get("turn_id", 1)
            clip_path = turn_clips.get(t_id)

            if clip_path and clip_path.exists():
                aud_res = evaluator.evaluate_audio_branch(
                    turn_id=t_id, 
                    audio_clip_path=clip_path,
                    resume_text=resume_text,
                    jd_rubric_text=rubric_text
                )
                audio_outputs.append(aud_res)
                time.sleep(3)  # Intra-turn rate limit pacing

            tec_res = evaluator.evaluate_technical_branch(
                turn_id=t_id,
                topic=turn.get("topic", "General Technical"),
                question_text=turn.get("question_text", ""),
                candidate_transcript=turn.get("candidate_transcript", ""),
                resume_text=resume_text,
                jd_rubric_text=rubric_text
            )
            technical_outputs.append(tec_res)
            
            # Anti-Rate-Limit pacing for Free Tier (15 RPM)
            time.sleep(4)

        return audio_outputs, technical_outputs

    @staticmethod
    def _save_report_artifacts(
        final_report: CandidateReportPayload,
        target_out_dir: Path,
        session_dir: Path
    ):
        """Saves report.json and evaluation_summary.md artifacts strictly to target_out_dir."""
        json_path = target_out_dir / "report.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(final_report.model_dump(), f, indent=2)

        md_content = render_markdown_report(final_report)
        md_path = target_out_dir / "evaluation_summary.md"
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_content)

    def run(
        self,
        session_dir: Union[str, Path],
        model_name: Optional[str] = None,
        output_dir: Optional[Union[str, Path]] = None
    ) -> CandidateReportPayload:
        """
        Main execution method for Stage 4 Report Generation.
        """
        session_dir = Path(session_dir)
        manifest_path = session_dir / "transcript.json"
        if not manifest_path.exists():
            manifest_path = session_dir / "session_manifest.json"
        if not manifest_path.exists():
            raise FileNotFoundError(f"Transcript manifest missing at {session_dir}")

        wav_path = self._resolve_audio_file(session_dir)

        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest_data = json.load(f)

        session_id = manifest_data.get("session_id", session_dir.name)
        turns = manifest_data.get("turns", [])
        print(f"[Stage4Pipeline] Starting processing for session: {session_id}")

        target_out_dir = Path(output_dir) if output_dir else session_dir
        target_out_dir.mkdir(parents=True, exist_ok=True)

        turn_clips = slice_audio(wav_path=wav_path, manifest=manifest_data, output_dir=target_out_dir)
        use_model = model_name or self.config.gemini_model or "gemini-3.6-flash"
        evaluator = GeminiMultimodalEvaluator(model_name=use_model, config=self.config)

        resume_text, rubric_text = self._load_session_context(session_dir)

        audio_outputs, technical_outputs = self._evaluate_turns(
            evaluator, turns, turn_clips, resume_text, rubric_text
        )

        final_report = evaluator.evaluate_combine_branch(
            session_id=session_id,
            turns_data=turns,
            audio_outputs=audio_outputs,
            technical_outputs=technical_outputs,
            resume_text=resume_text,
            jd_rubric_text=rubric_text
        )

        if not final_report.generated_at:
            final_report.generated_at = datetime.utcnow().isoformat() + "Z"

        self._save_report_artifacts(final_report, target_out_dir, session_dir)
        return final_report


# Backward compatibility wrapper
def build_report(
    session_dir: Union[str, Path],
    model_name: str = "gemini-3.6-flash",
    output_dir: Union[str, Path] = None
) -> CandidateReportPayload:
    return Stage4Pipeline().run(session_dir, model_name=model_name, output_dir=output_dir)
