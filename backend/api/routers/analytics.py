"""
Netran AI — Analytics API Router.
Provides aggregated candidate interview readiness, pillar skill matrix, score trends, and real AI synthesis.
"""

from datetime import datetime, timezone, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session as DBSession

from api.db import get_db
from api.models import User, Session, SessionArtifact, SessionStatus
from api.dependencies import get_current_user
from api.schemas import (
    AnalyticsSummaryResponse,
    InsightItem,
    SkillMatrixItem,
    SessionComparisonItem,
)

router = APIRouter(prefix="/analytics", tags=["Analytics & Telemetry"])


@router.get("/summary", response_model=AnalyticsSummaryResponse)
def get_analytics_summary(
    time_range: str = Query("30d", pattern="^(7d|15d|30d|60d|90d|all|custom)$"),
    custom_days: Optional[int] = Query(None, ge=1, le=365),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Fetch candidate's aggregated performance report metrics.
    Aggregates composite readiness, domain skill matrix, score trends, and AI insights.
    """
    query = db.query(Session).filter(Session.user_id == current_user.id)

    now = datetime.now(timezone.utc)
    if time_range == "7d":
        cutoff = now - timedelta(days=7)
        query = query.filter(Session.created_at >= cutoff)
    elif time_range == "15d":
        cutoff = now - timedelta(days=15)
        query = query.filter(Session.created_at >= cutoff)
    elif time_range == "30d":
        cutoff = now - timedelta(days=30)
        query = query.filter(Session.created_at >= cutoff)
    elif time_range == "60d":
        cutoff = now - timedelta(days=60)
        query = query.filter(Session.created_at >= cutoff)
    elif time_range == "90d":
        cutoff = now - timedelta(days=90)
        query = query.filter(Session.created_at >= cutoff)
    elif time_range == "custom":
        if start_date and end_date:
            try:
                s_dt = datetime.fromisoformat(start_date).replace(tzinfo=timezone.utc)
                e_dt = datetime.fromisoformat(end_date).replace(tzinfo=timezone.utc) + timedelta(days=1)
                query = query.filter(Session.created_at >= s_dt, Session.created_at <= e_dt)
            except ValueError:
                pass
        elif custom_days:
            cutoff = now - timedelta(days=custom_days)
            query = query.filter(Session.created_at >= cutoff)
        else:
            cutoff = now - timedelta(days=30)
            query = query.filter(Session.created_at >= cutoff)

    sessions = query.order_by(Session.created_at.desc()).all()
    total_sessions = len(sessions)

    # Collect reports and scores
    reports = []
    session_scores = []

    for s in sessions:
        artifact = db.query(SessionArtifact).filter(SessionArtifact.session_id == s.id).first()
        if artifact and artifact.evaluation_report:
            rep = artifact.evaluation_report
            reports.append(rep)
            score = rep.get("overall_technical_score", 0)
            session_scores.append({
                "session_id": s.id,
                "score": score,
                "created_at": s.created_at.isoformat()
            })

    completed_count = len(reports)

    if completed_count > 0:
        composite_score = round(sum(s["score"] for s in session_scores) / completed_count)
    else:
        composite_score = 0

    # Calculate trend percent comparing latest score vs baseline
    if completed_count >= 2:
        latest_score = session_scores[0]["score"]
        earliest_score = session_scores[-1]["score"]
        if earliest_score > 0:
            trend_percent = round(((latest_score - earliest_score) / earliest_score) * 100, 1)
        else:
            trend_percent = 0.0
    else:
        trend_percent = 0.0

    # Aggregate Skill Matrix across standard pillars
    pillar_totals = {
        "System Architecture": {"sum": 0, "count": 0},
        "Communication & Pacing": {"sum": 0, "count": 0},
        "Problem Solving & Tradeoffs": {"sum": 0, "count": 0},
        "Code Quality & Professionalism": {"sum": 0, "count": 0},
    }

    for rep in reports:
        pillars = rep.get("technical_pillars", [])
        for p in pillars:
            p_name = p.get("pillar_name", "System Architecture")
            p_score = p.get("score", 0)
            
            # Map dynamic pillar names to standard categories if needed
            matched = False
            for std_name in pillar_totals.keys():
                if std_name.lower() in p_name.lower() or p_name.lower() in std_name.lower():
                    pillar_totals[std_name]["sum"] += p_score
                    pillar_totals[std_name]["count"] += 1
                    matched = True
                    break
            if not matched:
                pillar_totals["System Architecture"]["sum"] += p_score
                pillar_totals["System Architecture"]["count"] += 1

        # Also blend vocal confidence into Communication & Pacing if present
        vocal_score = rep.get("overall_vocal_confidence_score")
        if vocal_score is not None:
            pillar_totals["Communication & Pacing"]["sum"] += vocal_score
            pillar_totals["Communication & Pacing"]["count"] += 1

    skill_matrix = []
    strongest_area = "N/A - Complete practice track"
    highest_avg = -1

    for name, data in pillar_totals.items():
        if data["count"] > 0:
            avg = round(data["sum"] / data["count"])
        else:
            avg = composite_score if completed_count > 0 else 0

        color = "#22c55e" if avg >= 80 else "#65597b"
        skill_matrix.append(SkillMatrixItem(name=name, score=avg, color=color))

        if avg > highest_avg and data["count"] > 0:
            highest_avg = avg
            strongest_area = name

    if strongest_area == "N/A - Complete practice track" and completed_count > 0:
        strongest_area = "System Architecture & Problem Solving"

    # Synthesize Eva's Insights from latest evaluation reports
    insights = []
    if completed_count > 0:
        latest_rep = reports[0]
        feedback = latest_rep.get("candidate_feedback", {})
        strengths = feedback.get("key_strengths", [])
        growth_areas = feedback.get("primary_growth_areas", [])
        exec_summary = latest_rep.get("executive_summary", "")

        insight_id = 1
        if strengths:
            insights.append(InsightItem(
                id=insight_id,
                type="positive",
                text=f"Key Strength: {strengths[0]}"
            ))
            insight_id += 1

        if growth_areas:
            insights.append(InsightItem(
                id=insight_id,
                type="warning",
                text=f"Growth Focus: {growth_areas[0]}"
            ))
            insight_id += 1

        if len(strengths) > 1:
            insights.append(InsightItem(
                id=insight_id,
                type="positive",
                text=f"Demonstrated Competency: {strengths[1]}"
            ))
        elif exec_summary:
            insights.append(InsightItem(
                id=insight_id,
                type="positive",
                text=exec_summary[:160] + "..." if len(exec_summary) > 160 else exec_summary
            ))
    else:
        insights = [
            InsightItem(
                id=1,
                type="positive",
                text="Welcome to Netran AI! Complete your first practice track to unlock real-time performance analytics."
            ),
            InsightItem(
                id=2,
                type="warning",
                text="No completed interview sessions found in this time window. Launch a practice session from the Dashboard."
            ),
        ]

    # Session Comparison (last 5 sessions chronologically S1..S5)
    recent_chronological = list(reversed(session_scores[:5]))
    session_comparison = []

    if recent_chronological:
        for idx, item in enumerate(recent_chronological):
            label = f"S{idx + 1}"
            is_active = (idx == len(recent_chronological) - 1)
            session_comparison.append(SessionComparisonItem(
                label=label,
                score=item["score"],
                active=is_active,
                created_at=item["created_at"]
            ))
    else:
        # Default placeholder bars for fresh user
        session_comparison = [
            SessionComparisonItem(label="S1", score=0, active=False),
            SessionComparisonItem(label="S2", score=0, active=False),
            SessionComparisonItem(label="S3", score=0, active=False),
            SessionComparisonItem(label="S4", score=0, active=False),
            SessionComparisonItem(label="S5", score=0, active=True),
        ]

    return AnalyticsSummaryResponse(
        time_range=time_range,
        composite_score=composite_score,
        total_sessions=total_sessions,
        trend_percent=trend_percent,
        strongest_area=strongest_area,
        insights=insights,
        skill_matrix=skill_matrix,
        session_comparison=session_comparison
    )
