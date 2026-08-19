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
    raw_jd_text: Optional[str] = None



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


# --- Setup & Pipeline Schemas ---

class AnalyzeRequest(BaseModel):
    """Request to trigger Stage 1 & Stage 2 pipeline analysis."""
    session_id: str
    target_seniority: Optional[str] = "Senior"
    force_refresh: Optional[bool] = False


class AnalyzeStatusResponse(BaseModel):
    """Immediate response after triggering background pipeline analysis."""
    session_id: str
    status: SessionStatus = SessionStatus.ANALYZING
    progress_message: str = "Starting pipeline..."
    message: str = "Pipeline analysis started in background."


class SessionStatusResponse(BaseModel):
    """Status polling response for interview setup pipeline."""
    session_id: str
    status: SessionStatus
    progress_message: Optional[str] = None


class QuestionPreviewResponse(BaseModel):
    """Response payload containing generated 15-question tree & interviewer behavior prompt."""
    session_id: str
    status: SessionStatus
    total_questions: int
    question_tree: list[dict[str, Any]]
    resume_analysis: Optional[dict[str, Any]] = None
    interview_behavior: Optional[dict[str, Any]] = None
    jd_detail: Optional[dict[str, Any]] = None
    cached: bool = False


# --- Stage 3 Voice WS Schemas ---

class VoiceTurnEvent(BaseModel):
    """WebSocket JSON frame sent to client during live voice interview."""
    event: str  # CONNECTED, SPEAKING_QUESTION, LISTENING_CANDIDATE, PROCESSING_RESPONSE, EVA_RESPONDING_BRANCH, TURN_COMPLETE, INTERVIEW_COMPLETE, ERROR
    session_id: str
    turn_id: int = 0
    topic: Optional[str] = None
    question_text: Optional[str] = None
    candidate_transcript: Optional[str] = None
    eva_response: Optional[str] = None
    branch_taken: Optional[str] = None
    progress_pct: Optional[int] = None
    stt_latency_ms: Optional[float] = None
    ttft_ms: Optional[float] = None
    detail: Optional[str] = None  # for error messages


class VoiceSessionStatusResponse(BaseModel):
    """Initial check response before WebSocket connect."""
    session_id: str
    status: SessionStatus
    total_turns_completed: int = 0
    interview_started_at: Optional[datetime] = None


# --- Stage 4 Report Schemas ---

class ReportGenerateResponse(BaseModel):
    """Response returned when report generation background task is initiated."""
    session_id: str
    status: SessionStatus = SessionStatus.EVALUATING
    progress_message: str = "Stage 4: Post-session multimodal report generation started..."
    message: str = "Report generation triggered in background."


class ReportResponse(BaseModel):
    """Payload containing evaluation report JSON and session metadata."""
    session_id: str
    status: SessionStatus
    evaluation_report: Optional[dict[str, Any]] = None
    progress_message: Optional[str] = None


# --- Analytics Schemas ---

class InsightItem(BaseModel):
    """Insight callout entry for Eva's AI Synthesis."""
    id: int
    type: str  # "positive" | "warning"
    text: str


class SkillMatrixItem(BaseModel):
    """Single pillar score entry for Aggregated Skill Matrix."""
    name: str
    score: int
    color: Optional[str] = "#65597b"


class SessionComparisonItem(BaseModel):
    """Session comparison entry for score trend chart."""
    label: str
    score: int
    active: bool = False
    created_at: Optional[str] = None


class AnalyticsSummaryResponse(BaseModel):
    """Aggregated candidate performance analytics response payload."""
    time_range: str
    composite_score: int
    total_sessions: int
    trend_percent: float
    strongest_area: str
    insights: list[InsightItem]
    skill_matrix: list[SkillMatrixItem]
    session_comparison: list[SessionComparisonItem]


# --- History Schemas ---

class HistorySessionItem(BaseModel):
    """Summarized session row for history archive table."""
    id: str
    created_at: datetime
    date_text: str
    status: SessionStatus
    track: str
    role_title: str
    company: Optional[str] = "Tech Corporation"
    score: Optional[int] = None
    hiring_signal: Optional[str] = None
    duration_text: str = "18m 42s"
    total_questions: int = 15
    has_report: bool = False
    has_recording: bool = False


class HistoryListResponse(BaseModel):
    """Response containing list of candidate history sessions."""
    total: int
    sessions: list[HistorySessionItem]


class HistorySessionDetailResponse(BaseModel):
    """Detailed view payload for question tree & resume analysis inspection modal."""
    session_id: str
    status: SessionStatus
    created_at: datetime
    role_title: str
    company: Optional[str] = None
    seniority_level: Optional[str] = None
    question_tree: list[dict[str, Any]] = []
    resume_analysis: Optional[dict[str, Any]] = None
    evaluation_report: Optional[dict[str, Any]] = None
    parsed_jd: Optional[dict[str, Any]] = None
    parsed_resume: Optional[dict[str, Any]] = None
    has_recording: bool = False


# --- Common Schemas ---

class HealthResponse(BaseModel):
    """API gateway status response."""
    status: str = "ok"
    version: str
    project: str

