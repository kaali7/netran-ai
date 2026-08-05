"""
Netran AI — Stage 3: Live Voice-to-Voice Loop
Module: schemas.py
Description: Pydantic v2 data contracts enforcing strict input validation for Stage 2 bundle
             artifacts and defining output turn & session manifest schemas for Stage 4.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field


class AnswerRubric(BaseModel):
    """Evaluation rubric indicators for a technical question."""
    poor_answer_indicators: list[str] = Field(default_factory=list)
    good_answer_indicators: list[str] = Field(default_factory=list)
    bar_raiser_indicators: list[str] = Field(default_factory=list)


class InterviewQuestionInput(BaseModel):
    """Schema for individual technical interview questions ingested from Stage 2."""
    id: int
    tier: str = "Tier 1 (Warmup)"
    topic: str = "General Technical"
    difficulty: str = "Mid"
    question_text: str
    resume_context: str | None = None
    expected_keywords: list[str] = Field(default_factory=list)
    rubric: AnswerRubric | dict[str, Any] | None = None
    followup_if_strong: str | None = None
    followup_if_weak: str | None = None


class InterviewerBehaviorInput(BaseModel):
    """Schema for interviewer behavior guidelines ingested from Stage 2."""
    session_id: str = "default_session"
    persona: str = "Eva"
    target_company: str | None = None
    candidate_name: str | None = None
    target_role: str | None = None
    interviewer_system_prompt: str
    behavior_rules: list[str] = Field(default_factory=list)


class Stage2SessionBundle(BaseModel):
    """Container loading all Stage 2 input artifacts for Stage 3 execution."""
    behavior: InterviewerBehaviorInput
    questions: list[InterviewQuestionInput]
    system_prompt: str
    resume_analysis: dict[str, Any] | None = None


class Telemetry(BaseModel):
    """Timing and latency metrics for a single turn."""
    stt_latency_ms: float = 0.0
    llm_ttft_ms: float = 0.0
    tts_ttfa_ms: float = 0.0
    barge_in_reaction_time_ms: float = 0.0


class EvaluationMetrics(BaseModel):
    """Keyword density and evaluation branch metrics."""
    keyword_density_score: float = 0.0
    branch_taken: str = "next_topic"
    matched_keywords: list[str] = Field(default_factory=list)


class TurnManifest(BaseModel):
    """Telemetry and transcript data for a single interview turn."""
    turn_id: int
    timestamp_iso: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    turn_intent: Literal[
        "TECHNICAL_ANSWER",
        "ICEBREAKER",
        "CANDIDATE_META_QUERY",
        "SKIP_REQUEST",
        "AUDIO_CHECK_OR_PAUSE",
        "BARGE_IN_INTERRUPTION"
    ] = "TECHNICAL_ANSWER"
    question_id: int | str | None = None
    topic: str | None = "General Technical"
    question_text: str | None = ""
    candidate_transcript: str = ""
    candidate_raw_transcript: str | None = None
    eva_internal_reasoning: str | None = "N/A - CoT Disabled for Low Latency"
    eva_tone_used: str | None = "direct"
    eva_spoken_reply: str | None = None
    audio_start_sec: float = 0.0
    audio_end_sec: float = 0.0
    silence_duration_before_answer_sec: float = 0.0
    evaluation_branch_taken: str = "next_topic"
    evaluation_metrics: EvaluationMetrics | None = None
    telemetry: Telemetry = Field(default_factory=Telemetry)

    # Backward compatibility properties
    @property
    def stt_latency_ms(self) -> float:
        return self.telemetry.stt_latency_ms

    @property
    def ttft_ms(self) -> float:
        return self.telemetry.llm_ttft_ms

    @property
    def eva_reasoning(self) -> str | None:
        return self.eva_internal_reasoning

    @property
    def eva_reply(self) -> str | None:
        return self.eva_spoken_reply


class SessionMetadata(BaseModel):
    """Session metadata details."""
    session_id: str
    candidate_name: str | None = "Candidate"
    target_role: str | None = "Technical Role"
    target_company: str | None = "Netran AI"
    start_time_iso: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    end_time_iso: str | None = None
    total_turns: int = 0
    total_barge_ins: int = 0


class EvaluatedTechnicalSummary(BaseModel):
    """Consolidated technical evaluation summary."""
    topics_covered: int = 0
    completed_naturally: bool = True
    average_keyword_density: float = 0.0
    strong_branches_triggered: int = 0
    weak_branches_triggered: int = 0
    skips_requested: int = 0


class SessionManifest(BaseModel):
    """Root container storing session metadata, chronological transcript turns, and evaluated technical summary."""
    session_metadata: SessionMetadata
    turns: list[TurnManifest] = Field(default_factory=list)
    evaluated_technical_summary: EvaluatedTechnicalSummary = Field(default_factory=EvaluatedTechnicalSummary)

    # Backward compatibility properties & dict exports
    @property
    def session_id(self) -> str:
        return self.session_metadata.session_id

    @property
    def session_start_iso(self) -> str:
        return self.session_metadata.start_time_iso

    @property
    def total_turns(self) -> int:
        return self.session_metadata.total_turns

    @property
    def full_chronological_transcript(self) -> list[TurnManifest]:
        return self.turns

    def model_dump(self, **kwargs) -> dict[str, Any]:
        d = super().model_dump(**kwargs)
        d["session_id"] = self.session_metadata.session_id
        d["session_start_iso"] = self.session_metadata.start_time_iso
        d["total_turns"] = self.session_metadata.total_turns
        return d


def load_stage2_bundle(dir_path: str | Path) -> Stage2SessionBundle:
    """
    Loads and validates Stage 2 output artifacts from a specified directory.

    Expected files:
    - interview_questions.json (Required)
    - interviewer_behavior.json (Required, contains interviewer_system_prompt)
    - resume_analysis.json (Optional)

    :param dir_path: Directory path containing Stage 2 files.
    :return: Stage2SessionBundle object.
    """
    p = Path(dir_path).resolve()
    if not p.exists() or not p.is_dir():
        raise FileNotFoundError(f"Stage 2 input directory not found: {p}")

    questions_file = p / "interview_questions.json"
    behavior_file = p / "interviewer_behavior.json"
    system_prompt_file = p / "system_prompt.txt"
    resume_analysis_file = p / "resume_analysis.json"

    if not questions_file.exists():
        raise FileNotFoundError(f"Missing required Stage 2 artifact: {questions_file}")
    if not behavior_file.exists():
        raise FileNotFoundError(f"Missing required Stage 2 artifact: {behavior_file}")

    with open(questions_file, "r", encoding="utf-8") as f:
        raw_questions = json.load(f)

    with open(behavior_file, "r", encoding="utf-8") as f:
        raw_behavior = json.load(f)

    questions = [InterviewQuestionInput.model_validate(q) for q in raw_questions]
    behavior = InterviewerBehaviorInput.model_validate(raw_behavior)

    if system_prompt_file.exists():
        with open(system_prompt_file, "r", encoding="utf-8") as f:
            system_prompt = f.read().strip()
    else:
        system_prompt = behavior.interviewer_system_prompt

    resume_analysis = None
    if resume_analysis_file.exists():
        try:
            with open(resume_analysis_file, "r", encoding="utf-8") as f:
                resume_analysis = json.load(f)
        except Exception:
            resume_analysis = None

    return Stage2SessionBundle(
        behavior=behavior,
        questions=questions,
        system_prompt=system_prompt,
        resume_analysis=resume_analysis,
    )


if __name__ == "__main__":
    print("Testing Stage 3 Schemas Module...")
    # Test schema instantiation
    sample_q = InterviewQuestionInput(
        id=1,
        topic="FastAPI",
        question_text="How does FastAPI handle async def?",
        expected_keywords=["event loop", "asyncio"]
    )
    print("Sample Question validated:", sample_q.model_dump_json(indent=2))
