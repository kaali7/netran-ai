"""
Netran AI — Questions Preview & Status Polling Router.
Fetch generated interview questions, live pipeline progress, and system persona.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session as DBSession

from api.db import get_db
from api.models import User, Session as SessionModel, SessionStatus
from api.schemas import SessionStatusResponse, QuestionPreviewResponse
from api.dependencies import get_current_user

router = APIRouter(prefix="/questions", tags=["Question Tree & Preview"])


@router.get(
    "/status/{session_id}",
    response_model=SessionStatusResponse,
    summary="Poll Pipeline Analysis Status",
    description=(
        "Poll current pipeline analysis state (`setup`, `analyzing`, `ready`) "
        "and human-readable live `progress_message`."
    ),
)
def get_analysis_status(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
) -> SessionStatusResponse:
    """Fetch live pipeline execution status and progress message for polling."""
    session_row = (
        db.query(SessionModel)
        .filter(
            SessionModel.id == session_id,
            SessionModel.user_id == current_user.id,
        )
        .first()
    )

    if not session_row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found or does not belong to you.",
        )

    return SessionStatusResponse(
        session_id=session_id,
        status=session_row.status,
        progress_message=session_row.progress_message or "No active pipeline status.",
    )


@router.get(
    "/preview/{session_id}",
    response_model=QuestionPreviewResponse,
    summary="Preview Generated Question Tree & Persona",
    description=(
        "Fetch generated 15-question tree, candidate resume analysis, and interviewer "
        "behavior prompt. Returns 202 Accepted if pipeline is still running, or 200 OK "
        "with complete payload when ready."
    ),
)
def preview_questions(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    """Fetch structured question tree and candidate breakdown for preview."""
    session_row = (
        db.query(SessionModel)
        .filter(
            SessionModel.id == session_id,
            SessionModel.user_id == current_user.id,
        )
        .first()
    )

    if not session_row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found or does not belong to you.",
        )

    # ── Check lifecycle state ────────────────────────────────────────────────
    if session_row.status == SessionStatus.SETUP:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Pipeline analysis has not been triggered for this session yet. "
                "Call POST /api/v1/setup/analyze first."
            ),
        )

    if session_row.status == SessionStatus.ANALYZING:
        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED,
            content={
                "session_id": session_id,
                "status": "analyzing",
                "progress_message": session_row.progress_message or "Pipeline processing...",
                "message": "Pipeline analysis is still in progress. Retry in a few seconds.",
            },
        )

    artifact = session_row.artifacts
    question_tree = (artifact.question_tree if artifact and artifact.question_tree else [])

    return QuestionPreviewResponse(
        session_id=session_id,
        status=session_row.status,
        total_questions=len(question_tree),
        question_tree=question_tree,
        resume_analysis=artifact.resume_analysis if artifact else None,
        interview_behavior=artifact.interview_behavior if artifact else None,
        jd_detail=artifact.jd_detail if artifact else None,
        cached=False,
    )
