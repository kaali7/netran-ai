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


# --- Ingestion Schemas ---

class WorkExperience(BaseModel):
    """A single work history entry in a candidate profile."""
    company: Optional[str] = None
    role: Optional[str] = None
    duration: Optional[str] = None
    responsibilities: Optional[list[str]] = None


class Education(BaseModel):
    """A single education entry in a candidate profile."""
    degree: Optional[str] = None
    institution: Optional[str] = None
    year: Optional[str] = None
    gpa: Optional[str] = None


class CandidateProfile(BaseModel):
    """Structured candidate profile extracted from a resume."""
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    summary: Optional[str] = None
    technical_skills: Optional[list[str]] = None
    soft_skills: Optional[list[str]] = None
    work_history: Optional[list[WorkExperience]] = None
    education: Optional[list[Education]] = None
    projects: Optional[list[str]] = None
    certifications: Optional[list[str]] = None
    languages: Optional[list[str]] = None
    raw_text_length: Optional[int] = None


class ParsedJD(BaseModel):
    """Structured job description extracted from raw JD text."""
    role_title: Optional[str] = None
    company: Optional[str] = None
    seniority_level: Optional[str] = None
    employment_type: Optional[str] = None
    location: Optional[str] = None
    required_skills: Optional[list[str]] = None
    optional_skills: Optional[list[str]] = None
    responsibilities: Optional[list[str]] = None
    qualifications: Optional[list[str]] = None
    experience_years_min: Optional[int] = None
    experience_years_max: Optional[int] = None
    domain: Optional[str] = None
    raw_text_length: Optional[int] = None


class IngestJDRequest(BaseModel):
    """JD ingestion request: raw pasted job description text."""
    raw_jd_text: str
    session_id: Optional[str] = None  # Optional: attach to existing session


class IngestResumeResponse(BaseModel):
    """Response after resume upload and parsing."""
    session_id: str
    resume_hash: str
    parsed_resume: CandidateProfile
    cached: bool = False
    message: str = "Resume parsed successfully"


class IngestJDResponse(BaseModel):
    """Response after JD ingestion and parsing."""
    session_id: str
    jd_hash: str
    parsed_jd: ParsedJD
    cached: bool = False
    message: str = "Job description parsed successfully"



# --- Common Schemas ---

class HealthResponse(BaseModel):
    """API gateway status response."""
    status: str = "ok"
    version: str
    project: str
