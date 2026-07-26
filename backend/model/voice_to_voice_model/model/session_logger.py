"""
Netran AI — Stage 3: Live Voice-to-Voice Loop
Module: session_logger.py
Description: Session telemetry tracking module using high-resolution monotonic clocks (`time.perf_counter()`)
             to generate the atomic `session_manifest.json` artifact for downstream Stage 4 audio slicing.
"""

import os
import json
import time
from datetime import datetime

class SessionLogger:
    """
    Manages session timer and logs per-turn transcript, timestamps, and performance metrics
    into a session_manifest.json file.
    """
    def __init__(self, session_id: str, session_dir: str):
        self.session_id = session_id
        self.session_dir = session_dir
        self.session_start_perf = time.perf_counter()
        self.session_start_iso = datetime.utcnow().isoformat() + "Z"
        self.turns = []
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
        silence_duration_before_answer_sec: float,
        stt_latency_ms: float = 0.0,
        ttft_ms: float = 0.0
    ):
        """Appends turn information to internal list."""
        turn_data = {
            "turn_id": turn_id,
            "topic": topic,
            "question_text": question_text,
            "candidate_transcript": candidate_transcript,
            "audio_start_sec": round(audio_start_sec, 3),
            "audio_end_sec": round(audio_end_sec, 3),
            "silence_duration_before_answer_sec": round(max(0.0, silence_duration_before_answer_sec), 3),
            "stt_latency_ms": round(stt_latency_ms, 1),
            "ttft_ms": round(ttft_ms, 1)
        }
        self.turns.append(turn_data)

    def finalize(self):
        """Writes the session manifest and transcript JSON files to disk."""
        manifest = {
            "session_id": self.session_id,
            "session_start_iso": self.session_start_iso,
            "total_turns": len(self.turns),
            "turns": self.turns
        }
        manifest_path = os.path.join(self.session_dir, "session_manifest.json")
        transcript_path = os.path.join(self.session_dir, "transcript.json")
        try:
            with open(manifest_path, "w", encoding="utf-8") as f:
                json.dump(manifest, f, indent=2)
            with open(transcript_path, "w", encoding="utf-8") as f:
                json.dump(manifest, f, indent=2)
            print(f"[SessionLogger] Finalized manifest & transcript artifacts in: {self.session_dir}", flush=True)
        except Exception as e:
            print(f"[SessionLogger Error] Failed to write manifest: {e}", flush=True)
