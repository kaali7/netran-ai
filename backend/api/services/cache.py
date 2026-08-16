"""
Netran AI — SHA-256 Cache Lookup Service.
Prevents redundant Gemini API calls for duplicate resume/JD uploads
using SHA-256 fingerprinting stored in the sessions table.
"""

import hashlib
from typing import Optional
from sqlalchemy.orm import Session as DBSession
from api.models import Session, SessionArtifact


def compute_hash(text: str) -> str:
    """
    Compute a SHA-256 hex digest of the given string.

    Args:
        text: Input text to hash (raw resume or JD text).

    Returns:
        str: 64-character lowercase hex SHA-256 digest.
    """
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def lookup_resume_cache(db: DBSession, hash_str: str) -> Optional[dict]:
    """
    Check if a parsed resume result already exists for this SHA-256 hash.

    Args:
        db: Active SQLAlchemy database session.
        hash_str: SHA-256 hash of the raw resume text.

    Returns:
        dict | None: Cached parsed_resume JSON if found, else None.
    """
    session_row = (
        db.query(Session)
        .filter(Session.resume_hash == hash_str)
        .first()
    )
    if session_row and session_row.artifacts and session_row.artifacts.parsed_resume:
        return session_row.artifacts.parsed_resume
    return None


def lookup_jd_cache(db: DBSession, hash_str: str) -> Optional[dict]:
    """
    Check if a parsed JD result already exists for this SHA-256 hash.

    Args:
        db: Active SQLAlchemy database session.
        hash_str: SHA-256 hash of the raw JD text.

    Returns:
        dict | None: Cached parsed_jd JSON if found, else None.
    """
    session_row = (
        db.query(Session)
        .filter(Session.jd_hash == hash_str)
        .first()
    )
    if session_row and session_row.artifacts and session_row.artifacts.parsed_jd:
        return session_row.artifacts.parsed_jd
    return None


def find_latest_setup_session(db: DBSession, user_id: str) -> Optional[Session]:
    """
    Find the most recent SETUP-status session for a given user (for JD attachment).

    Args:
        db: Active SQLAlchemy database session.
        user_id: User UUID string.

    Returns:
        Session | None: Latest SETUP session or None if not found.
    """
    from api.models import SessionStatus
    return (
        db.query(Session)
        .filter(Session.user_id == user_id, Session.status == SessionStatus.SETUP)
        .order_by(Session.created_at.desc())
        .first()
    )
