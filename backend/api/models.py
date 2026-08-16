"""
Netran AI — SQLAlchemy ORM Models.
Defines Users, Sessions, and SessionArtifacts tables.
"""

import uuid
import enum
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Enum, ForeignKey, JSON
from sqlalchemy.orm import relationship
from api.db import Base


class UserRole(str, enum.Enum):
    """User role permissions."""
    CANDIDATE = "candidate"
    ADMIN = "admin"


class SessionStatus(str, enum.Enum):
    """Interview session operational lifecycle states."""
    SETUP = "setup"
    ANALYZING = "analyzing"
    READY = "ready"
    IN_PROGRESS = "in_progress"
    EVALUATING = "evaluating"
    COMPLETED = "completed"


def generate_uuid() -> str:
    """Generate string UUID."""
    return str(uuid.uuid4())


def utc_now() -> datetime:
    """Return timezone-aware current UTC time."""
    return datetime.now(timezone.utc)


class User(Base):
    """User account entity."""

    __tablename__ = "users"

    id = Column(String, primary_key=True, default=generate_uuid)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.CANDIDATE, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    # Relationships
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")


class Session(Base):
    """Interview session metadata entity."""

    __tablename__ = "sessions"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    resume_hash = Column(String, nullable=True, index=True)
    jd_hash = Column(String, nullable=True, index=True)
    status = Column(Enum(SessionStatus), default=SessionStatus.SETUP, nullable=False)
    progress_message = Column(String, nullable=True, default=None)
    created_at = Column(DateTime, default=utc_now, nullable=False)


    # Relationships
    user = relationship("User", back_populates="sessions")
    artifacts = relationship(
        "SessionArtifact",
        uselist=False,
        back_populates="session",
        cascade="all, delete-orphan"
    )


class SessionArtifact(Base):
    """Core stage JSON knowledge and output artifacts entity."""

    __tablename__ = "session_artifacts"

    id = Column(String, primary_key=True, default=generate_uuid)
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False, unique=True, index=True)

    parsed_resume = Column(JSON, nullable=True)
    parsed_jd = Column(JSON, nullable=True)
    jd_detail = Column(JSON, nullable=True)
    resume_analysis = Column(JSON, nullable=True)
    interview_behavior = Column(JSON, nullable=True)
    question_tree = Column(JSON, nullable=True)
    transcript = Column(JSON, nullable=True)
    evaluation_report = Column(JSON, nullable=True)

    # Relationships
    session = relationship("Session", back_populates="artifacts")
