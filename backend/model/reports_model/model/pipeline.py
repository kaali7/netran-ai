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
        md.append(f"- **Scores:** Technical: `{turn.technical_score}/10` | Vocal Confidence: `{turn.vocal_confidence_score}/10`")
        md.append(f"- **Speech Characteristics:** Emotion: `{turn.emotional_state}` | Hesitation: `{turn.hesitation_level}` | Filler Count: `{turn.filler_word_count}`")
        if turn.missing_concepts:
            missing_str = ", ".join([f"`{m}`" for m in turn.missing_concepts])
            md.append(f"- **Missing/Weak Concepts:** {missing_str}")
        md.append(f"- **Audio & Delivery Notes:** {turn.audio_notes}\n")

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
    def _evaluate_turns(
        evaluator: GeminiMultimodalEvaluator,
        turns: list[dict[str, Any]],
        turn_clips: dict[int, Path]
    ) -> tuple[list[AudioBranchOutput], list[TechnicalBranchOutput]]:
        """Runs audio and technical branch evaluations per turn."""
        audio_outputs = []
        technical_outputs = []

        for turn in turns:
            t_id = turn.get("turn_id", 1)
            clip_path = turn_clips.get(t_id)

            if clip_path and clip_path.exists():
                aud_res = evaluator.evaluate_audio_branch(turn_id=t_id, audio_clip_path=clip_path)
                audio_outputs.append(aud_res)

            tec_res = evaluator.evaluate_technical_branch(
                turn_id=t_id,
                topic=turn.get("topic", "General Technical"),
                question_text=turn.get("question_text", ""),
                candidate_transcript=turn.get("candidate_transcript", "")
            )
            technical_outputs.append(tec_res)

        return audio_outputs, technical_outputs

    @staticmethod
    def _save_report_artifacts(
        final_report: CandidateReportPayload,
        target_out_dir: Path,
        session_dir: Path
    ):
        """Saves report.json and evaluation_summary.md artifacts."""
        json_path = target_out_dir / "report.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(final_report.model_dump(), f, indent=2)

        md_content = render_markdown_report(final_report)
        md_path = target_out_dir / "evaluation_summary.md"
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_content)

        if target_out_dir != session_dir:
            try:
                with open(session_dir / "report.json", "w", encoding="utf-8") as f:
                    json.dump(final_report.model_dump(), f, indent=2)
                with open(session_dir / "evaluation_summary.md", "w", encoding="utf-8") as f:
                    f.write(md_content)
            except OSError:
                pass

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
        manifest_path = session_dir / "session_manifest.json"
        if not manifest_path.exists():
            raise FileNotFoundError(f"Manifest missing at {manifest_path}")

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

        audio_outputs, technical_outputs = self._evaluate_turns(evaluator, turns, turn_clips)

        final_report = evaluator.evaluate_combine_branch(
            session_id=session_id,
            turns_data=turns,
            audio_outputs=audio_outputs,
            technical_outputs=technical_outputs
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
