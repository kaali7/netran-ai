"""
Netran AI — Candidate Notification Router.
Provides real-time DB-backed notifications for interview setup, evaluation reports, and system announcements.
"""

import logging
from typing import Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session as DBSession

from api.db import get_db
from api.models import User, Notification
from api.schemas import (
    NotificationItem,
    NotificationListResponse,
    NotificationMarkReadResponse,
)
from api.dependencies import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("", response_model=NotificationListResponse, summary="List Candidate Notifications")
def list_notifications(
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    """Retrieve all notifications for the authenticated candidate, auto-seeding a welcome message if empty."""
    user_notifications = (
        db.query(Notification)
        .filter(Notification.user_id == current_user.id)
        .order_by(Notification.created_at.desc())
        .limit(50)
        .all()
    )

    # Auto-seed friendly welcome notification if the user has 0 notifications
    if not user_notifications:
        candidate_name = current_user.display_name or (current_user.email.split("@")[0].title() if current_user.email else "Candidate")
        welcome_notif = Notification(
            user_id=current_user.id,
            title=f"Welcome to Netran AI, {candidate_name}!",
            message="Your candidate profile is active. Launch an instant practice mock or configure a custom practice track to get started.",
            type="welcome",
            link="/setup",
            read=False,
            created_at=datetime.now(timezone.utc),
        )
        db.add(welcome_notif)
        db.commit()
        db.refresh(welcome_notif)
        user_notifications = [welcome_notif]

    unread_count = sum(1 for n in user_notifications if not n.read)

    return NotificationListResponse(
        notifications=user_notifications,
        unread_count=unread_count,
    )


@router.patch("/{notification_id}/read", response_model=NotificationItem, summary="Mark Single Notification as Read")
def mark_notification_read(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    """Mark a specific notification as read."""
    notif = (
        db.query(Notification)
        .filter(Notification.id == notification_id, Notification.user_id == current_user.id)
        .first()
    )
    if not notif:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found.",
        )

    notif.read = True
    db.add(notif)
    db.commit()
    db.refresh(notif)
    return notif


@router.post("/mark-all-read", response_model=NotificationMarkReadResponse, summary="Mark All Notifications as Read")
def mark_all_notifications_read(
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    """Mark all candidate notifications as read."""
    db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.read == False
    ).update({"read": True})
    db.commit()

    return NotificationMarkReadResponse(
        message="All notifications marked as read.",
        unread_count=0,
    )


@router.delete("/{notification_id}", summary="Delete Single Notification")
def delete_notification(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    """Delete a specific notification from candidate history."""
    notif = (
        db.query(Notification)
        .filter(Notification.id == notification_id, Notification.user_id == current_user.id)
        .first()
    )
    if not notif:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found.",
        )

    db.delete(notif)
    db.commit()
    return {"message": "Notification deleted successfully."}
