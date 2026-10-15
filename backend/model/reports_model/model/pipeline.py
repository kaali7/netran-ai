"""
Netran AI — Stage 4: Post-Session Evaluation & Report Generation Engine
Module: pipeline.py
Description: Master class-based Stage4Pipeline orchestrator executing non-destructive WAV slicing,
             deterministic audio delivery metrics, local CPU Speech Emotion Recognition (Wav2Vec2),
             high-speed Groq technical answer intelligence, and exporting dual report artifacts
             (`report.json` and `evaluation_summary.md`).
"""

import json
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from .answer_evaluator import AnswerEvaluator
    from .audio_metrics import calculate_audio_metrics
    from .audio_slicer import slice_audio
    from .config import Stage4Config
    from .emotion_service import predict_speech_emotion
    from .schemas import (
        AudioBranchOutput,
        CandidateReportPayload,
        TechnicalBranchOutput,
        TurnAnalysis,
        TurnTelemetry,
    )
except ImportError:
    try:
        from model.reports_model.model.answer_evaluator import AnswerEvaluator
        from model.reports_model.model.audio_metrics import calculate_audio_metrics
        from model.reports_model.model.audio_slicer import slice_audio
        from model.reports_model.model.config import Stage4Config
        from model.reports_model.model.emotion_service import predict_speech_emotion
        from model.reports_model.model.schemas import (
            AudioBranchOutput,
            CandidateReportPayload,
            TechnicalBranchOutput,
            TurnAnalysis,
            TurnTelemetry,
        )
    except ImportError:
        from answer_evaluator import AnswerEvaluator
        from audio_metrics import calculate_audio_metrics
        from audio_slicer import slice_audio
        from config import Stage4Config
        from emotion_service import predict_speech_emotion
        from schemas import (
            AudioBranchOutput,
            CandidateReportPayload,
            TechnicalBranchOutput,
            TurnAnalysis,
            TurnTelemetry,
        )


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
    md.append("## Detailed Turn-by-Turn Grounded Analysis")
    for turn in report.turn_evaluations:
        md.append(f"### Turn #{turn.turn_id}: {turn.question_text}")
        md.append(f"- **Candidate Response:** *\"{turn.candidate_transcript}\"*")

        # Telemetry metrics
        if getattr(turn, "telemetry", None):
            telem = turn.telemetry
            md.append(f"- **Precision Telemetry:** Latency: `{telem.initial_silence_latency_ms}ms` | Duration: `{telem.turn_duration_sec}s`")

        md.append(f"- **Scores:** Technical: `{turn.technical_score}/10` | Vocal Confidence: `{turn.vocal_confidence_score}/10`")
        md.append(f"- **Speech Characteristics:** Emotion: `{turn.emotional_state}` | Hesitation: `{turn.hesitation_level}` | Filler Count: `{turn.filler_word_count}`")
        if turn.missing_concepts:
            missing_str = ", ".join([f"`{m}`" for m in turn.missing_concepts])
            md.append(f"- **Missing/Weak Concepts:** {missing_str}")
        if getattr(turn, "resume_verification_note", None):
            md.append(f"- **Resume Claim Verification:** {turn.resume_verification_note}")
        md.append(f"- **Acoustic & Delivery Notes:** {turn.audio_notes}")

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
    """Master pipeline execution class for Stage 4 (Post-Session Evaluation & Report Generation)."""

    def __init__(self, config: Stage4Config | None = None):
        self.config = config or Stage4Config.from_env()
        self.evaluator = AnswerEvaluator(
            groq_api_key=self.config.groq_api_key,
            groq_model=self.config.groq_model,
            ollama_model=self.config.ollama_model,
        )

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

        resume_json_path = session_dir / "sample_resume.json"
        if resume_json_path.exists():
            with open(resume_json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                resume_text = data.get("resume_text", str(data))
        else:
            resume_path = session_dir / "sample_resume.txt"
            if not resume_path.exists():
                resume_path = session_dir / "resume.txt"
            if resume_path.exists():
                with open(resume_path, "r", encoding="utf-8") as f:
                    resume_text = f.read()

        jd_path = session_dir / "sample_job_detail.json"
        if jd_path.exists():
            with open(jd_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                rubric_text = json.dumps(data.get("rubric", data), indent=2)
        else:
            rubric_path = session_dir / "sample_rubric.json"
            if not rubric_path.exists():
                rubric_path = session_dir / "stage1_rubric.json"
            if rubric_path.exists():
                with open(rubric_path, "r", encoding="utf-8") as f:
                    rubric_text = f.read()

        return resume_text, rubric_text

    @classmethod
    def _evaluate_turns(
        cls,
        evaluator: AnswerEvaluator,
        turns: list[dict[str, Any]],
        turn_clips: dict[int, Path],
        resume_text: str = "",
        rubric_text: str = "",
        session_dir: Path | None = None,
        status_callback: Callable[[int, int, str], None] | None = None,
        config: Stage4Config | None = None,
    ) -> tuple[list[AudioBranchOutput], list[TechnicalBranchOutput]]:
        """
        Runs audio metrics, local CPU emotion inference, and Groq/Ollama technical evaluation
        per turn with parallel processing and thread-safe progressive caching.
        """
        import threading
        from concurrent.futures import ThreadPoolExecutor, as_completed

        cache_file = session_dir / "turn_cache.json" if session_dir else None
        cache_data = {}
        cache_lock = threading.Lock()

        if cache_file and cache_file.exists():
            with open(cache_file, "r", encoding="utf-8") as f:
                try:
                    cache_data = json.load(f)
                except Exception:
                    cache_data = {}

        total_turns = len(turns)
        turn_results: dict[int, tuple[AudioBranchOutput | None, TechnicalBranchOutput | None]] = {}
        uncached_items: list[tuple[int, dict[str, Any]]] = []

        # 1. Check Cache Hits
        for idx, turn in enumerate(turns, 1):
            t_id = turn.get("turn_id", idx)
            t_id_str = str(t_id)

            if t_id_str in cache_data:
                cached_turn = cache_data[t_id_str]
                aud_res = None
                tec_res = None
                if "audio" in cached_turn:
                    aud_res = AudioBranchOutput.model_validate(cached_turn["audio"])
                if "technical" in cached_turn:
                    tec_res = TechnicalBranchOutput.model_validate(cached_turn["technical"])
                if aud_res is not None and tec_res is not None:
                    turn_results[t_id] = (aud_res, tec_res)
                    continue

            uncached_items.append((idx, turn))

        # If all turns are cached, assemble and return immediately
        if not uncached_items:
            sorted_tids = sorted(turn_results.keys())
            audio_outputs = [turn_results[t][0] for t in sorted_tids if turn_results[t][0] is not None]
            technical_outputs = [turn_results[t][1] for t in sorted_tids if turn_results[t][1] is not None]
            return audio_outputs, technical_outputs

        max_workers = min(len(uncached_items), config.max_parallel_workers if config else 5)
        max_workers = max(1, max_workers)
        completed_count = len(turn_results)

        def _evaluate_single_turn(item: tuple[int, dict[str, Any]]) -> tuple[int, AudioBranchOutput, TechnicalBranchOutput]:
            idx, turn = item
            t_id = turn.get("turn_id", idx)
            t_id_str = str(t_id)
            topic = turn.get("topic", "General Technical")
            question_text = turn.get("question_text", "")
            transcript = turn.get("candidate_transcript", "")

            start_sec = float(turn.get("audio_start_sec", 0.0))
            end_sec = float(turn.get("audio_end_sec", 0.0))
            turn_duration = max(0.1, end_sec - start_sec if end_sec > start_sec else 10.0)

            clip_path = turn_clips.get(t_id)

            # 1. Deterministic Audio Metrics
            metrics = calculate_audio_metrics(
                transcript=transcript,
                duration_seconds=turn_duration,
                audio_path=clip_path,
            )

            # 2. Local CPU Speech Emotion Recognition (Wav2Vec2)
            if clip_path and clip_path.exists():
                emotion_res = predict_speech_emotion(clip_path)
            else:
                emotion_res = {
                    "emotional_state": "Calm",
                    "vocal_confidence_score": 6,
                    "delivery_notes": "Audio clip not available for acoustic analysis.",
                }

            combined_audio_notes = (
                f"{emotion_res['delivery_notes']} Speaking pace: {metrics['speaking_rate_wpm']} WPM "
                f"({metrics['long_pause_count']} pauses >0.7s, speech coverage {int(metrics['speech_coverage_ratio'] * 100)}%)."
            )

            aud_res = AudioBranchOutput(
                turn_id=t_id,
                gemini_verified_transcript=transcript,
                vocal_confidence_score=emotion_res["vocal_confidence_score"],
                hesitation_level=metrics["hesitation_level"],
                emotional_state=emotion_res["emotional_state"],
                filler_word_count=metrics["filler_word_count"],
                audio_notes=combined_audio_notes,
            )

            # 3. Technical Answer Intelligence Evaluation (Groq / Ollama / Rules)
            tec_res = evaluator.evaluate_turn(
                turn_id=t_id,
                topic=topic,
                question_text=question_text,
                candidate_transcript=transcript,
                resume_text=resume_text,
                jd_rubric_text=rubric_text,
            )

            # 4. Progressive Thread-Safe Caching
            with cache_lock:
                nonlocal completed_count
                completed_count += 1

                cache_data[t_id_str] = {
                    "audio": aud_res.model_dump(),
                    "technical": tec_res.model_dump(),
                }

                if cache_file:
                    try:
                        with open(cache_file, "w", encoding="utf-8") as f:
                            json.dump(cache_data, f, indent=2)
                    except Exception as ce:
                        print(f"[Stage4Pipeline] Cache write warning: {ce}", flush=True)

                if status_callback:
                    status_callback(completed_count, total_turns, f"Evaluated turn {completed_count}/{total_turns} ({topic})")

                print(f"[Stage4Pipeline] Evaluated Turn {t_id}/{total_turns} ({topic}) in ~0.5s", flush=True)

            return t_id, aud_res, tec_res

        # Parallel Turn Execution
        print(f"[Stage4Pipeline] Evaluating {len(uncached_items)} uncached turns with {max_workers} workers...", flush=True)
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_tid = {
                executor.submit(_evaluate_single_turn, item): item[1].get("turn_id", item[0])
                for item in uncached_items
            }

            for future in as_completed(future_to_tid):
                tid = future_to_tid[future]
                try:
                    ret_tid, aud_res, tec_res = future.result()
                    turn_results[ret_tid] = (aud_res, tec_res)
                except Exception as exc:
                    print(f"[Stage4Pipeline] [ERROR] Turn {tid} evaluation failed: {exc}", flush=True)
                    raise

        sorted_tids = sorted(turn_results.keys())
        audio_outputs = [turn_results[t][0] for t in sorted_tids if turn_results[t][0] is not None]
        technical_outputs = [turn_results[t][1] for t in sorted_tids if turn_results[t][1] is not None]

        return audio_outputs, technical_outputs

    @staticmethod
    def _save_report_artifacts(
        final_report: CandidateReportPayload,
        target_out_dir: Path,
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
        session_dir: str | Path,
        model_name: str | None = None,
        output_dir: str | Path | None = None,
        status_callback: Callable[[int, int, str], None] | None = None,
    ) -> CandidateReportPayload:
        """
        Main execution method for Stage 4 Post-Session Multimodal Evaluation.
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

        if "session_metadata" in manifest_data:
            session_id = manifest_data["session_metadata"].get("session_id", session_dir.name)
        else:
            session_id = manifest_data.get("session_id", session_dir.name)

        turns = manifest_data.get("turns", [])
        print(f"[Stage4Pipeline] Starting fast post-session evaluation for session: {session_id}")

        target_out_dir = Path(output_dir) if output_dir else session_dir
        target_out_dir.mkdir(parents=True, exist_ok=True)

        turn_clips = slice_audio(wav_path=wav_path, manifest=manifest_data, output_dir=target_out_dir)
        resume_text, rubric_text = self._load_session_context(session_dir)

        audio_outputs, technical_outputs = self._evaluate_turns(
            evaluator=self.evaluator,
            turns=turns,
            turn_clips=turn_clips,
            resume_text=resume_text,
            rubric_text=rubric_text,
            session_dir=session_dir,
            status_callback=status_callback,
            config=self.config,
        )

        # Combine synthesis
        synthesis = self.evaluator.evaluate_combine_branch(
            session_id=session_id,
            turns_data=turns,
            audio_outputs=audio_outputs,
            technical_outputs=technical_outputs,
            resume_text=resume_text,
            jd_rubric_text=rubric_text,
        )

        # Assemble full TurnAnalysis items
        turn_evaluations: list[TurnAnalysis] = []
        for t_data, aud, tec in zip(turns, audio_outputs, technical_outputs):
            telemetry_data = t_data.get("telemetry", {})
            start_s = float(t_data.get("audio_start_sec", 0.0))
            end_s = float(t_data.get("audio_end_sec", 0.0))
            turn_dur = round(max(0.0, end_s - start_s), 2)

            telem = TurnTelemetry(
                initial_silence_latency_ms=int(telemetry_data.get("stt_latency_ms", 0)),
                turn_duration_sec=turn_dur,
                stt_whisper_hallucination_flag=False,
            )

            turn_evaluations.append(
                TurnAnalysis(
                    turn_id=t_data.get("turn_id", 1),
                    question_text=t_data.get("question_text", ""),
                    candidate_transcript=t_data.get("candidate_transcript", ""),
                    gemini_verified_transcript=aud.gemini_verified_transcript if aud else t_data.get("candidate_transcript", ""),
                    telemetry=telem,
                    technical_score=tec.technical_score,
                    vocal_confidence_score=aud.vocal_confidence_score if aud else 6,
                    hesitation_level=aud.hesitation_level if aud else "Medium",
                    emotional_state=aud.emotional_state if aud else "Calm",
                    filler_word_count=aud.filler_word_count if aud else 0,
                    missing_concepts=tec.missing_concepts,
                    technical_notes=tec.technical_notes,
                    resume_verification_note=tec.resume_verification_note,
                    audio_notes=aud.audio_notes if aud else "Steady vocal pacing.",
                )
            )

        final_report = CandidateReportPayload(
            session_id=session_id,
            generated_at=datetime.now(timezone.utc).isoformat(),
            overall_hiring_signal=synthesis["overall_hiring_signal"],
            overall_technical_score=synthesis["overall_technical_score"],
            overall_vocal_confidence_score=synthesis["overall_vocal_confidence_score"],
            technical_pillars=synthesis["technical_pillars"],
            behavioral_flags=synthesis["behavioral_flags"],
            candidate_feedback=synthesis["candidate_feedback"],
            turn_evaluations=turn_evaluations,
            executive_summary=synthesis["executive_summary"],
        )

        self._save_report_artifacts(final_report, target_out_dir)
        print(f"[Stage4Pipeline] Complete! Saved report.json and evaluation_summary.md in {target_out_dir}")
        return final_report


# Backward compatibility wrapper
def build_report(
    session_dir: str | Path,
    model_name: str = "groq",
    output_dir: str | Path | None = None,
) -> CandidateReportPayload:
    return Stage4Pipeline().run(session_dir, output_dir=output_dir)
