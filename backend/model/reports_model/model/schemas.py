"""
Netran AI — Stage 4: Post-Session Multimodal Evaluation & Report Generation Engine
Module: schemas.py
Description: Pydantic v2 data models enforcing output structures for candidate report payloads.
"""

from pydantic import BaseModel, Field


class TurnTelemetry(BaseModel):
    initial_silence_latency_ms: int = Field(default=0, description="Exact delay in ms before the candidate spoke after question completion.")
    turn_duration_sec: float = Field(default=0.0, description="Total turn audio clip duration in seconds.")
    stt_whisper_hallucination_flag: bool = Field(default=False, description="True if local STT text significantly diverges from audio waveform.")


class TurnAnalysis(BaseModel):
    turn_id: int = Field(description="Sequential turn identifier starting from 1.")
    question_text: str = Field(description="The question asked by the interviewer.")
    candidate_transcript: str = Field(description="Original transcript recorded during the interview session.")
    gemini_verified_transcript: str = Field(description="Transcript verified/corrected by Gemini from continuous audio waveform.")
    telemetry: TurnTelemetry = Field(default_factory=TurnTelemetry, description="Precision time and STT discrepancy metrics from Stage 3 manifest.")
    technical_score: int = Field(ge=1, le=10, description="Technical accuracy score from 1 (poor) to 10 (excellent).")
    vocal_confidence_score: int = Field(ge=1, le=10, description="Vocal confidence score from 1 (timid/hesitant) to 10 (assertive/fluent).")
    hesitation_level: str = Field(description="Observed hesitation level: 'Low', 'Medium', or 'High'.")
    emotional_state: str = Field(description="Primary vocal emotion: 'Calm', 'Stressed', 'Uncertain', or 'Confident'.")
    filler_word_count: int = Field(ge=0, description="Estimated count of filler words (e.g., um, ah, like, you know).")
    missing_concepts: list[str] = Field(default_factory=list, description="Key technical concepts missing from the candidate's response.")
    audio_notes: str = Field(description="Specific qualitative feedback on candidate's vocal tone, pacing, and speech delivery.")
    resume_verification_note: str | None = Field(default=None, description="Assessment of whether the candidate's response supports or contradicts their stated resume experience.")


class PillarScore(BaseModel):
    pillar_name: str = Field(description="Name of technical evaluation pillar (e.g., 'Frontend Architecture', 'React Internals').")
    score: int = Field(ge=0, le=100, description="Aggregated score out of 100 for this domain pillar.")
    summary: str = Field(description="Detailed performance summary for this pillar.")


class BehavioralFlag(BaseModel):
    type: str = Field(description="Flag type, e.g., 'SESSION_ABORT_REQUEST', 'STT_AUDIO_DISCREPANCY', 'HIGH_HESITATION'.")
    severity: str = Field(description="Severity level: 'CRITICAL', 'HIGH', 'MEDIUM', or 'LOW'.")
    turn_id: int = Field(description="Turn ID where the behavioral event occurred.")
    description: str = Field(description="Concise description of observed behavior or discrepancy.")


class CandidateFeedback(BaseModel):
    key_strengths: list[str] = Field(default_factory=list, description="Candidate's top technical and behavioral strengths.")
    primary_growth_areas: list[str] = Field(default_factory=list, description="Core technical concepts or communication skills requiring growth.")
    recommended_topics_to_study: list[str] = Field(default_factory=list, description="Specific architectural topics, frameworks, or papers recommended for study.")


class AudioBranchOutput(BaseModel):
    turn_id: int
    gemini_verified_transcript: str
    vocal_confidence_score: int = Field(ge=1, le=10)
    hesitation_level: str
    emotional_state: str
    filler_word_count: int
    audio_notes: str


class TechnicalBranchOutput(BaseModel):
    turn_id: int
    technical_score: int = Field(ge=1, le=10)
    missing_concepts: list[str]
    technical_notes: str
    resume_verification_note: str | None = None


class CandidateReportPayload(BaseModel):
    session_id: str = Field(description="Unique session identifier.")
    generated_at: str = Field(description="ISO timestamp when the report was synthesized.")
    overall_hiring_signal: str = Field(description="Overall recommendation: 'Strong Hire', 'Hire', 'Lean No Hire', or 'No Hire'.")
    overall_technical_score: int = Field(ge=0, le=100, description="Aggregated overall technical score across all turns.")
    overall_vocal_confidence_score: int = Field(ge=0, le=100, description="Aggregated overall vocal delivery score across all turns.")
    technical_pillars: list[PillarScore] = Field(default_factory=list, description="Domain-specific score breakdowns.")
    behavioral_flags: list[BehavioralFlag] = Field(default_factory=list, description="Observed behavioral red flags, abort requests, or STT discrepancies.")
    candidate_feedback: CandidateFeedback = Field(default_factory=CandidateFeedback, description="Structured roadmap for candidate growth and upskilling.")
    turn_evaluations: list[TurnAnalysis] = Field(default_factory=list, description="Detailed per-turn evaluation items.")
    executive_summary: str = Field(description="High-level narrative summary of candidate performance for hiring managers.")
