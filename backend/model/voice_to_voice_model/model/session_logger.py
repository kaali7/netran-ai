"""
Netran AI — Stage 3: Live Voice-to-Voice Loop
Module: session_logger.py
Description: Session telemetry tracking module using high-resolution monotonic clocks (`time.perf_counter()`)
             to generate the atomic `session_manifest.json` artifact for downstream Stage 4 audio slicing.
"""

import json
import os
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional

try:
    from .schemas import SessionManifest, TurnManifest
except ImportError:
    try:
        from model.voice_to_voice_model.model.schemas import SessionManifest, TurnManifest
    except ImportError:
        from schemas import SessionManifest, TurnManifest


class SessionLogger:
    """
    Manages session timer and logs per-turn transcript, timestamps, latency metrics,
    and adaptive branching decisions into a unified session_manifest.json file.
    """
    def __init__(self, session_id: str, session_dir: str):
        self.session_id = session_id
        self.session_dir = session_dir
        self.session_start_perf = time.perf_counter()
        self.session_start_iso = datetime.now(timezone.utc).isoformat()
        self.turns: List[TurnManifest] = []
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
        silence_duration_before_answer_sec: float = 0.0,
        stt_latency_ms: float = 0.0,
        ttft_ms: float = 0.0,
        question_id: Optional[int] = None,
        evaluation_branch_taken: Literal["strong_followup", "weak_followup", "next_topic"] = "next_topic"
    ):
        """Appends turn information to internal turn list using TurnManifest validation."""
        q_id = question_id if question_id is not None else turn_id

        turn_manifest = TurnManifest(
            turn_id=turn_id,
            question_id=q_id,
            topic=topic,
            question_text=question_text,
            candidate_transcript=candidate_transcript,
            audio_start_sec=round(audio_start_sec, 3),
            audio_end_sec=round(audio_end_sec, 3),
            silence_duration_before_answer_sec=round(max(0.0, silence_duration_before_answer_sec), 3),
            stt_latency_ms=round(stt_latency_ms, 1),
            ttft_ms=round(ttft_ms, 1),
            evaluation_branch_taken=evaluation_branch_taken
        )
        self.turns.append(turn_manifest)

    def finalize(self):
        """Writes the unified session_manifest.json file to disk and cleans up redundant files."""
        session_manifest = SessionManifest(
            session_id=self.session_id,
            session_start_iso=self.session_start_iso,
            total_turns=len(self.turns),
            turns=self.turns
        )

        manifest_path = os.path.join(self.session_dir, "session_manifest.json")
        try:
            with open(manifest_path, "w", encoding="utf-8") as f:
                f.write(session_manifest.model_dump_json(indent=2))
            print(f"[SessionLogger] Finalized session_manifest.json in: {self.session_dir}", flush=True)

            # Cleanup duplicate files if they exist to keep session directory clean
            for redundant_filename in ["transcript.json", "continuous_mic_input.wav"]:
                r_path = os.path.join(self.session_dir, redundant_filename)
                if os.path.exists(r_path):
                    try:
                        os.remove(r_path)
                        print(f"[SessionLogger] Removed redundant file: {redundant_filename}", flush=True)
                    except Exception:
                        pass

        except Exception as e:
            print(f"[SessionLogger Error] Failed to write manifest: {e}", flush=True)


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
