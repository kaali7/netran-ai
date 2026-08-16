"""
Netran AI — Document Ingestion Router (Resume & JD Parsing).
"""

from fastapi import APIRouter, Depends, status, HTTPException
from api.models import User
from api.dependencies import get_current_user

router = APIRouter(prefix="/ingest", tags=["Document Ingestion"])


@router.post("/resume")
def ingest_resume(current_user: User = Depends(get_current_user)):
    """Upload and parse candidate resume (.pdf, .docx, .txt)."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Resume ingestion endpoint stub — to be implemented in next step."
    )


@router.post("/jd")
def ingest_jd(current_user: User = Depends(get_current_user)):
    """Ingest and normalize raw Job Description text."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="JD ingestion endpoint stub — to be implemented in next step."
    )
