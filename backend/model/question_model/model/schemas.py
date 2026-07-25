from pydantic import BaseModel, Field
from typing import List, Literal, Optional

class QuestionItem(BaseModel):
    id: int = Field(description="Sequential question index (1-15).")
    topic: str = Field(description="Technical domain pillar (e.g., React Internals, Tailwind CSS).")
    difficulty: Literal["Junior", "Mid", "Senior"] = Field(description="Difficulty level for this category")
    question_text: str = Field(description="Phrased technical interview question.")
    expected_keywords: List[str] = Field(description="Core architectural concepts expected in the candidate's response.")
    resume_reference: Optional[str] = Field(None, description="Referenced past project or skill from candidate resume.")

class Stage2Output(BaseModel):
    session_id: str = Field(description="Unique session identifier.")
    interviewer_system_prompt: str = Field(description="Formatted runtime system prompt injected into Ollama Qwen2.5.")
    question_tree: List[QuestionItem] = Field(description="Ordered array of 15 structured technical questions.")
