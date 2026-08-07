"""
Netran AI — Stage 1: JD Research & Market Intelligence Engine
Module: schemas.py
Description: Pydantic v2 schemas (`ParsedJD`, `InterviewTopic`, `InterviewRubric`) enforcing JSON outputs.
"""


from pydantic import BaseModel, Field


class ParsedJD(BaseModel):
    role: str = Field(description="Extracted job role/title (e.g. Senior Frontend Engineer)")
    company: str = Field(description="Extracted company name or 'Target Company' if not specified")
    target_seniority: str = Field(default="Senior", description="Junior, Mid, Senior, Lead, or Staff")
    tech_stack: list[str] = Field(description="List of key technologies, frameworks, and skills")
    search_queries: list[str] = Field(description="3 targeted web search queries for Tech, Market, and HR vectors")


class SalaryRange(BaseModel):
    usd_range: str = Field(description="Estimated USD salary range (e.g. $140k - $190k Base)")
    inr_range: str = Field(description="Estimated INR CTC salary range (e.g. ₹28 LPA - ₹55 LPA)")
    compensation_notes: str = Field(description="Key compensation drivers or equity/bonus notes")


class MarketIntelligence(BaseModel):
    salary_benchmark: SalaryRange = Field(description="USD and INR CTC salary benchmarks")
    market_demand_level: str = Field(description="High, Very High, or Niche")
    hiring_landscape: str = Field(description="Industry demand overview and market trends")
    top_hiring_company_types: list[str] = Field(description="Types of companies actively hiring this profile")


class HRRecruiterLens(BaseModel):
    what_hr_looks_for: list[str] = Field(description="Key resume metrics and achievements HR checks")
    green_flags: list[str] = Field(description="Positive behavioral/technical screening indicators")
    red_flags: list[str] = Field(description="Warning signs or missing core experiences")


class SoftSkillsBreakdown(BaseModel):
    skill: str = Field(description="Name of soft skill")
    why_it_matters: str = Field(description="Why this soft skill is essential for this role level")
    evaluation_method: str = Field(description="How to evaluate this soft skill in an interview")


class SkillRequirements(BaseModel):
    must_have_hard_skills: list[str] = Field(description="Non-negotiable technical skills")
    nice_to_have_hard_skills: list[str] = Field(description="Bonus technical skills")
    critical_soft_skills: list[SoftSkillsBreakdown] = Field(description="Essential soft skills breakdown")


class InterviewTopic(BaseModel):
    category: str = Field(description="Core technical area or topic category (e.g., System Design, Data Structures)")
    difficulty: str = Field(description="Difficulty level for this category (Junior, Mid, Senior, Lead, Staff)")
    example_questions: list[str] = Field(description="3-5 realistic interview questions based on market intel")


class InterviewRubric(BaseModel):
    roleOverview: str = Field(description="Summary of the role expectations and target candidate profile")
    marketIntelligence: MarketIntelligence | None = Field(default=None, description="Market demand, hiring landscape, and salary bands")
    hrRecruiterLens: HRRecruiterLens | None = Field(default=None, description="HR screening criteria, green flags, and red flags")
    skillRequirements: SkillRequirements | None = Field(default=None, description="Hard skills breakdown and soft skills evaluation matrix")
    keyTechnicalPillars: list[str] = Field(description="3-5 critical technical pillars required for this role")
    expectedInterviewTopics: list[InterviewTopic] = Field(description="Structured list of interview topics and questions")


# Alias for spec compliance
EnhancedInterviewRubric = InterviewRubric


class Stage1Output(BaseModel):
    rubric: InterviewRubric = Field(description="Generated interview rubric object")
    parsed_jd: ParsedJD = Field(description="Extracted JD metadata and search queries")
    search_context: list[dict[str, str]] = Field(default_factory=list, description="Retrieved web search snippets and sources")
    cached: bool = Field(default=False, description="True if loaded from SQLite cache")
    execution_time_seconds: float | None = Field(default=None, description="Pipeline execution time in seconds")

