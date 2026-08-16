"""
Netran AI — Pydantic v2 Serialization & Request/Response Schemas.
"""

from typing import Optional, Any
from datetime import datetime
from pydantic import BaseModel, EmailStr, ConfigDict
from api.models import UserRole, SessionStatus


# --- Auth Schemas ---

class UserCreate(BaseModel):
    """User signup request payload."""
    email: EmailStr
    password: str
    role: Optional[UserRole] = UserRole.CANDIDATE


class UserLogin(BaseModel):
    """User login request payload."""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """User profile response schema."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: EmailStr
    role: UserRole
    created_at: datetime


class TokenResponse(BaseModel):
    """OAuth2 JWT token response."""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenData(BaseModel):
    """JWT payload data structure."""
    user_id: Optional[str] = None
    role: Optional[str] = None


# --- Session Schemas ---

class SessionCreate(BaseModel):
    """Session initialization request payload."""
    resume_hash: Optional[str] = None
    jd_hash: Optional[str] = None


class SessionResponse(BaseModel):
    """Interview session metadata response."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    resume_hash: Optional[str] = None
    jd_hash: Optional[str] = None
    status: SessionStatus
    created_at: datetime


class SessionArtifactsResponse(BaseModel):
    """Session artifacts response payload."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    session_id: str
    parsed_resume: Optional[dict[str, Any]] = None
    parsed_jd: Optional[dict[str, Any]] = None
    jd_detail: Optional[dict[str, Any]] = None
    resume_analysis: Optional[dict[str, Any]] = None
    interview_behavior: Optional[dict[str, Any]] = None
    question_tree: Optional[dict[str, Any]] = None
    transcript: Optional[dict[str, Any]] = None
    evaluation_report: Optional[dict[str, Any]] = None


# --- Common Schemas ---

class HealthResponse(BaseModel):
    """API gateway status response."""
    status: str = "ok"
    version: str
    project: str
