"""
Netran AI — Stage 4: Post-Session Multimodal Evaluation & Report Generation Engine
Module: report_schema.py
Description: Pydantic v2 data models enforcing output structures for candidate report payloads.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class TurnAnalysis(BaseModel):
    turn_id: int = Field(description="Sequential turn identifier starting from 1.")
    question_text: str = Field(description="The question asked by the interviewer.")
    candidate_transcript: str = Field(description="Original transcript recorded during the interview session.")
    gemini_verified_transcript: str = Field(description="Transcript verified/corrected by Gemini from continuous audio waveform.")
    technical_score: int = Field(ge=1, le=10, description="Technical accuracy score from 1 (poor) to 10 (excellent).")
    vocal_confidence_score: int = Field(ge=1, le=10, description="Vocal confidence score from 1 (timid/hesitant) to 10 (assertive/fluent).")
    hesitation_level: str = Field(description="Observed hesitation level: 'Low', 'Medium', or 'High'.")
    emotional_state: str = Field(description="Primary vocal emotion: 'Calm', 'Stressed', 'Uncertain', or 'Confident'.")
    filler_word_count: int = Field(ge=0, description="Estimated count of filler words (e.g., um, ah, like, you know).")
    missing_concepts: List[str] = Field(default_factory=list, description="Key technical concepts missing from the candidate's response.")
    audio_notes: str = Field(description="Specific qualitative feedback on candidate's vocal tone, pacing, and speech delivery.")


class PillarScore(BaseModel):
    pillar_name: str = Field(description="Name of technical evaluation pillar (e.g., 'Frontend Architecture', 'React Internals').")
    score: int = Field(ge=0, le=100, description="Aggregated score out of 100 for this domain pillar.")
    summary: str = Field(description="Detailed performance summary for this pillar.")


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
    missing_concepts: List[str]
    technical_notes: str


class CandidateReportPayload(BaseModel):
    session_id: str = Field(description="Unique session identifier.")
    generated_at: str = Field(description="ISO timestamp when the report was synthesized.")
    overall_hiring_signal: str = Field(description="Overall recommendation: 'Strong Hire', 'Hire', 'Lean No Hire', or 'No Hire'.")
    overall_technical_score: int = Field(ge=0, le=100, description="Aggregated overall technical score across all turns.")
    overall_vocal_confidence_score: int = Field(ge=0, le=100, description="Aggregated overall vocal delivery score across all turns.")
    technical_pillars: List[PillarScore] = Field(default_factory=list, description="Domain-specific score breakdowns.")
    turn_evaluations: List[TurnAnalysis] = Field(default_factory=list, description="Detailed per-turn evaluation items.")
    executive_summary: str = Field(description="High-level narrative summary of candidate performance for hiring managers.")
