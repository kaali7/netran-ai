import json
import logging
import os
import time
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

class ExecutionLogger:
    """
    Structured logger for tracing granular events across the voice-to-voice pipeline.
    Writes JSONL (JSON Lines) to execution_trace.jsonl in the session directory.
    Helps diagnose whether issues originate in the frontend or backend.
    """
    def __init__(self, session_id: str, session_dir: str):
        self.session_id = session_id
        self.session_dir = session_dir
        self.log_file = os.path.join(session_dir, "execution_trace.jsonl")
        
        # Ensure directory exists
        os.makedirs(self.session_dir, exist_ok=True)

    def log_event(self, source: str, event_type: str, details: dict[str, Any] = None):
        """
        Appends a structured event to the execution trace log.
        
        Args:
            source: e.g., "FRONTEND", "BACKEND_API", "BACKEND_ENGINE"
            event_type: e.g., "WS_CONNECTED", "VAD_TRIGGERED", "AUDIO_CHUNK_RECEIVED"
            details: Optional dictionary with granular metrics (sizes, latencies, etc.)
        """
        if details is None:
            details = {}
            
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "perf_time": time.perf_counter(),
            "session_id": self.session_id,
            "source": source,
            "event_type": event_type,
            "details": details
        }
        
        try:
            event_json = json.dumps(event)
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(event_json + "\n")
            # Showcase in terminal during runtime (using print to bypass FastAPI logger config)
            print(f"[EXEC_TRACE] [{source}] {event_type} - {details}", flush=True)
        except Exception as e:
            print(f"Failed to write to execution trace log for session {self.session_id}: {e}", flush=True)
