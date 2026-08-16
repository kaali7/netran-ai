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

    return ReportResponse(
        session_id=session.id,
        status=session.status,
        evaluation_report=evaluation_report,
        progress_message=session.progress_message
    )

