"""
Netran AI — Stage 2: Contextual Question & Behavioral Prompt Engine
Module: schemas.py
Description: Enriched Pydantic v2 schemas for Stage 2 Adaptive Contextual & Behavioral Intelligence Engine.
"""

from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


class SkillMatch(BaseModel):
    skill: str = Field(description="Name of the matched technical skill or framework.")
    resume_evidence: str = Field(description="Direct evidence or project reference extracted from candidate resume.")
    proficiency_tier: Literal["Production Master", "Advanced", "Intermediate", "Foundational"] = Field(
        default="Intermediate", description="Assessed candidate proficiency level."
    )


class SkillGap(BaseModel):
    missing_skill: str = Field(description="Technical requirement from JD/Rubric missing or weak on resume.")
    jd_importance: Literal["Critical", "Secondary"] = Field(description="Importance level of the missing skill for this role.")
    probing_strategy: str = Field(description="Strategic question approach to verify foundational understanding.")


class PersonalTraitsAndHobbies(BaseModel):
    traits_detected: list[str] = Field(default_factory=list, description="Work style or personality traits detected.")
    hobbies_or_interests: list[str] = Field(default_factory=list, description="Extracted or inferred personal interests.")
    icebreaker_probe_topic: str = Field(
        default="Personal passions & engineering approach",
        description="A creative icebreaker context connecting personal traits to engineering."
    )


class CandidateProfile(BaseModel):
    candidate_name: str = Field(default="Candidate", description="Extracted or inferred candidate full name.")
    target_role: str = Field(default="Target Role", description="Target role from JD.")
    years_of_experience: float = Field(default=0.0, description="Total estimated years of experience.")
    current_company_or_status: str = Field(default="N/A", description="Current employer or status.")
    core_identity_summary: str = Field(default="", description="1-2 sentence core developer profile summary.")
    soft_skills: list[str] = Field(default_factory=list, description="Extracted soft skills.")
    key_achievements: list[str] = Field(default_factory=list, description="Quantifiable metrics and achievements.")
    personal_traits_and_hobbies: PersonalTraitsAndHobbies = Field(
        default_factory=PersonalTraitsAndHobbies,
        description="Personal traits, hobbies, and icebreaker probe topic."
    )


class RoleFitScoring(BaseModel):
    overall_jd_match_score: int = Field(default=80, description="Overall JD match score (0-100).")
    technical_depth_score: int = Field(default=80, description="Technical depth score (0-100).")
    experience_seniority_score: int = Field(default=80, description="Experience and seniority alignment score (0-100).")
    project_relevance_score: int = Field(default=80, description="Project relevance score (0-100).")
    clarity_and_impact_score: int = Field(default=80, description="Clarity and impact score (0-100).")


class ExtractedSkillMatch(BaseModel):
    skill: str = Field(description="Skill Name.")
    resume_evidence: str = Field(description="Verbatim or summarized evidence from resume.")
    proficiency_tier: Literal["Production Master", "Advanced", "Intermediate", "Foundational"] = Field(
        default="Intermediate", description="Proficiency tier."
    )
    jd_requirement_level: Literal["Must-Have", "Important", "Nice-to-Have"] = Field(
        default="Must-Have", description="JD requirement level."
    )


class WorkHistoryEntry(BaseModel):
    company_name: str = Field(description="Company Name.")
    role: str = Field(description="Role Title.")
    tenure: str = Field(description="Dates or Duration.")
    impact_level: Literal["High", "Medium", "Low"] = Field(default="High", description="Impact level.")
    key_responsibilities: str = Field(description="Summary of key responsibilities.")
    verifiable_outcomes: list[str] = Field(default_factory=list, description="Quantifiable outcomes.")


class DetailedProjectAnalysis(BaseModel):
    project_name: str = Field(description="Project Name.")
    relevance_score: int = Field(default=8, description="Relevance score to target JD (1-10).")
    tech_stack_used: list[str] = Field(default_factory=list, description="Tech stack technologies used.")
    architecture_type: str = Field(default="Microservices", description="Architecture pattern.")
    quantifiable_scale: str = Field(default="Production scale", description="Scale/traffic metrics.")
    suggested_interview_probes: list[str] = Field(default_factory=list, description="Probing questions.")


