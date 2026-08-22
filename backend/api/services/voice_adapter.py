import asyncio
import logging
import threading
from typing import Any

from api.schemas import VoiceTurnEvent
from api.config import BASE_DIR
SESSIONS_DIR = BASE_DIR / "data" / "sessions"

try:
    from model.voice_to_voice_model.model.voice_engine import WorkflowVoiceEngine
    from model.voice_to_voice_model.model.schemas import SessionManifest
except ImportError:
    try:
        from voice_to_voice_model.model.voice_engine import WorkflowVoiceEngine
        from voice_to_voice_model.model.schemas import SessionManifest
    except ImportError:
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "model", "voice_to_voice_model"))
        from model.voice_engine import WorkflowVoiceEngine
        from model.schemas import SessionManifest

logger = logging.getLogger(__name__)


def run_voice_session_with_callback(
    session_id: str,
    thread_safe_callback,
    stop_event: threading.Event,
    question_tree: list[dict[str, Any]],
    system_prompt: str,
    total_questions: int,
    audio_queue: Any = None,
    audio_out_queue: Any = None,
    engine_holder: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """
    Runs the WorkflowVoiceEngine in a background thread.
    Bridges engine callbacks via thread_safe_callback for the WebSocket.
    
    Returns the serialized SessionManifest on completion.
    """
    session_dir = str(SESSIONS_DIR / session_id)
    engine = WorkflowVoiceEngine(session_dir=session_dir, session_id=session_id)
    engine.stop_event = stop_event
    engine.inject_question_tree(questions=question_tree, system_prompt=system_prompt)
    if engine_holder is not None:
        engine_holder["engine"] = engine
    
    def status_callback(turn_id: int, state: str, question: str, transcript: str):
        progress_pct = int((turn_id / total_questions) * 100) if total_questions > 0 else 0
        progress_pct = min(100, progress_pct)
        
        event_type = state.split("|")[0]
        
        if event_type == "AUDIO_LEVEL":
            import json
            data = json.loads(state.split("|", 1)[1])
            thread_safe_callback(VoiceTurnEvent(
                event="AUDIO_LEVEL",
                session_id=session_id,
                turn_id=turn_id,
                detail=json.dumps(data)
            ))
            return

        branch_taken = state.split("|")[1] if "|" in state and len(state.split("|")) > 1 else None
        
        eva_response = None
        if event_type == "EVA_RESPONDING_BRANCH" and transcript:
            parts = transcript.split("\n\n[Eva]: ")
            if len(parts) == 2:
                transcript = parts[0]
                eva_response = parts[1]
                
        event = VoiceTurnEvent(
            event=event_type,
            session_id=session_id,
            turn_id=turn_id,
            question_text=question if question else None,
            candidate_transcript=transcript if transcript else None,
            eva_response=eva_response,
            branch_taken=branch_taken,
            progress_pct=progress_pct
        )
        thread_safe_callback(event)

    try:
        engine.run_interview(status_callback=status_callback, max_turns=total_questions, ws_audio_queue=audio_queue, ws_audio_out_queue=audio_out_queue)
        
        # Load final manifest
        import os
        import json
        manifest_path = os.path.join(session_dir, "session_manifest.json")
        if os.path.exists(manifest_path):
            with open(manifest_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return None
    except Exception as e:
        logger.error(f"Voice engine failed: {e}", exc_info=True)
        event = VoiceTurnEvent(
            event="ERROR",
            session_id=session_id,
            detail=str(e)
        )
        thread_safe_callback(event)
        return None
