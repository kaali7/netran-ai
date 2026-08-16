"""
Netran AI — Stage 4 Multimodal Reports Router.
Triggers evaluation and fetches session reports.
"""

from fastapi import APIRouter, Depends, status, HTTPException
from api.models import User
from api.dependencies import get_current_user

router = APIRouter(prefix="/reports", tags=["Evaluation & Reports"])


@router.post("/generate/{session_id}")
def generate_report(session_id: str, current_user: User = Depends(get_current_user)):
    """Trigger Stage 4 multimodal evaluation background task."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Report generation endpoint stub — to be implemented in next step."
    )


@router.get("/{session_id}")
def get_report(session_id: str, current_user: User = Depends(get_current_user)):
    """Fetch completed evaluation report JSON & Markdown summary."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Get report endpoint stub — to be implemented in next step."
    )
