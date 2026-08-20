import asyncio
import logging
import threading
from typing import Any
from datetime import datetime, timezone

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session as DBSession

from api.db import get_db
from api.dependencies import get_current_user, get_ws_user
from api.models import User, Session, SessionStatus, SessionArtifact
from api.schemas import VoiceSessionStatusResponse, VoiceTurnEvent
from api.services.voice_adapter import run_voice_session_with_callback

from pathlib import Path
from fastapi.responses import FileResponse
import sys
import os

try:
    from model.voice_to_voice_model.model.execution_logger import ExecutionLogger
except ImportError:
    ExecutionLogger = None

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/voice", tags=["Voice Interview"])


@router.get("/status/{session_id}", response_model=VoiceSessionStatusResponse)
def check_voice_session_status(
    session_id: str,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Check if a session is ready for a voice interview before connecting.
    Uses the same token validation logic as the WebSocket.
    """
    session = db.query(Session).filter(Session.id == session_id, Session.user_id == current_user.id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    return VoiceSessionStatusResponse(
        session_id=session.id,
        status=session.status,
        total_turns_completed=0,
        interview_started_at=None
    )


@router.get("/recording/{session_id}")
def stream_audio_recording(
    session_id: str,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Stream continuous audio recording file (.wav) for candidate session playback.
    """
    session = db.query(Session).filter(Session.id == session_id, Session.user_id == current_user.id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    base_dir = Path(__file__).resolve().parent.parent.parent
    possible_paths = [
        base_dir / "data" / "sessions" / session_id / "continuous_mic_input.wav",
        base_dir / "model" / "voice_to_voice_model" / "test" / "output" / session_id / "recording.wav",
        base_dir / "model" / "reports_model" / "test" / "input" / "sample_session" / "continuous_mic_input.wav",
    ]

    for p in possible_paths:
        if p.exists():
            return FileResponse(
                path=str(p),
                media_type="audio/wav",
                filename=f"recording_{session_id}.wav"
            )

    raise HTTPException(status_code=404, detail="Audio recording file not found for this session")


@router.websocket("/stream/{session_id}")
async def voice_interview_stream(
    websocket: WebSocket,
    session_id: str,
    current_user: User = Depends(get_ws_user),
    db: DBSession = Depends(get_db)
):
    """
    WebSocket endpoint for full-duplex voice interview streaming.
    """
    await websocket.accept()

    # Validate session
    session = db.query(Session).filter(Session.id == session_id, Session.user_id == current_user.id).first()
    if not session:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Session not found")
        return
        
    if session.status not in [SessionStatus.READY, SessionStatus.IN_PROGRESS]:
        await websocket.send_json({"event": "ERROR", "detail": f"Session is in {session.status.value} state, must be ready"})
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
        
    artifact = session.artifacts
    if not artifact or not artifact.question_tree or not artifact.interview_behavior:
        await websocket.send_json({"event": "ERROR", "detail": "Missing question tree or behavior artifacts"})
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    questions = artifact.question_tree
    behavior = artifact.interview_behavior
    system_prompt = behavior.get("interviewer_system_prompt", "")
    candidate_name = behavior.get("candidate_name", "Candidate")
    total_questions = len(questions)
    
    if total_questions == 0:
        await websocket.send_json({"event": "ERROR", "detail": "Question tree is empty"})
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # Update state to IN_PROGRESS
    session.status = SessionStatus.IN_PROGRESS
    session.progress_message = "Voice interview in progress"
    db.commit()

    await websocket.send_json({
        "event": "CONNECTED",
        "session_id": session_id,
        "candidate_name": candidate_name,
        "total_questions": total_questions
    })

    # Instantiate execution logger
    exec_logger = None
    if ExecutionLogger:
        base_dir = Path(__file__).resolve().parent.parent.parent
        session_dir = str(base_dir / "model" / "voice_to_voice_model" / "test" / "output" / session_id)
        exec_logger = ExecutionLogger(session_id=session_id, session_dir=session_dir)
        exec_logger.log_event("BACKEND_API", "WS_CONNECTED", {"total_questions": total_questions})

    # Prepare threading primitives
    ws_queue = asyncio.Queue()
    stop_event = threading.Event()
    import queue
    audio_queue = queue.Queue()
    audio_out_queue = queue.Queue()
    loop = asyncio.get_running_loop()

    def thread_safe_callback(event: VoiceTurnEvent):
        loop.call_soon_threadsafe(ws_queue.put_nowait, event.model_dump(exclude_none=True))

    # Background task for draining ws_queue -> WebSocket
    async def send_worker():
        try:
            while True:
                event_dict = await ws_queue.get()
                await websocket.send_json(event_dict)
                ws_queue.task_done()
                if event_dict.get("event") in ["INTERVIEW_COMPLETE", "ERROR"]:
                    break
        except (WebSocketDisconnect, RuntimeError):
            pass
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error in send_worker: {type(e).__name__} - {str(e)}")

    # Background task for reading from WebSocket -> engine control & audio streaming
    async def recv_worker():
        import json
        try:
            while True:
                message = await websocket.receive()
                if "bytes" in message:
                    # Raw PCM audio chunk from frontend Worklet
                    if exec_logger:
                        exec_logger.log_event("FRONTEND", "AUDIO_CHUNK_RECEIVED", {"size_bytes": len(message["bytes"])})
                    audio_queue.put(message["bytes"])
                elif "text" in message:
                    data = json.loads(message["text"])
                    action = data.get("action")
                    if action == "client_log":
                        if exec_logger:
                            exec_logger.log_event("FRONTEND", data.get("event_type", "UNKNOWN"), data.get("details", {}))
                    elif action == "stop":
                        logger.info(f"Client requested stop for session {session_id}")
                        stop_event.set()
                        break
                    elif action == "ping":
                        await websocket.send_json({"event": "pong"})
        except (WebSocketDisconnect, RuntimeError):
            logger.info(f"WebSocket disconnected for session {session_id}")
            stop_event.set()
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error in recv_worker: {type(e).__name__} - {str(e)}")
            stop_event.set()

    async def audio_send_worker():
        try:
            while not stop_event.is_set():
                try:
                    chunk = audio_out_queue.get_nowait()
                    if exec_logger:
                        exec_logger.log_event("BACKEND_API", "AUDIO_CHUNK_SENT", {"size_bytes": len(chunk)})
                    await websocket.send_bytes(chunk)
                except queue.Empty:
                    await asyncio.sleep(0.02)
        except (WebSocketDisconnect, RuntimeError, asyncio.CancelledError):
            pass

    send_task = asyncio.create_task(send_worker())
    audio_send_task = asyncio.create_task(audio_send_worker())
    recv_task = asyncio.create_task(recv_worker())

    try:
        # Run synchronous voice engine in thread pool
        manifest = await asyncio.to_thread(
            run_voice_session_with_callback,
            session_id,
            thread_safe_callback,
            stop_event,
            questions,
            system_prompt,
            total_questions,
            audio_queue,
            audio_out_queue
        )
        
        # Interview finished or stopped
        # Signal send worker we are done by putting INTERVIEW_COMPLETE
        await ws_queue.put({
            "event": "INTERVIEW_COMPLETE",
            "session_id": session_id,
            "total_turns": manifest.get("total_turns", 0) if manifest else 0,
            "session_status": "evaluating"
        })
        
        # Wait for queue to flush
        await send_task

        # Save manifest
        if manifest:
            # Re-fetch session to avoid stale DB state
            session = db.query(Session).filter(Session.id == session_id).first()
            if session and session.artifacts:
                session.artifacts.transcript = manifest
                
                # Prevent React Strict Mode double-connects from instantly terminating the session
                total_turns = manifest.get("total_turns", 0)
                if total_turns > 0:
                    session.status = SessionStatus.EVALUATING
                    session.progress_message = "Interview complete. Generating evaluation report."
                else:
                    session.status = SessionStatus.READY
                    session.progress_message = "Ready to start interview"
                    
                db.commit()

    except Exception as e:
        logger.error(f"Voice session error: {e}", exc_info=True)
    finally:
        send_task.cancel()
        audio_send_task.cancel()
        recv_task.cancel()
        if not stop_event.is_set():
            stop_event.set()
        try:
            await websocket.close()
            if exec_logger:
                exec_logger.log_event("BACKEND_API", "WS_DISCONNECTED", {})
        except Exception:
            pass
