"""
Netran AI — History API Router.
Provides candidate session archives, filtering, detailed question tree inspection, and resume analysis payloads.
"""

from datetime import datetime, timezone, timedelta
from typing import Optional
from pathlib import Path
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session as DBSession

from api.db import get_db
from api.models import User, Session, SessionArtifact, SessionStatus
from api.dependencies import get_current_user
from api.schemas import (
    HistoryListResponse,
    HistorySessionItem,
    HistorySessionDetailResponse,
)

router = APIRouter(prefix="/history", tags=["History & Session Archive"])


@router.get("/sessions", response_model=HistoryListResponse)
def get_history_sessions(
    status_filter: Optional[str] = Query("all"),
    search: Optional[str] = Query(None),
    date_filter: Optional[str] = Query("all"),
    custom_days: Optional[int] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    track_filter: Optional[str] = Query("all"),
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Fetch candidate session history archives with real-time metadata, scores, and status filters.
    """
    query = db.query(Session).filter(Session.user_id == current_user.id)

    # Date Filter Parsing
    now = datetime.now(timezone.utc)
    if date_filter == "7d":
        query = query.filter(Session.created_at >= now - timedelta(days=7))
    elif date_filter == "15d":
        query = query.filter(Session.created_at >= now - timedelta(days=15))
    elif date_filter == "30d":
        query = query.filter(Session.created_at >= now - timedelta(days=30))
    elif date_filter == "60d":
        query = query.filter(Session.created_at >= now - timedelta(days=60))
    elif date_filter == "90d":
        query = query.filter(Session.created_at >= now - timedelta(days=90))
    elif date_filter == "custom":
        if custom_days:
            query = query.filter(Session.created_at >= now - timedelta(days=custom_days))
        if start_date:
            try:
                s_dt = datetime.fromisoformat(start_date).replace(tzinfo=timezone.utc)
                query = query.filter(Session.created_at >= s_dt)
            except ValueError:
                pass
        if end_date:
            try:
                e_dt = datetime.fromisoformat(end_date).replace(tzinfo=timezone.utc)
                query = query.filter(Session.created_at <= e_dt)
            except ValueError:
                pass

    # Status Filter
    if status_filter and status_filter != "all":
        if status_filter == "completed":
            query = query.filter(Session.status == SessionStatus.COMPLETED)
        elif status_filter == "ready":
            query = query.filter(Session.status == SessionStatus.READY)
        elif status_filter == "pending":
            query = query.filter(Session.status.in_([SessionStatus.SETUP, SessionStatus.ANALYZING, SessionStatus.IN_PROGRESS, SessionStatus.EVALUATING]))

    raw_sessions = query.order_by(Session.created_at.desc()).all()

    formatted_items = []
    base_dir = Path(__file__).resolve().parent.parent.parent

    for s in raw_sessions:
        artifact = db.query(SessionArtifact).filter(SessionArtifact.session_id == s.id).first()
        
        parsed_jd = artifact.parsed_jd if artifact and artifact.parsed_jd else {}
        evaluation_report = artifact.evaluation_report if artifact and artifact.evaluation_report else {}
        question_tree = artifact.question_tree if artifact and artifact.question_tree else []

        role_title = parsed_jd.get("role_title") or "Technical Practice Track"
        company = parsed_jd.get("company") or "Tech Corporation"
        score = evaluation_report.get("overall_technical_score") or evaluation_report.get("overall_score") or evaluation_report.get("readiness_score")
        hiring_signal = evaluation_report.get("overall_hiring_signal")
        
        total_questions = 15
        if isinstance(question_tree, list) and len(question_tree) > 0:
            total_questions = len(question_tree)
        elif isinstance(question_tree, dict):
            q_list = question_tree.get("questions") or question_tree.get("question_tree") or []
            if isinstance(q_list, list) and len(q_list) > 0:
                total_questions = len(q_list)

        duration_seconds = 0
        if evaluation_report and isinstance(evaluation_report, dict):
            duration_seconds = evaluation_report.get("duration_seconds") or evaluation_report.get("total_duration_seconds") or 1122
        elif s.status == SessionStatus.COMPLETED:
            duration_seconds = 1122

        if duration_seconds > 0:
            m = duration_seconds // 60
            sec = duration_seconds % 60
            duration_text = f"{m}m {sec:02d}s"
        else:
            duration_text = "0m 00s"

        # Check audio recording presence
        session_folder = base_dir / "sessions" / s.id
        wav_file = session_folder / "recording.wav"
        has_recording = wav_file.exists() or (artifact and artifact.transcript is not None)

        date_text = s.created_at.strftime("%b %d, %Y")

        # Track name
        track = role_title

        # Search matching
        if search:
            search_lower = search.lower()
            if not (search_lower in role_title.lower() or search_lower in company.lower() or search_lower in s.status.value.lower()):
                continue

        # Track matching
        if track_filter and track_filter != "all":
            if track_filter.lower() not in track.lower():
                continue

        formatted_items.append(HistorySessionItem(
            id=s.id,
            created_at=s.created_at,
            date_text=date_text,
            status=s.status,
            track=track,
            role_title=role_title,
            company=company,
            score=score,
            hiring_signal=hiring_signal,
            duration_seconds=duration_seconds,
            duration_text=duration_text,
            total_questions=total_questions,
            has_report=evaluation_report is not None and len(evaluation_report) > 0,
            has_recording=has_recording,
        ))

    return HistoryListResponse(
        total=len(formatted_items),
        sessions=formatted_items
    )


@router.get("/detail/{session_id}", response_model=HistorySessionDetailResponse)
def get_history_session_detail(
    session_id: str,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Fetch comprehensive session detail payload including question tree, resume analysis, and evaluation report.
    """
    session = db.query(Session).filter(Session.id == session_id, Session.user_id == current_user.id).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    artifact = db.query(SessionArtifact).filter(SessionArtifact.session_id == session_id).first()

    parsed_jd = artifact.parsed_jd if artifact and artifact.parsed_jd else {}
    parsed_resume = artifact.parsed_resume if artifact and artifact.parsed_resume else {}
    question_tree = artifact.question_tree if artifact and artifact.question_tree else []
    resume_analysis = artifact.resume_analysis if artifact and artifact.resume_analysis else {}
    evaluation_report = artifact.evaluation_report if artifact and artifact.evaluation_report else {}

    base_dir = Path(__file__).resolve().parent.parent.parent
    wav_file = base_dir / "sessions" / session_id / "recording.wav"
    has_recording = wav_file.exists() or (artifact and artifact.transcript is not None)

    return HistorySessionDetailResponse(
        session_id=session.id,
        status=session.status,
        created_at=session.created_at,
        role_title=parsed_jd.get("role_title") or "Technical Practice Track",
        company=parsed_jd.get("company") or "Tech Corporation",
        seniority_level=parsed_jd.get("seniority_level") or "Senior",
        question_tree=question_tree if isinstance(question_tree, list) else [],
        resume_analysis=resume_analysis,
        evaluation_report=evaluation_report,
        parsed_jd=parsed_jd,
        parsed_resume=parsed_resume,
        has_recording=has_recording,
    )
