"""
Netran AI — Stage 2: Contextual Question & Behavioral Prompt Engine
Module: schemas.py
Description: Pydantic v2 schemas (`QuestionItem`, `Stage2Output`) enforcing output constraints.
"""

from typing import Literal

from pydantic import BaseModel, Field


class QuestionItem(BaseModel):
    id: int = Field(description="Sequential question index (1-15).")
    topic: str = Field(description="Technical domain pillar (e.g., React Internals, Tailwind CSS).")
    difficulty: Literal["Junior", "Mid", "Senior"] = Field(description="Difficulty level for this category")
    question_text: str = Field(description="Phrased technical interview question.")
    expected_keywords: list[str] = Field(description="Core architectural concepts expected in the candidate's response.")
    resume_reference: str | None = Field(None, description="Referenced past project or skill from candidate resume.")

class Stage2Output(BaseModel):
    session_id: str = Field(description="Unique session identifier.")
    interviewer_system_prompt: str = Field(description="Formatted runtime system prompt injected into Ollama Qwen2.5.")
    question_tree: list[QuestionItem] = Field(description="Ordered array of 15 structured technical questions.")
