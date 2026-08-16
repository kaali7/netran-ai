"""
Netran AI — Document Ingestion Router (Resume & JD Parsing).
Handles resume file uploads and job description text ingestion,
extracting structured JSON payloads via Gemini and persisting to SQLite.
"""

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session as DBSession

from api.db import get_db
from api.models import User, Session as SessionModel, SessionArtifact, SessionStatus
from api.schemas import (
    IngestResumeResponse,
    IngestJDRequest,
    IngestJDResponse,
    CandidateProfile,
    ParsedJD,
)
from api.dependencies import get_current_user
from api.services import text_extractor, gemini_extractor, cache

router = APIRouter(prefix="/ingest", tags=["Document Ingestion"])

# Max upload size: 10 MB
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024


@router.post(
    "/resume",
    response_model=IngestResumeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload & Parse Resume",
    description=(
        "Upload a candidate resume in `.pdf`, `.docx`, `.txt`, or `.tex` format. "
        "The file is parsed via Gemini into a structured `CandidateProfile` JSON and "
        "persisted to SQLite. Duplicate uploads (same SHA-256) return the cached result "
        "without a Gemini API call."
    ),
)
async def ingest_resume(
    file: UploadFile = File(..., description="Resume file (.pdf, .docx, .txt, .tex)"),
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
) -> IngestResumeResponse:
    """Upload and parse a candidate resume into a structured CandidateProfile."""

    # ── 1. Read and validate file size ──────────────────────────────────────
    file_bytes = await file.read()
    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds the 10 MB limit. Received: {len(file_bytes) / 1024 / 1024:.1f} MB",
        )
    if len(file_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Uploaded file is empty.",
        )

    # ── 2. Extract raw text by file type ────────────────────────────────────
    raw_text = text_extractor.extract_text(file.filename or "resume.txt", file_bytes)

    # ── 3. Compute SHA-256 hash & check cache ───────────────────────────────
    resume_hash = cache.compute_hash(raw_text)
    cached_result = cache.lookup_resume_cache(db, resume_hash)

    if cached_result:
        # Return existing session for this hash
        existing_session = (
            db.query(SessionModel)
            .filter(SessionModel.resume_hash == resume_hash)
            .order_by(SessionModel.created_at.desc())
            .first()
        )
        return IngestResumeResponse(
            session_id=existing_session.id,
            resume_hash=resume_hash,
            parsed_resume=CandidateProfile(**cached_result),
            cached=True,
            message="Resume already parsed. Returning cached result.",
        )

    # ── 4. Call Gemini for structured extraction ─────────────────────────────
    parsed_dict = gemini_extractor.parse_resume(raw_text)

    # ── 5. Persist: Create new Session + SessionArtifact ────────────────────
    new_session = SessionModel(
        user_id=current_user.id,
        resume_hash=resume_hash,
        status=SessionStatus.SETUP,
    )
    db.add(new_session)
    db.flush()  # Get session ID without full commit

    artifact = SessionArtifact(
        session_id=new_session.id,
        parsed_resume=parsed_dict,
    )
    db.add(artifact)
    db.commit()
    db.refresh(new_session)

    return IngestResumeResponse(
        session_id=new_session.id,
        resume_hash=resume_hash,
        parsed_resume=CandidateProfile(**parsed_dict),
        cached=False,
        message="Resume parsed and saved successfully.",
    )


@router.post(
    "/jd",
    response_model=IngestJDResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest & Parse Job Description",
    description=(
        "Submit raw job description text (paste from job posting). "
        "Gemini extracts a structured `ParsedJD` schema and attaches it to an "
        "existing session (by `session_id`) or the user's latest SETUP session. "
        "Duplicate JD text (same SHA-256) returns the cached result."
    ),
)
def ingest_jd(
    request: IngestJDRequest,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
) -> IngestJDResponse:
    """Ingest raw job description text and extract a structured ParsedJD schema."""

    raw_jd_text = request.raw_jd_text.strip()
    if not raw_jd_text:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="JD text cannot be empty.",
        )
    if len(raw_jd_text) < 50:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="JD text is too short. Please paste the full job description.",
        )

    # ── 1. Compute SHA-256 hash & check cache ───────────────────────────────
    jd_hash = cache.compute_hash(raw_jd_text)
    cached_result = cache.lookup_jd_cache(db, jd_hash)

    # ── 2. Resolve target session ────────────────────────────────────────────
    target_session: SessionModel | None = None

    if request.session_id:
        # Explicit session_id provided
        target_session = (
            db.query(SessionModel)
            .filter(
                SessionModel.id == request.session_id,
                SessionModel.user_id == current_user.id,
            )
            .first()
        )
        if not target_session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session '{request.session_id}' not found or does not belong to you.",
            )
    else:
        # Auto-attach to latest SETUP session
        target_session = cache.find_latest_setup_session(db, current_user.id)

    # ── 3. Return cached result if hash already stored ───────────────────────
    if cached_result:
        existing_session = (
            db.query(SessionModel)
            .filter(SessionModel.jd_hash == jd_hash)
            .order_by(SessionModel.created_at.desc())
            .first()
        )
        return IngestJDResponse(
            session_id=existing_session.id,
            jd_hash=jd_hash,
            parsed_jd=ParsedJD(**cached_result),
            cached=True,
            message="JD already parsed. Returning cached result.",
        )

    # ── 4. Call Gemini for structured extraction ─────────────────────────────
    parsed_dict = gemini_extractor.parse_jd(raw_jd_text)

    # ── 5. Persist: Update existing session or create new one ────────────────
    if target_session:
        # Update existing session with jd_hash
        target_session.jd_hash = jd_hash
        db.flush()

        if target_session.artifacts:
            target_session.artifacts.parsed_jd = parsed_dict
        else:
            artifact = SessionArtifact(
                session_id=target_session.id,
                parsed_jd=parsed_dict,
            )
            db.add(artifact)

        db.commit()
        db.refresh(target_session)

        return IngestJDResponse(
            session_id=target_session.id,
            jd_hash=jd_hash,
            parsed_jd=ParsedJD(**parsed_dict),
            cached=False,
            message="JD parsed and attached to existing session.",
        )
    else:
        # No existing session; create a new one
        new_session = SessionModel(
            user_id=current_user.id,
            jd_hash=jd_hash,
            status=SessionStatus.SETUP,
        )
        db.add(new_session)
        db.flush()

        artifact = SessionArtifact(
            session_id=new_session.id,
            parsed_jd=parsed_dict,
        )
        db.add(artifact)
        db.commit()
        db.refresh(new_session)

        return IngestJDResponse(
            session_id=new_session.id,
            jd_hash=jd_hash,
            parsed_jd=ParsedJD(**parsed_dict),
            cached=False,
            message="JD parsed and saved to a new session.",
        )
