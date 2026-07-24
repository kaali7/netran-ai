import json
from datetime import datetime
from pathlib import Path
from typing import Union, Dict, Any

from .audio_slicer import slice_audio
from .gemini_evaluator import GeminiMultimodalEvaluator
from .report_schema import CandidateReportPayload


def render_markdown_report(report: CandidateReportPayload) -> str:
    """
    Renders CandidateReportPayload into a beautifully formatted Markdown string.
    """
    md = []
    md.append(f"# Netran AI — Technical Candidate Evaluation Summary")
    md.append(f"**Session ID:** `{report.session_id}`  ")
    md.append(f"**Generated At:** {report.generated_at}  ")
    md.append(f"**Overall Hiring Signal:** **{report.overall_hiring_signal.upper()}**  \n")

    md.append("---")
    md.append("## Executive Scorecard")
    md.append(f"| Metric | Score / Value |")
    md.append(f"| --- | --- |")
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


def build_report(
    session_dir: Union[str, Path],
    model_name: str = "gemini-3.6-flash"
) -> CandidateReportPayload:
    """
    Main entry point for Stage 4 Report Generation.

    Args:
        session_dir: Directory path containing continuous_mic_input.wav and session_manifest.json
        model_name: Gemini model name (default: gemini-3.6-flash)

    Returns:
        Validated CandidateReportPayload object.
    """
    session_dir = Path(session_dir)
    manifest_path = session_dir / "session_manifest.json"
    wav_path = session_dir / "continuous_mic_input.wav"

    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest missing at {manifest_path}")
    if not wav_path.exists():
        raise FileNotFoundError(f"Audio file missing at {wav_path}")

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest_data = json.load(f)

    session_id = manifest_data.get("session_id", session_dir.name)
    turns = manifest_data.get("turns", [])

    print(f"[ReportBuilder] Starting Stage 4 processing for session: {session_id}")

    # Step 1: Slice audio
    turn_clips = slice_audio(
        wav_path=wav_path,
        manifest=manifest_data,
        output_dir=session_dir
    )

    # Step 2: Initialize Evaluator
    evaluator = GeminiMultimodalEvaluator(model_name=model_name)

    # Step 3: Run Audio and Technical branches per turn
    audio_outputs = []
    technical_outputs = []

    for turn in turns:
        t_id = turn.get("turn_id", 1)
        clip_path = turn_clips.get(t_id)

        # Audio branch
        if clip_path and clip_path.exists():
            aud_res = evaluator.evaluate_audio_branch(turn_id=t_id, audio_clip_path=clip_path)
            audio_outputs.append(aud_res)

        # Technical branch
        tec_res = evaluator.evaluate_technical_branch(
            turn_id=t_id,
            topic=turn.get("topic", "General Technical"),
            question_text=turn.get("question_text", ""),
            candidate_transcript=turn.get("candidate_transcript", "")
        )
        technical_outputs.append(tec_res)

    # Step 4: Run Combine branch
    final_report = evaluator.evaluate_combine_branch(
        session_id=session_id,
        turns_data=turns,
        audio_outputs=audio_outputs,
        technical_outputs=technical_outputs
    )

    # Ensure metadata fields
    if not final_report.generated_at:
        final_report.generated_at = datetime.utcnow().isoformat() + "Z"

    # Step 5: Save report.json
    json_path = session_dir / "report.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(final_report.model_dump(), f, indent=2)
    print(f"[ReportBuilder] Saved JSON report artifact to: {json_path}")

    # Step 6: Save evaluation_summary.md
    md_content = render_markdown_report(final_report)
    md_path = session_dir / "evaluation_summary.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)
    print(f"[ReportBuilder] Saved Markdown evaluation summary to: {md_path}")

    return final_report