class RedFlagItem(BaseModel):
    flag_type: Literal["Claim Verification", "Infrastructure Depth", "Employment Gap", "General Warning"] = Field(
        default="General Warning", description="Type of warning flag."
    )
    description: str = Field(description="Specific concern regarding a claim or lack of detail.")
    probe_question: str = Field(description="Direct challenge question to verify authenticity.")


class ExperienceGapsAndRedFlags(BaseModel):
    technical_gaps: list[SkillGap] = Field(default_factory=list, description="Missing skills or experience gaps.")
    resume_red_flags: list[RedFlagItem] = Field(default_factory=list, description="Specific warning signals or red flags.")


class ProjectRelevance(BaseModel):
    project_name: str = Field(description="Name or title of candidate project.")
    relevance_score: int = Field(description="Score from 1 to 10 evaluating project relevance to the target JD.")
    reasoning: str = Field(description="Brief technical justification for the relevance score.")


class ResumeAnalysis(BaseModel):
    candidate_profile: CandidateProfile = Field(default_factory=CandidateProfile, description="Detailed candidate profile and personality.")
    role_fit_scoring: RoleFitScoring = Field(default_factory=RoleFitScoring, description="Quantitative 5-pillar JD fit scoring.")
    extracted_skill_overlap: list[ExtractedSkillMatch] = Field(default_factory=list, description="Extracted technical skill overlap.")
    experience_and_work_history: list[WorkHistoryEntry] = Field(default_factory=list, description="Detailed work history and outcomes.")
    detailed_project_analysis: list[DetailedProjectAnalysis] = Field(default_factory=list, description="Detailed project architecture & scale analysis.")
    experience_gaps_and_red_flags: ExperienceGapsAndRedFlags = Field(default_factory=ExperienceGapsAndRedFlags, description="Technical gaps and red flag probes.")

    @model_validator(mode="before")
    @classmethod
    def migrate_legacy_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # 1. Skill overlap migration
            if "matched_skills" in data and "extracted_skill_overlap" not in data:
                raw_matched = data.pop("matched_skills")
                converted_matched = []
                if isinstance(raw_matched, list):
                    for item in raw_matched:
                        if isinstance(item, dict):
                            converted_matched.append({
                                "skill": item.get("skill", "Unknown"),
                                "resume_evidence": item.get("resume_evidence", "Extracted from resume"),
                                "proficiency_tier": item.get("proficiency_tier", "Intermediate") if item.get("proficiency_tier") in ["Production Master", "Advanced", "Intermediate", "Foundational"] else "Intermediate",
                                "jd_requirement_level": "Must-Have"
                            })
                data["extracted_skill_overlap"] = converted_matched

            # 2. Experience gaps migration
            if "missing_or_gap_skills" in data and "experience_gaps" not in data and "experience_gaps_and_red_flags" not in data:
                raw_gaps = data.pop("missing_or_gap_skills")
                raw_flags = data.pop("resume_red_flags", [])
                converted_flags = []
                if isinstance(raw_flags, list):
                    for rf in raw_flags:
                        if isinstance(rf, str):
                            converted_flags.append({"flag_type": "Claim Verification", "description": rf, "probe_question": rf})
                        elif isinstance(rf, dict):
                            converted_flags.append(rf)
                data["experience_gaps_and_red_flags"] = {
                    "technical_gaps": raw_gaps,
                    "resume_red_flags": converted_flags
                }

            # 3. Project analysis migration
            if "key_projects_to_probe" in data and "detailed_project_analysis" not in data:
                raw_projects = data.pop("key_projects_to_probe")
                converted_projects = []
                if isinstance(raw_projects, list):
                    for item in raw_projects:
                        if isinstance(item, str):
                            converted_projects.append({
                                "project_name": item,
                                "relevance_score": 8,
                                "tech_stack_used": ["Python", "Backend"],
                                "architecture_type": "Microservices",
                                "quantifiable_scale": "Production Workload",
                                "suggested_interview_probes": [f"Deep dive into {item}"]
                            })
                        elif isinstance(item, dict):
                            converted_projects.append(item)
                data["detailed_project_analysis"] = converted_projects
            elif "project_relevance_scores" in data and "detailed_project_analysis" not in data:
                raw_prs = data.pop("project_relevance_scores")
                converted_projects = []
                if isinstance(raw_prs, list):
                    for item in raw_prs:
                        if isinstance(item, dict):
                            converted_projects.append({
                                "project_name": item.get("project_name", "Project"),
                                "relevance_score": item.get("relevance_score", 8),
                                "tech_stack_used": ["Backend Stack"],
                                "architecture_type": "Microservices",
                                "quantifiable_scale": "Production Scale",
                                "suggested_interview_probes": [item.get("reasoning", "Deep dive")]
                            })
                data["detailed_project_analysis"] = converted_projects

        return data

    # Backward compatibility properties
    @property
    def matched_skills(self) -> list[ExtractedSkillMatch]:
        return self.extracted_skill_overlap

    @property
    def missing_or_gap_skills(self) -> list[SkillGap]:
        return self.experience_gaps_and_red_flags.technical_gaps

    @property
    def experience_gaps(self) -> list[SkillGap]:
        return self.experience_gaps_and_red_flags.technical_gaps

    @property
    def project_relevance_scores(self) -> list[ProjectRelevance]:
        return [
            ProjectRelevance(
                project_name=p.project_name,
                relevance_score=p.relevance_score,
                reasoning=p.quantifiable_scale
            )
            for p in self.detailed_project_analysis
        ]

    @property
    def candidate_highlights(self) -> list[str]:
        return self.candidate_profile.key_achievements or [self.candidate_profile.core_identity_summary]

    @property
    def resume_red_flags(self) -> list[str]:
        return [rf.description for rf in self.experience_gaps_and_red_flags.resume_red_flags]

    @property
    def key_projects_to_probe(self) -> list[str]:
        return [f"{p.project_name} (Score: {p.relevance_score}/10)" for p in self.detailed_project_analysis]


