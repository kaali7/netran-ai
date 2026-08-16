"""
Netran AI — Questions Preview Router.
Fetch generated interview questions and system persona.
"""

from fastapi import APIRouter, Depends, status, HTTPException
from api.models import User
from api.dependencies import get_current_user

router = APIRouter(prefix="/questions", tags=["Question Tree & Preview"])


@router.get("/preview/{session_id}")
def preview_questions(session_id: str, current_user: User = Depends(get_current_user)):
    """Fetch structured question tree and candidate breakdown for preview."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Question preview endpoint stub — to be implemented in next step."
    )
