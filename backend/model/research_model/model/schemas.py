"""
Netran AI — Stage 1: JD Research & Market Intelligence Engine
Module: schemas.py
Description: Pydantic v2 schemas (`ParsedJD`, `InterviewTopic`, `InterviewRubric`) enforcing JSON outputs.
"""

from typing import List, Literal
from pydantic import BaseModel, Field

class ParsedJD(BaseModel):
    role: str = Field(description="Extracted job role/title (e.g. Senior Frontend Engineer)")
    company: str = Field(description="Extracted company name or 'Target Company' if not specified")
    tech_stack: List[str] = Field(description="List of key technologies, frameworks, and skills")
    search_queries: List[str] = Field(description="2-3 targeted web search queries to find real interview questions for this role and stack")

class InterviewTopic(BaseModel):
    category: str = Field(description="Core technical area or topic category (e.g., System Design, Data Structures)")
    difficulty: Literal["Junior", "Mid", "Senior"] = Field(description="Difficulty level for this category")
    example_questions: List[str] = Field(description="3-5 realistic interview questions based on market intel")

class InterviewRubric(BaseModel):
    roleOverview: str = Field(description="Summary of the role expectations and target candidate profile")
    keyTechnicalPillars: List[str] = Field(description="3-5 critical technical pillars required for this role")
    expectedInterviewTopics: List[InterviewTopic] = Field(description="Structured list of interview topics and questions")
