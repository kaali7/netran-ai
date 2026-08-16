"""
Netran AI — Setup & Pipeline Analysis Router.
Triggers Stage 1 & Stage 2 processing.
"""

from fastapi import APIRouter, Depends, status, HTTPException
from api.models import User
from api.dependencies import get_current_user

router = APIRouter(prefix="/setup", tags=["Setup & Pipeline Analysis"])


@router.post("/analyze")
def trigger_analysis(current_user: User = Depends(get_current_user)):
    """Trigger background execution for Stage 1 (Research) & Stage 2 (Question Engine)."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Pipeline analysis endpoint stub — to be implemented in next step."
    )
