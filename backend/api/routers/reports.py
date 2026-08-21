"""
Netran AI — Stage 4 Multimodal Reports Router.
Triggers evaluation and fetches session reports.
"""

from fastapi import APIRouter, Depends, status, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session as DBSession

from api.db import get_db
from api.models import User, Session, SessionArtifact, SessionStatus
from api.dependencies import get_current_user
from api.schemas import ReportGenerateResponse, ReportResponse
from api.services.pipeline_runner import run_stage4

router = APIRouter(prefix="/reports", tags=["Evaluation & Reports"])


@router.post("/generate/{session_id}", response_model=ReportGenerateResponse, status_code=status.HTTP_202_ACCEPTED)
def generate_report(
    session_id: str,
    background_tasks: BackgroundTasks,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Trigger Stage 4 multimodal evaluation background task.
    Evaluates transcript, audio waveforms, hesitation, and technical accuracy.
    """
    session = db.query(Session).filter(Session.id == session_id, Session.user_id == current_user.id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    session.status = SessionStatus.EVALUATING
    session.progress_message = "Stage 4: Post-session multimodal report generation queued..."
    db.commit()

    background_tasks.add_task(run_stage4, session_id)

    return ReportGenerateResponse(
        session_id=session.id,
        status=SessionStatus.EVALUATING,
        progress_message=session.progress_message,
        message="Report generation triggered in background."
    )


@router.get("/{session_id}", response_model=ReportResponse)
def get_report(
    session_id: str,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Fetch completed evaluation report JSON & session status.
    """
    session = db.query(Session).filter(Session.id == session_id, Session.user_id == current_user.id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    artifact = db.query(SessionArtifact).filter(SessionArtifact.session_id == session_id).first()
    evaluation_report = artifact.evaluation_report if artifact else None

    # Enrich turn_evaluations with audio timings from transcript manifest if available
    if evaluation_report and isinstance(evaluation_report, dict) and artifact and artifact.transcript:
        raw_t = artifact.transcript
        transcript_turns = (
            raw_t.get("turns") or raw_t.get("full_chronological_transcript")
            if isinstance(raw_t, dict)
            else (raw_t if isinstance(raw_t, list) else [])
        )
        if isinstance(transcript_turns, list):
            turn_map = {
                t.get("turn_id", idx + 1): t
                for idx, t in enumerate(transcript_turns)
                if isinstance(t, dict)
            }
            turn_evals = evaluation_report.get("turn_evaluations", [])
            for t_item in turn_evals:
                if isinstance(t_item, dict):
                    t_id = t_item.get("turn_id")
                    if t_id in turn_map:
                        src = turn_map[t_id]
                        t_item["audio_start_sec"] = src.get("audio_start_sec", 0.0)
                        t_item["audio_end_sec"] = src.get("audio_end_sec", 0.0)

    return ReportResponse(
        session_id=session.id,
        status=session.status,
        evaluation_report=evaluation_report,
        progress_message=session.progress_message
    )

