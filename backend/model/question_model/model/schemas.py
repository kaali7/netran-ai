"""
Netran AI — Stage 2: Contextual Question & Behavioral Prompt Engine
Module: schemas.py
Description: Enriched Pydantic v2 schemas for Stage 2 Adaptive Contextual & Behavioral Intelligence Engine.
"""

from typing import Literal

from pydantic import BaseModel, Field


class SkillMatch(BaseModel):
    skill: str = Field(description="Name of the matched technical skill or framework.")
    resume_evidence: str = Field(description="Direct evidence or project reference extracted from candidate resume.")
    proficiency_tier: Literal["Foundational", "Intermediate", "Production Master"] = Field(
        description="Assessed candidate proficiency level."
    )


class SkillGap(BaseModel):
    missing_skill: str = Field(description="Technical requirement from JD/Rubric missing or weak on resume.")
    jd_importance: Literal["Critical", "Secondary"] = Field(description="Importance level of the missing skill for this role.")
    probing_strategy: str = Field(description="Strategic question approach to verify foundational understanding.")


class ResumeAnalysis(BaseModel):
    matched_skills: list[SkillMatch] = Field(default_factory=list, description="List of matched candidate skills with evidence.")
    missing_or_gap_skills: list[SkillGap] = Field(default_factory=list, description="Identified skill gaps and probing strategy.")
    resume_red_flags: list[str] = Field(default_factory=list, description="Potential resume warning signals or unexplained gaps.")
    key_projects_to_probe: list[str] = Field(default_factory=list, description="Top candidate resume projects to deep-dive on.")


class AnswerRubric(BaseModel):
    poor_answer_indicators: list[str] = Field(description="Indicators of a superficial, weak, or incorrect answer.")
    good_answer_indicators: list[str] = Field(description="Indicators of a solid, production-grade candidate response.")
    bar_raiser_indicators: list[str] = Field(description="Indicators of an exceptional, senior/staff level answer.")


class QuestionItem(BaseModel):
    id: int = Field(description="Sequential question index (1-15).")
    tier: str = Field(default="Tier 2 (Core Production)", description="Tier 1 (Warmup) | Tier 2 (Core Production) | Tier 3 (System Design)")
    topic: str = Field(description="Technical domain pillar or topic category.")
    difficulty: Literal["Junior", "Mid", "Senior", "Lead", "Staff"] = Field(description="Difficulty level for this question.")
    question_text: str = Field(description="Phrased technical interview question.")
    resume_context: str = Field(default="General candidate profile", description="Referenced candidate resume project or skill context.")
    expected_keywords: list[str] = Field(default_factory=list, description="Core architectural concepts expected in response.")
    rubric: AnswerRubric = Field(description="Evaluation rubric containing poor, good, and bar-raiser indicators.")
    followup_if_strong: str = Field(description="Advanced follow-up question if candidate gives a bar-raiser response.")
    followup_if_weak: str = Field(description="Simplifying diagnostic follow-up question if candidate struggles.")


class InterviewerBehavior(BaseModel):
    session_id: str = Field(description="Unique session identifier.")
    persona: str = Field(default="Eva", description="Interviewer persona name.")
    target_company: str = Field(default="Target Company", description="Target company name.")
    candidate_name: str = Field(default="Candidate", description="Candidate name.")
    target_role: str = Field(default="Target Role", description="Target role title.")
    interviewer_system_prompt: str = Field(description="Token-calibrated system prompt for Stage 3 Ollama Qwen2.5.")
    behavior_rules: list[str] = Field(default_factory=list, description="Low-latency voice interaction rules.")


class Stage2Output(BaseModel):
    session_id: str = Field(description="Unique session identifier.")
    resume_analysis: ResumeAnalysis = Field(description="Skill match & risk analysis matrix.")
    interview_questions: list[QuestionItem] = Field(description="Ordered array of 15 branching technical questions.")
    interviewer_behavior: InterviewerBehavior = Field(description="Voice persona settings and runtime system prompt.")