class AnswerRubric(BaseModel):
    poor_answer_indicators: list[str] = Field(description="Indicators of a superficial, weak, or incorrect answer.")
    good_answer_indicators: list[str] = Field(description="Indicators of a solid, production-grade candidate response.")
    bar_raiser_indicators: list[str] = Field(description="Indicators of an exceptional, senior/staff level answer.")


class QuestionItem(BaseModel):
    id: int = Field(description="Sequential question index (1-15).")
    tier: str = Field(
        default="Tier 2 (Core Production)",
        description="Category / Tier: ICEBREAKER | BEHAVIORAL | PROJECT_DEEP_DIVE | EXPERIENCE | TECHNICAL"
    )
    topic: str = Field(description="Technical or behavioral domain pillar or topic category.")
    difficulty: Literal["easy", "medium", "hard", "Junior", "Mid", "Senior", "Lead", "Staff"] = Field(description="Difficulty level for this question.")
    question_text: str = Field(description="Phrased interview question.")
    resume_context: str = Field(default="General candidate profile", description="Referenced candidate resume project or skill context.")
    expected_keywords: list[str] = Field(default_factory=list, description="Core architectural or behavioral concepts expected in response.")
    rubric: AnswerRubric = Field(description="Evaluation rubric containing poor, good, and bar-raiser indicators.")
    followup_if_strong: str = Field(description="Advanced follow-up question if candidate gives a bar-raiser response.")
    followup_if_weak: str = Field(description="Simplifying diagnostic follow-up question if candidate struggles.")


class InterviewerBehavior(BaseModel):
    session_id: str = Field(description="Unique session identifier.")
    persona: str = Field(default="Eva - Senior Technical Interviewer", description="Interviewer persona name.")
    target_company: str = Field(default="Target Company", description="Target company name.")
    candidate_name: str = Field(default="Candidate", description="Candidate name.")
    target_role: str = Field(default="Target Role", description="Target role title.")
    interviewer_system_prompt: str = Field(description="Token-calibrated system prompt for Stage 3 Ollama Qwen2.5.")
    behavior_rules: list[str] = Field(default_factory=list, description="Low-latency voice interaction rules.")


class PlannerOutput(BaseModel):
    interview_questions: list[QuestionItem] = Field(description="Ordered array of 12-15 multi-phase interview questions.")
    interviewer_behavior: InterviewerBehavior = Field(description="Interviewer persona settings and runtime system prompt.")


class Stage2Output(BaseModel):
    session_id: str = Field(description="Unique session identifier.")
    resume_analysis: ResumeAnalysis = Field(description="Skill match & risk analysis matrix.")
    interview_questions: list[QuestionItem] = Field(description="Ordered array of 12-15 branching technical questions.")
    interviewer_behavior: InterviewerBehavior = Field(description="Voice persona settings and runtime system prompt.")
