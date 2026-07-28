"""
Netran AI — Stage 3: Live Voice-to-Voice Loop
Module: schemas.py
Description: Pydantic v2 data contracts enforcing strict input validation for Stage 2 bundle
             artifacts and defining output turn & session manifest schemas for Stage 4.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field


class AnswerRubric(BaseModel):
    """Evaluation rubric indicators for a technical question."""
    poor_answer_indicators: List[str] = Field(default_factory=list)
    good_answer_indicators: List[str] = Field(default_factory=list)
    bar_raiser_indicators: List[str] = Field(default_factory=list)


class InterviewQuestionInput(BaseModel):
    """Schema for individual technical interview questions ingested from Stage 2."""
    id: int
    tier: str = "Tier 1 (Warmup)"
    topic: str = "General Technical"
    difficulty: str = "Mid"
    question_text: str
    resume_context: Optional[str] = None
    expected_keywords: List[str] = Field(default_factory=list)
    rubric: Optional[Union[AnswerRubric, Dict[str, Any]]] = None
    followup_if_strong: Optional[str] = None
    followup_if_weak: Optional[str] = None


class InterviewerBehaviorInput(BaseModel):
    """Schema for interviewer behavior guidelines ingested from Stage 2."""
    session_id: str = "default_session"
    persona: str = "Eva"
    target_company: Optional[str] = None
    candidate_name: Optional[str] = None
    target_role: Optional[str] = None
    interviewer_system_prompt: str
    behavior_rules: List[str] = Field(default_factory=list)


class Stage2SessionBundle(BaseModel):
    """Container loading all Stage 2 input artifacts for Stage 3 execution."""
    behavior: InterviewerBehaviorInput
    questions: List[InterviewQuestionInput]
    system_prompt: str
    resume_analysis: Optional[Dict[str, Any]] = None


class TurnManifest(BaseModel):
    """Telemetry and transcript data for a single interview turn."""
    turn_id: int
    question_id: int
    topic: str
    question_text: str
    candidate_transcript: str
    audio_start_sec: float
    audio_end_sec: float
    silence_duration_before_answer_sec: float = 0.0
    stt_latency_ms: float = 0.0
    ttft_ms: float = 0.0
    evaluation_branch_taken: Literal["strong_followup", "weak_followup", "next_topic"] = "next_topic"


class SessionManifest(BaseModel):
    """Root container storing session metadata and sequence of turn manifests."""
    session_id: str
    session_start_iso: str
    total_turns: int
    turns: List[TurnManifest]


def load_stage2_bundle(dir_path: Union[str, Path]) -> Stage2SessionBundle:
    """
    Loads and validates Stage 2 output artifacts from a specified directory.

    Expected files:
    - interview_questions.json (Required)
    - interviewer_behavior.json (Required)
    - system_prompt.txt (Optional, fallback to interviewer_behavior system prompt)
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
