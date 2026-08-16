"""
Netran AI — Setup & Pipeline Analysis Router.
Triggers Stage 1 (Tavily Research) & Stage 2 (15-Question Tree & Persona Engine) in background.
"""

from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException, status
from sqlalchemy.orm import Session as DBSession

from api.db import get_db
from api.models import User, Session as SessionModel, SessionStatus
from api.schemas import AnalyzeRequest, AnalyzeStatusResponse
from api.dependencies import get_current_user
from api.services.pipeline_runner import run_stage1_and_stage2

router = APIRouter(prefix="/setup", tags=["Setup & Pipeline Analysis"])


@router.post(
    "/analyze",
    response_model=AnalyzeStatusResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger Stage 1 & 2 Pipeline Analysis",
    description=(
        "Triggers async execution for Stage 1 (Tavily research) and Stage 2 (15-question tree & "
        "interviewer system prompt). Requires prior resume upload (`POST /ingest/resume`) and "
        "JD ingestion (`POST /ingest/jd`). Returns 202 Accepted immediately while the background "
        "task runs. Poll `GET /questions/status/{session_id}` for progress."
    ),
)
def trigger_analysis(
    request: AnalyzeRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
) -> AnalyzeStatusResponse:
    """Trigger background processing for Stage 1 Research & Stage 2 Question Tree."""

    # ── 1. Fetch & validate session ownership ─────────────────────────────
    session_row = (
        db.query(SessionModel)
        .filter(
            SessionModel.id == request.session_id,
            SessionModel.user_id == current_user.id,
        )
        .first()
    )

    if not session_row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{request.session_id}' not found or does not belong to you.",
        )

    # ── 2. Validate that required ingestion artifacts exist ────────────────
    artifact = session_row.artifacts
    if not artifact or not artifact.parsed_resume:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Resume has not been uploaded for this session yet. "
                "Please upload a resume via POST /api/v1/ingest/resume first."
            ),
        )

    if not artifact or not artifact.parsed_jd:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Job Description has not been ingested for this session yet. "
                "Please ingest a JD via POST /api/v1/ingest/jd first."
            ),
        )

    # ── 3. Guard against duplicate running pipeline ──────────────────────────
    if session_row.status == SessionStatus.ANALYZING and not request.force_refresh:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Pipeline analysis is already currently running for this session. "
                "Poll GET /api/v1/questions/status/{session_id} for progress."
            ),
        )

    # ── 4. Set status to ANALYZING & commit before starting background task ─
    session_row.status = SessionStatus.ANALYZING
    session_row.progress_message = "Starting pipeline..."
    db.commit()

    # ── 5. Dispatch background task ─────────────────────────────────────────
    target_seniority = request.target_seniority or "Senior"
    force_refresh = bool(request.force_refresh)

    background_tasks.add_task(
        run_stage1_and_stage2,
        session_id=request.session_id,
        target_seniority=target_seniority,
        force_refresh=force_refresh,
    )

    return AnalyzeStatusResponse(
        session_id=request.session_id,
        status=SessionStatus.ANALYZING,
        progress_message="Starting pipeline...",
        message="Pipeline analysis started in background. Poll /questions/status for progress.",
    )
