"""
Netran AI — Stage 1 & Stage 2 Background Pipeline Runner.
Orchestrates Tavily research synthesis (Stage 1) and 15-question tree generation (Stage 2),
updating session progress_message and persisting artifacts to SQLite.
"""

import json
import logging
import os

from api.config import settings, BASE_DIR
from api.db import SessionLocal
from api.models import Session, SessionArtifact, SessionStatus

logger = logging.getLogger(__name__)


def _update_progress(db, session_id: str, message: str, status: SessionStatus | None = None):
    """Update progress_message and optional status in the database."""
    try:
        session_row = db.query(Session).filter(Session.id == session_id).first()
        if session_row:
            session_row.progress_message = message
            if status is not None:
                session_row.status = status
            db.commit()
            logger.info(f"[{session_id}] {message}")
    except Exception as exc:
        logger.error(f"Failed to update progress for session '{session_id}': {exc}")
        db.rollback()


def run_stage1_and_stage2(
    session_id: str,
    target_seniority: str = "Senior",
    force_refresh: bool = False,
):
    """
    Background worker function running Stage 1 and Stage 2 engines sequentially.

    Args:
        session_id: Target interview session UUID.
        target_seniority: Target role level ("Junior", "Mid", "Senior", "Lead", "Staff").
        force_refresh: If True, bypasses Stage 1 & Stage 2 caches.
    """
    db = SessionLocal()
    try:
        # ── 1. Fetch Session and SessionArtifact ──────────────────────────────
        session_row = db.query(Session).filter(Session.id == session_id).first()
        if not session_row:
            logger.error(f"Pipeline runner error: Session '{session_id}' not found.")
            return

        artifact = session_row.artifacts
        if not artifact or not artifact.parsed_jd or not artifact.parsed_resume:
            _update_progress(
                db,
                session_id,
                "Pipeline failed: Missing parsed JD or parsed resume artifact.",
                status=SessionStatus.SETUP,
            )
            return

        # ── 2. Run Stage 1 (JD Research & Tavily Market Intel Synthesis) ────────
        _update_progress(db, session_id, "Stage 1: Parsing job description with Gemini...")

        # Extract JD text from parsed_jd or fallback string
        parsed_jd = artifact.parsed_jd
        if isinstance(parsed_jd, dict):
            raw_jd_text = parsed_jd.get("raw_jd_text") or json.dumps(parsed_jd)
        else:
            raw_jd_text = str(parsed_jd)

        _update_progress(
            db,
            session_id,
            "Stage 1: Running Tavily multi-vector web search (market intelligence)...",
        )

        from model.research_model.model.pipeline import Stage1Pipeline
        from model.research_model.model.config import Stage1Config

        s1_config = Stage1Config(
            gemini_api_key=settings.GEMINI_API_KEY,
            gemini_model=settings.GEMINI_MODEL,
            tavily_api_key=settings.TAVILY_API_KEY,
        )
        s1_pipeline = Stage1Pipeline(config=s1_config)

        s1_output = s1_pipeline.run(
            jd_text=raw_jd_text,
            force_refresh=force_refresh,
        )

        rubric_dict = s1_output.rubric.model_dump()
        artifact.jd_detail = rubric_dict
        db.commit()

        _update_progress(
            db,
            session_id,
            "Stage 1: Research complete. Building candidate resume context file...",
        )

        # ── 3. Prepare resume context file for Stage 2 ────────────────────────
        session_dir = os.path.join(BASE_DIR, "data", "sessions", session_id)
        os.makedirs(session_dir, exist_ok=True)
        temp_resume_path = os.path.join(session_dir, "resume_parsed.json")

        parsed_resume = artifact.parsed_resume
        with open(temp_resume_path, "w", encoding="utf-8") as f:
            if isinstance(parsed_resume, dict):
                json.dump(parsed_resume, f, indent=2)
            else:
                f.write(str(parsed_resume))

        # ── 4. Run Stage 2 (15-Question Tree & Behavioral System Prompt) ────────
        _update_progress(
            db,
            session_id,
            "Stage 2: Generating 15-question interview tree and voice system prompt...",
        )

        from model.question_model.model.pipeline import Stage2Pipeline
        from model.question_model.model.config import Stage2Config

        s2_config = Stage2Config(
            gemini_api_key=settings.GEMINI_API_KEY,
            gemini_model=settings.GEMINI_MODEL,
        )
        s2_pipeline = Stage2Pipeline(config=s2_config)

        s2_output = s2_pipeline.run(
            session_id=session_id,
            jd_input=rubric_dict,
            resume_path=temp_resume_path,
            target_seniority=target_seniority,
        )

        # ── 5. Persist Stage 2 outputs to SQLite ──────────────────────────────
        _update_progress(db, session_id, "Stage 2: Saving question tree & behavior prompt...")

        artifact.resume_analysis = s2_output.resume_analysis.model_dump()
        artifact.interview_behavior = s2_output.interviewer_behavior.model_dump()
        artifact.question_tree = [
            q.model_dump() for q in s2_output.interview_questions
        ]

        session_row.status = SessionStatus.READY
        session_row.progress_message = "Pipeline complete! Interview ready."
        db.commit()

        logger.info(
            f"Pipeline successfully completed for session '{session_id}'. "
            f"Generated {len(s2_output.interview_questions)} questions."
        )

    except Exception as exc:
        logger.exception(f"Pipeline execution failed for session '{session_id}': {exc}")
        db.rollback()
        _update_progress(
            db,
            session_id,
            f"Pipeline failed: {str(exc)[:200]}",
            status=SessionStatus.SETUP,
        )
    finally:
        db.close()
