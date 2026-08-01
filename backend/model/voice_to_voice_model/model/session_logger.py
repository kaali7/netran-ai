"""
Netran AI — Stage 3: Live Voice-to-Voice Loop
Module: session_logger.py
Description: Session telemetry tracking module using high-resolution monotonic clocks (`time.perf_counter()`)
             to generate the atomic `transcript.json` artifact for downstream Stage 4 audio slicing.
"""

import json
import os
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional, Union

try:
    from .schemas import EvaluationMetrics, EvaluatedTechnicalSummary, SessionManifest, SessionMetadata, Telemetry, TurnManifest
except ImportError:
    try:
        from model.voice_to_voice_model.model.schemas import EvaluationMetrics, EvaluatedTechnicalSummary, SessionManifest, SessionMetadata, Telemetry, TurnManifest
    except ImportError:
        from schemas import EvaluationMetrics, EvaluatedTechnicalSummary, SessionManifest, SessionMetadata, Telemetry, TurnManifest


class SessionLogger:
    """
    Manages session timer and logs per-turn transcript, timestamps, latency metrics,
    and adaptive branching decisions into a unified transcript.json file.
    """
    def __init__(
        self,
        session_id: str,
        session_dir: str,
        candidate_name: str = "Candidate",
        target_role: str = "Software Engineer",
        target_company: str = "Netran AI"
    ):
        self.session_id = session_id
        self.session_dir = session_dir
        self.candidate_name = candidate_name
        self.target_role = target_role
        self.target_company = target_company
        self.session_start_perf = time.perf_counter()
        self.session_start_iso = datetime.now(timezone.utc).isoformat()
        self.turns: List[TurnManifest] = []
        self.total_barge_ins = 0
        os.makedirs(self.session_dir, exist_ok=True)

    def elapsed_sec(self) -> float:
        """Returns elapsed time in seconds since session start with millisecond precision."""
        return round(time.perf_counter() - self.session_start_perf, 3)

    def log_turn(
        self,
        turn_id: int,
        topic: str,
        question_text: str,
        candidate_transcript: str,
        audio_start_sec: float,
        audio_end_sec: float,
        turn_intent: Optional[str] = None,
        silence_duration_before_answer_sec: float = 0.0,
        stt_latency_ms: float = 0.0,
        ttft_ms: float = 0.0,
        tts_ttfa_ms: float = 0.0,
        barge_in_reaction_time_ms: float = 0.0,
        question_id: Optional[Union[int, str]] = None,
        evaluation_branch_taken: str = "next_topic",
        eva_reasoning: Optional[str] = None,
        eva_tone_used: str = "direct",
        eva_reply: Optional[str] = None,
        evaluation_metrics: Optional[Dict[str, Any]] = None,
        was_barge_in: bool = False
    ):
        """Appends turn information to internal turn list using TurnManifest validation."""
        q_id = question_id if question_id is not None else turn_id

        # Intent Tag Resolution
        if not turn_intent:
            if was_barge_in or barge_in_reaction_time_ms > 0:
                turn_intent = "BARGE_IN_INTERRUPTION"
            elif evaluation_branch_taken == "icebreaker_response":
                turn_intent = "ICEBREAKER"
            elif evaluation_branch_taken == "interviewer_meta":
                turn_intent = "CANDIDATE_META_QUERY"
            elif evaluation_branch_taken in ("audio_check", "thinking_pause"):
                turn_intent = "AUDIO_CHECK_OR_PAUSE"
            elif evaluation_branch_taken == "next_topic" and ("skip" in candidate_transcript.lower() or "don't know" in candidate_transcript.lower()):
                turn_intent = "SKIP_REQUEST"
            else:
                turn_intent = "TECHNICAL_ANSWER"

        if turn_intent == "BARGE_IN_INTERRUPTION" or was_barge_in:
            self.total_barge_ins += 1

        eval_metrics_obj = None
        if evaluation_metrics:
            eval_metrics_obj = EvaluationMetrics(
                keyword_density_score=float(evaluation_metrics.get("keyword_density_score", 0.0)),
                branch_taken=str(evaluation_metrics.get("branch_taken", evaluation_branch_taken)),
                matched_keywords=list(evaluation_metrics.get("matched_keywords", []))
            )

        telemetry_obj = Telemetry(
            stt_latency_ms=round(stt_latency_ms, 1),
            llm_ttft_ms=round(ttft_ms, 1),
            tts_ttfa_ms=round(tts_ttfa_ms, 1),
            barge_in_reaction_time_ms=round(barge_in_reaction_time_ms, 1)
        )

        turn_manifest = TurnManifest(
            turn_id=turn_id,
            timestamp_iso=datetime.now(timezone.utc).isoformat(),
            turn_intent=turn_intent,
            question_id=q_id,
            topic=topic,
            question_text=question_text,
            candidate_transcript=candidate_transcript,
            candidate_raw_transcript=candidate_transcript,
            audio_start_sec=round(audio_start_sec, 3),
            audio_end_sec=round(audio_end_sec, 3),
            silence_duration_before_answer_sec=round(max(0.0, silence_duration_before_answer_sec), 3),
            evaluation_branch_taken=evaluation_branch_taken,
            eva_internal_reasoning=eva_reasoning,
            eva_tone_used=eva_tone_used,
            eva_spoken_reply=eva_reply,
            evaluation_metrics=eval_metrics_obj,
            telemetry=telemetry_obj
        )
        self.turns.append(turn_manifest)

    def finalize(self, completed_naturally: bool = True):
        """Writes the unified transcript.json file to disk."""
        end_time_iso = datetime.now(timezone.utc).isoformat()
        
        total_turns = len(self.turns)
        strong_count = sum(1 for t in self.turns if t.evaluation_branch_taken == "strong_followup")
        weak_count = sum(1 for t in self.turns if t.evaluation_branch_taken == "weak_followup")
        skips_count = sum(1 for t in self.turns if t.turn_intent == "SKIP_REQUEST")
        
        scores = []
        for t in self.turns:
            if t.evaluation_metrics and t.evaluation_metrics.keyword_density_score > 0:
                scores.append(t.evaluation_metrics.keyword_density_score)
        avg_density = round(sum(scores) / len(scores), 2) if scores else 0.0
        
        topics_covered = len({t.topic for t in self.turns if t.topic and t.turn_intent == "TECHNICAL_ANSWER"})

        metadata = SessionMetadata(
            session_id=self.session_id,
            candidate_name=self.candidate_name,
            target_role=self.target_role,
            target_company=self.target_company,
            start_time_iso=self.session_start_iso,
            end_time_iso=end_time_iso,
            total_turns=total_turns,
            total_barge_ins=self.total_barge_ins
        )

        summary = EvaluatedTechnicalSummary(
            topics_covered=topics_covered,
            completed_naturally=completed_naturally,
            average_keyword_density=avg_density,
            strong_branches_triggered=strong_count,
            weak_branches_triggered=weak_count,
            skips_requested=skips_count
        )

        session_manifest = SessionManifest(
            session_metadata=metadata,
            turns=self.turns,
            evaluated_technical_summary=summary
        )

        transcript_path = os.path.join(self.session_dir, "transcript.json")
        try:
            dumped_data = session_manifest.model_dump()
            with open(transcript_path, "w", encoding="utf-8") as f:
                json.dump(dumped_data, f, indent=2)

            # Cleanup legacy session_manifest.json if present
            legacy_manifest = os.path.join(self.session_dir, "session_manifest.json")
            if os.path.exists(legacy_manifest):
                try:
                    os.remove(legacy_manifest)
                except Exception:
                    pass

            print(f"[SessionLogger] Finalized transcript.json in: {self.session_dir}", flush=True)
        except Exception as e:
            print(f"[SessionLogger Error] Failed to write transcript.json: {e}", flush=True)



if __name__ == "__main__":
    print("Testing SessionLogger Module...")
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        logger = SessionLogger(session_id="test_sess", session_dir=tmpdir)
        logger.log_turn(
            turn_id=1,
            topic="FastAPI",
            question_text="Explain async",
            candidate_transcript="AsyncIO uses event loop",
            audio_start_sec=1.0,
            audio_end_sec=5.0,
            evaluation_branch_taken="strong_followup"
        )
        logger.finalize()
        print("Logged turns count:", len(logger.turns))
