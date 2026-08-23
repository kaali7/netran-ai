"""
Netran AI — Template Mock Interview Router.

Provides pre-built interview templates (Backend, Frontend, Fullstack) that allow
candidates to start a full 15-question mock interview without uploading a resume or JD.
Templates are loaded from backend/data/sample_interviews/ and hydrate a real DB session.
"""

import json
import uuid
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session as DBSession
from pydantic import BaseModel

from api.db import get_db
from api.models import User, Session as SessionModel, SessionStatus, SessionArtifact
from api.dependencies import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/template", tags=["Template Mock Interview"])

# ── Canonical template data directory ──────────────────────────────────────────
TEMPLATES_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "sample_interviews"

# ── Template metadata catalog ──────────────────────────────────────────────────
TEMPLATE_CATALOG = [
    {
        "id": "backend",
        "title": "Backend Engineer",
        "target_role": "Senior Backend Systems Engineer",
        "description": "Deep-dive into distributed systems, Python microservices, PostgreSQL, Redis, Kafka, and API design patterns.",
        "difficulty": "Hard",
        "question_count": 15,
        "tech_stack": ["Python", "FastAPI", "PostgreSQL", "Redis", "Kafka", "Docker"],
        "icon": "⚙️",
        "color": "#4f46e5",
        "folder": "backend",
    },
    {
        "id": "frontend",
        "title": "Frontend Engineer",
        "target_role": "Senior Frontend Engineer",
        "description": "Cover React, Next.js, TypeScript, Core Web Vitals, SSR/SSG, micro-frontends, and performance optimization.",
        "difficulty": "Medium",
        "question_count": 15,
        "tech_stack": ["React", "Next.js", "TypeScript", "CSS", "Vite", "Jest"],
        "icon": "🎨",
        "color": "#0891b2",
        "folder": "frontend",
    },
    {
        "id": "fullstack",
        "title": "Full Stack AI Engineer",
        "target_role": "Full Stack AI Engineer",
        "description": "Explore React, FastAPI, PyTorch, LangChain, RAG pipelines, Vector DBs, and AI system integration patterns.",
        "difficulty": "Hard",
        "question_count": 15,
        "tech_stack": ["React", "FastAPI", "Python", "LangChain", "Qdrant", "Docker"],
        "icon": "🤖",
        "color": "#7c3aed",
        "folder": "fullstack",
    },
]

# ── Lookup map keyed by template_id ───────────────────────────────────────────
TEMPLATE_MAP = {t["id"]: t for t in TEMPLATE_CATALOG}


# ── Pydantic Schemas ──────────────────────────────────────────────────────────

class StartTemplateRequest(BaseModel):
    """Request payload to start a template mock interview session."""
    template_id: Literal["backend", "frontend", "fullstack"]


class StartTemplateResponse(BaseModel):
    """Response after successfully creating a template interview session."""
    session_id: str
    template_id: str
    target_role: str
    status: str
    message: str


# ── Helpers ───────────────────────────────────────────────────────────────────

def _load_template_json(folder: str, filename: str) -> dict | list:
    """Load and parse a JSON file from the template data directory."""
    filepath = TEMPLATES_DIR / folder / filename
    if not filepath.exists():
        raise FileNotFoundError(f"Template file not found: {filepath}")
    with filepath.open("r", encoding="utf-8") as f:
        return json.load(f)


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get(
    "/list",
    summary="List Available Mock Interview Templates",
    description="Returns metadata for all pre-built mock interview templates available without resume/JD upload.",
)
def list_templates():
    """Return all available interview template packs."""
    # Return catalog without internal 'folder' key (not needed by frontend)
    public_catalog = []
    for t in TEMPLATE_CATALOG:
        public_catalog.append({k: v for k, v in t.items() if k != "folder"})
    return {"templates": public_catalog, "total": len(public_catalog)}


@router.post(
    "/start",
    response_model=StartTemplateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start a Template Mock Interview Session",
    description=(
        "Creates a real DB session pre-loaded with the selected template's question tree, "
        "interviewer behavior, and resume analysis. The session is immediately in READY status "
        "and can be connected to via the WebSocket voice interview endpoint."
    ),
)
def start_template_session(
    request: StartTemplateRequest,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
) -> StartTemplateResponse:
    """Create a pre-hydrated interview session from a template pack."""

    template_meta = TEMPLATE_MAP.get(request.template_id)
    if not template_meta:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown template_id '{request.template_id}'. Valid options: backend, frontend, fullstack.",
        )

    folder = template_meta["folder"]

    # ── 1. Load the three template JSON files ──────────────────────────────────
    try:
        questions = _load_template_json(folder, "interview_questions.json")
        behavior = _load_template_json(folder, "interviewer_behavior.json")
        resume_analysis = _load_template_json(folder, "resume_analysis.json")
    except FileNotFoundError as e:
        logger.error("Template file missing: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Template data files are missing for '{request.template_id}'. Contact support.",
        ) from e

    # ── 2. Determine Candidate Name & Personalize Artifacts ───────────────────
    candidate_name = (
        current_user.display_name.strip()
        if (current_user.display_name and current_user.display_name.strip())
        else (current_user.email.split("@")[0].replace(".", " ").title() if current_user.email else "Candidate")
    )

    if isinstance(behavior, dict):
        behavior["candidate_name"] = candidate_name
        behavior["session_id"] = session_id
        behavior["target_role"] = template_meta["target_role"]
        behavior["interviewer_system_prompt"] = (
            f"You are Eva, an Executive Technical Bar Raiser at Netran AI conducting a structured technical interview "
            f"for {candidate_name} for the {template_meta['target_role']} position. "
            f"Keep your responses ultra-concise, conversational, and direct (MAXIMUM 25 WORDS per turn). "
            f"Ask exactly one clear question at a time. Acknowledge candidate responses with brief vocal anchors "
            f"like 'Got it', 'Makes sense', or 'Understood', then bridge smoothly to the next question. "
            f"Maintain an encouraging yet precise, authoritative persona. Always end your response turn with a question tag ending with a question mark."
        )

    if isinstance(resume_analysis, dict):
        resume_analysis["candidate_name"] = candidate_name

    # ── 3. Create Session row ─────────────────────────────────────────────────
    session_row = SessionModel(
        id=session_id,
        user_id=current_user.id,
        status=SessionStatus.READY,
        progress_message=f"Template session ready — {template_meta['target_role']}",
        created_at=datetime.now(timezone.utc),
    )
    db.add(session_row)
    db.flush()  # Flush to get session_row.id for FK in artifact

    # ── 4. Create SessionArtifact pre-loaded with template data ───────────────
    artifact = SessionArtifact(
        session_id=session_id,
        question_tree=questions,
        interview_behavior=behavior,
        resume_analysis=resume_analysis,
        # Store template metadata in parsed_jd for dashboard title display
        parsed_jd={
            "role_title": template_meta["target_role"],
            "domain": template_meta["title"],
            "is_template": True,
            "template_id": request.template_id,
            "tech_stack": template_meta["tech_stack"],
        },
        parsed_resume={
            "candidate_name": candidate_name,
            "template_mode": True,
        },
    )
    db.add(artifact)
    db.commit()
    db.refresh(session_row)

    logger.info(
        "Template session created: %s | user=%s | template=%s",
        session_id, current_user.id, request.template_id
    )

    return StartTemplateResponse(
        session_id=session_id,
        template_id=request.template_id,
        target_role=template_meta["target_role"],
        status=SessionStatus.READY.value,
        message=f"Template interview session created and ready. Connect to /api/v1/voice/stream/{session_id}",
    )
