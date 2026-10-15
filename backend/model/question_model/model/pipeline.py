"""
Netran AI — Stage 2: Contextual Question & Behavioral Prompt Engine
Module: pipeline.py
Description: Master Stage2Pipeline orchestrator generating the 15-question tiered interview tree,
             resume gap analysis matrix, interviewer behavior settings, and latency-constrained voice system prompt.
"""

import json
import logging
import os
import time
from typing import Any

from google import genai
from google.genai import types

from concurrent.futures import ThreadPoolExecutor

try:
    from .cache import Stage2Cache
    from .config import Stage2Config
    from .prompt_builder import Stage2PromptBuilder
    from .prompts import (
        ANALYST_PROMPT_TEMPLATE,
        FALLBACK_SYSTEM_PROMPT_TEMPLATE,
        PLANNER_PROMPT_TEMPLATE,
    )
    from .resume_parser import ResumeParser
    from .schemas import (
        AnswerRubric,
        CandidateProfile,
        DetailedProjectAnalysis,
        ExperienceGapsAndRedFlags,
        ExtractedSkillMatch,
        InterviewerBehavior,
        PersonalTraitsAndHobbies,
        PlannerOutput,
        ProjectRelevance,
        QuestionItem,
        RedFlagItem,
        ResumeAnalysis,
        RoleFitScoring,
        SkillGap,
        SkillMatch,
        Stage2Output,
        WorkHistoryEntry,
    )
except ImportError:
    try:
        from model.question_model.model.cache import Stage2Cache
        from model.question_model.model.config import Stage2Config
        from model.question_model.model.prompt_builder import Stage2PromptBuilder
        from model.question_model.model.prompts import (
            ANALYST_PROMPT_TEMPLATE,
            FALLBACK_SYSTEM_PROMPT_TEMPLATE,
            PLANNER_PROMPT_TEMPLATE,
        )
        from model.question_model.model.resume_parser import ResumeParser
        from model.question_model.model.schemas import (
            AnswerRubric,
            CandidateProfile,
            DetailedProjectAnalysis,
            ExperienceGapsAndRedFlags,
            ExtractedSkillMatch,
            InterviewerBehavior,
            PersonalTraitsAndHobbies,
            PlannerOutput,
            ProjectRelevance,
            QuestionItem,
            RedFlagItem,
            ResumeAnalysis,
            RoleFitScoring,
            SkillGap,
            SkillMatch,
            Stage2Output,
            WorkHistoryEntry,
        )
    except ImportError:
        from cache import Stage2Cache
        from config import Stage2Config
        from prompt_builder import Stage2PromptBuilder
        from prompts import (
            ANALYST_PROMPT_TEMPLATE,
            FALLBACK_SYSTEM_PROMPT_TEMPLATE,
            PLANNER_PROMPT_TEMPLATE,
        )
        from resume_parser import ResumeParser
        from schemas import (
            AnswerRubric,
            CandidateProfile,
            DetailedProjectAnalysis,
            ExperienceGapsAndRedFlags,
            ExtractedSkillMatch,
            InterviewerBehavior,
            PersonalTraitsAndHobbies,
            PlannerOutput,
            ProjectRelevance,
            QuestionItem,
            RedFlagItem,
            ResumeAnalysis,
            RoleFitScoring,
            SkillGap,
            SkillMatch,
            Stage2Output,
            WorkHistoryEntry,
        )

logger = logging.getLogger(__name__)


class Stage2Pipeline:
    """Master pipeline execution class for Stage 2 (Adaptive Contextual & Behavioral Intelligence Engine)."""

    def __init__(self, config: Stage2Config | None = None):
        self.config = config or Stage2Config.from_env()
        self.cache = Stage2Cache()
        self.resume_parser = ResumeParser()
        self.prompt_builder = Stage2PromptBuilder()

    def run(
        self,
        session_id: str,
        jd_input: str | dict[str, Any],
        resume_path: str,
        target_seniority: str = "Senior",
        output_dir: str | None = None
    ) -> Stage2Output:
        """
        Core reasoning engine leveraging Gemini to generate structured resume analysis,
        15 tiered branching questions with rubrics, and the interviewer behavior prompt.
        """
        # 1. Standardize job context from input (raw text, dict, or Stage 1 JSON)
        job_dict: dict[str, Any] = {}
        if isinstance(jd_input, str):
            try:
                parsed = json.loads(jd_input)
                if isinstance(parsed, dict):
                    job_dict = parsed
                else:
                    job_dict = {"jd_text": jd_input, "target_seniority": target_seniority}
            except Exception:
                job_dict = {"jd_text": jd_input, "target_seniority": target_seniority}
        elif isinstance(jd_input, dict):
            job_dict = jd_input
        else:
            job_dict = {"jd_text": str(jd_input), "target_seniority": target_seniority}

        job_context = self.prompt_builder.extract_job_context(job_dict)
        effective_seniority = job_context.get("target_seniority", target_seniority) or target_seniority
        jd_text_for_hash = job_context.get("rubric_json", str(jd_input))

        # 2. Parse resume
        try:
            resume_text = self.resume_parser.parse(resume_path)
        except Exception as e:
            logger.error(f"Failed to parse resume: {e}")
            raise

        # 3. Check SQLite cache first for instant re-runs (<1ms)
        cached_output = self.cache.get(
            jd_text=jd_text_for_hash,
            resume_text=resume_text,
            target_seniority=effective_seniority,
            session_id=session_id
        )
        if cached_output:
            logger.info("Loaded Stage 2 question tree & system prompt from SQLite cache!")
            if output_dir:
                self.save_artifacts(output_dir, session_id, effective_seniority, cached_output)
            return cached_output

        groq_api_key = os.getenv("GROQ_API_KEY", "")
        groq_model = os.getenv("GROQ_EVALUATION_MODEL", "openai/gpt-oss-120b")

        api_key = self.config.gemini_api_key
        model = self.config.gemini_model or "gemini-3.6-flash"

        if not api_key and not groq_api_key:
            raise ValueError("Neither GROQ_API_KEY nor GEMINI_API_KEY is configured.")

        client = None
        if api_key:
            try:
                client = genai.Client(api_key=api_key)
            except Exception as e:
                logger.warning(f"Could not initialize Gemini client: {e}")

        planner_prompt = PLANNER_PROMPT_TEMPLATE.format(
            resume_text=resume_text,
            stage1_rubric_json=job_context["rubric_json"],
            session_id=session_id,
            company_name=job_context.get("company", "Target Company"),
            candidate_name="Candidate",
            target_role=job_context.get("role", "Target Role")
        )

        analyst_prompt = ANALYST_PROMPT_TEMPLATE.format(
            resume_text=resume_text,
            stage1_rubric_json=job_context["rubric_json"]
        )

        logger.info("Executing dual Planner & Analyst generation calls in parallel...")

        def _call_planner() -> PlannerOutput | None:
            # 1. Primary: Groq API
            if groq_api_key:
                try:
                    from groq import Groq
                    g_client = Groq(api_key=groq_api_key)
                    resp = g_client.chat.completions.create(
                        model=groq_model,
                        messages=[
                            {"role": "system", "content": "You are an expert interview question planner. Return strictly valid JSON conforming to the PlannerOutput schema."},
                            {"role": "user", "content": planner_prompt},
                        ],
                        response_format={"type": "json_object"},
                        temperature=0.2,
                        max_tokens=4096,
                    )
                    content = resp.choices[0].message.content
                    if content:
                        return PlannerOutput.model_validate_json(content)
                except Exception as ge:
                    logger.warning(f"Planner Groq call failed: {ge}. Trying Gemini...")

            # 2. Fallback: Google Gemini API
            if client:
                last_err = None
                for attempt in range(1, 4):
                    try:
                        res = client.models.generate_content(
                            model=model,
                            contents=planner_prompt,
                            config=types.GenerateContentConfig(
                                response_mime_type="application/json",
                                response_schema=PlannerOutput,
                                temperature=0.2,
                            )
                        )
                        if res and res.text:
                            return PlannerOutput.model_validate_json(res.text)
                    except Exception as e:
                        last_err = e
                        logger.warning(f"Planner Gemini API attempt {attempt}/3 error: {str(e)[:120]}")
                        if attempt < 3:
                            time.sleep(3 * attempt)
                logger.warning(f"Planner Gemini call failed after 3 attempts: {last_err}")
            return None

        def _call_analyst() -> ResumeAnalysis | None:
            # 1. Primary: Groq API
            if groq_api_key:
                try:
                    from groq import Groq
                    g_client = Groq(api_key=groq_api_key)
                    resp = g_client.chat.completions.create(
                        model=groq_model,
                        messages=[
                            {"role": "system", "content": "You are an expert resume and technical gap analyst. Return strictly valid JSON conforming to the ResumeAnalysis schema."},
                            {"role": "user", "content": analyst_prompt},
                        ],
                        response_format={"type": "json_object"},
                        temperature=0.2,
                        max_tokens=4096,
                    )
                    content = resp.choices[0].message.content
                    if content:
                        return ResumeAnalysis.model_validate_json(content)
                except Exception as ge:
                    logger.warning(f"Analyst Groq call failed: {ge}. Trying Gemini...")

            # 2. Fallback: Google Gemini API
            if client:
                last_err = None
                for attempt in range(1, 4):
                    try:
                        res = client.models.generate_content(
                            model=model,
                            contents=analyst_prompt,
                            config=types.GenerateContentConfig(
                                response_mime_type="application/json",
                                response_schema=ResumeAnalysis,
                                temperature=0.2,
                            )
                        )
                        if res and res.text:
                            return ResumeAnalysis.model_validate_json(res.text)
                    except Exception as e:
                        last_err = e
                        logger.warning(f"Analyst Gemini API attempt {attempt}/3 error: {str(e)[:120]}")
                        if attempt < 3:
                            time.sleep(3 * attempt)
                logger.warning(f"Analyst Gemini call failed after 3 attempts: {last_err}")
            return None

        planner_res: PlannerOutput | None = None
        analyst_res: ResumeAnalysis | None = None

        try:
            if groq_api_key:
                # Groq free tier enforces strict concurrent burst limits; sequential calls run in <2s safely
                planner_res = _call_planner()
                time.sleep(1.0)
                analyst_res = _call_analyst()
            else:
                with ThreadPoolExecutor(max_workers=2) as executor:
                    future_planner = executor.submit(_call_planner)
                    future_analyst = executor.submit(_call_analyst)
                    planner_res = future_planner.result()
                    analyst_res = future_analyst.result()
        except Exception as e:
            logger.warning(f"Dual execution exception ({e}). Utilizing fallback generator.")

        fallback_obj = self.generate_fallback_output(
            session_id=session_id,
            company=job_context.get("company", "Target Company"),
            role=job_context.get("role", "Target Role"),
            target_seniority=effective_seniority
        )

        final_questions = planner_res.interview_questions if (planner_res and planner_res.interview_questions) else fallback_obj.interview_questions
        final_behavior = planner_res.interviewer_behavior if (planner_res and planner_res.interviewer_behavior) else fallback_obj.interviewer_behavior
        final_behavior.session_id = session_id
        final_analysis = analyst_res if analyst_res else fallback_obj.resume_analysis

        stage2_output = Stage2Output(
            session_id=session_id,
            resume_analysis=final_analysis,
            interview_questions=final_questions,
            interviewer_behavior=final_behavior
        )

        # Save to SQLite cache
        self.cache.set(jd_text_for_hash, resume_text, effective_seniority, stage2_output)

        if output_dir:
            self.save_artifacts(output_dir, session_id, effective_seniority, stage2_output)

        return stage2_output

    @staticmethod
    def save_artifacts(output_dir: str, session_id: str, target_seniority: str, stage2_output: Stage2Output):
        """
        Saves the 3 core Stage 2 session artifacts into output_dir:
        1. resume_analysis.json
        2. interview_questions.json
        3. interviewer_behavior.json (contains interviewer_system_prompt)
        """
        os.makedirs(output_dir, exist_ok=True)

        # 1. resume_analysis.json
        analysis_path = os.path.join(output_dir, "resume_analysis.json")
        with open(analysis_path, "w", encoding="utf-8") as f:
            json.dump(stage2_output.resume_analysis.model_dump(), f, indent=2)

        # 2. interview_questions.json
        questions_path = os.path.join(output_dir, "interview_questions.json")
        with open(questions_path, "w", encoding="utf-8") as f:
            json.dump([q.model_dump() for q in stage2_output.interview_questions], f, indent=2)

        # 3. interviewer_behavior.json
        behavior_path = os.path.join(output_dir, "interviewer_behavior.json")
        with open(behavior_path, "w", encoding="utf-8") as f:
            json.dump(stage2_output.interviewer_behavior.model_dump(), f, indent=2)

        logger.info(f"Stage 2 output session artifacts saved to {output_dir}")

    @staticmethod
    def generate_fallback_output(
        session_id: str,
        company: str = "Target Company",
        role: str = "Target Role",
        target_seniority: str = "Senior"
    ) -> Stage2Output:
        """Generates structured fallback Stage2Output when LLM API is unavailable."""
        from .schemas import ProjectRelevance

        fallback_system_prompt = FALLBACK_SYSTEM_PROMPT_TEMPLATE.format(
            company_name=company,
            role_title=role,
            target_seniority=target_seniority
        )

        fallback_analysis = ResumeAnalysis(
            candidate_profile=CandidateProfile(
                candidate_name="Candidate",
                target_role=role,
                years_of_experience=5.0,
                current_company_or_status="Senior Software Engineer",
                core_identity_summary="Experienced backend engineer specializing in distributed systems and high-throughput microservices.",
                soft_skills=["Technical Leadership", "Problem Solving", "Cross-Functional Collaboration"],
                key_achievements=["Built FastAPI microservice processing 35M+ daily requests", "Reduced PostgreSQL p99 latency by 45%"],
                personal_traits_and_hobbies=PersonalTraitsAndHobbies(
                    traits_detected=["Analytical", "Pragmatic", "Curious"],
                    hobbies_or_interests=["Open Source Software", "System Architecture", "Chess"],
                    icebreaker_probe_topic="How chess strategies mirror distributed system fault tolerance"
                )
            ),
            role_fit_scoring=RoleFitScoring(
                overall_jd_match_score=88,
                technical_depth_score=90,
                experience_seniority_score=85,
                project_relevance_score=88,
                clarity_and_impact_score=90
            ),
            extracted_skill_overlap=[
                ExtractedSkillMatch(
                    skill="Python / Microservices Stack",
                    resume_evidence="Built scalable REST API services using FastAPI and PostgreSQL",
                    proficiency_tier="Production Master",
                    jd_requirement_level="Must-Have"
                ),
                ExtractedSkillMatch(
                    skill="Event-Driven Architecture",
                    resume_evidence="Deployed RabbitMQ and Kafka pipelines for async processing",
                    proficiency_tier="Advanced",
                    jd_requirement_level="Must-Have"
                )
            ],
            experience_and_work_history=[
                WorkHistoryEntry(
                    company_name="TechScale Solutions",
                    role="Senior Backend Engineer",
                    tenure="2022 - Present",
                    impact_level="High",
                    key_responsibilities="Designed high-throughput API gateway and event streaming services.",
                    verifiable_outcomes=["Scaled request volume from 5M to 35M daily requests with zero downtime"]
                )
            ],
            detailed_project_analysis=[
                DetailedProjectAnalysis(
                    project_name="High-Throughput Microservices Platform",
                    relevance_score=9,
                    tech_stack_used=["Python", "FastAPI", "PostgreSQL", "Redis"],
                    architecture_type="Microservices & Event-Driven",
                    quantifiable_scale="35M+ daily requests, <50ms median latency",
                    suggested_interview_probes=["Probe Redis cache invalidation strategies under high concurrency"]
                )
            ],
            experience_gaps_and_red_flags=ExperienceGapsAndRedFlags(
                technical_gaps=[
                    SkillGap(
                        missing_skill="Distributed Rate Limiting at API Gateway Layer",
                        jd_importance="Critical",
                        probing_strategy="Probe sliding window Redis rate limiters in FastAPI/API Gateways."
                    )
                ],
                resume_red_flags=[
                    RedFlagItem(
                        flag_type="Claim Verification",
                        description="Claims sub-35ms median response latency across 35M daily requests without specifying database cache hit ratio.",
                        probe_question="What was your database read/write ratio and cache hit percentage to maintain sub-35ms median latency?"
                    )
                ]
            )
        )

        fallback_rubric = AnswerRubric(
            poor_answer_indicators=["Generic definitions without code or metrics", "Inability to explain trade-offs"],
            good_answer_indicators=["Explains architecture clearly with correct terminology", "Cites production experiences"],
            bar_raiser_indicators=["Proactively discusses failure modes, memory leaks, trade-offs, and scale limits"]
        )

        fallback_questions = [
            QuestionItem(
                id=1,
                tier="Intro & Behavioral",
                topic="Personal Intro & Identity",
                difficulty="Mid",
                question_text=f"Welcome! To start off, please introduce yourself and tell us what key achievements defined your recent engineering work.",
                resume_context="Candidate background and identity check",
                expected_keywords=["background", "achievements", "engineering", "projects"],
                rubric=fallback_rubric,
                followup_if_strong="What was the most rewarding aspect of those achievements?",
                followup_if_weak="Could you briefly summarize your primary tech stack?"
            ),
            QuestionItem(
                id=2,
                tier="Intro & Behavioral",
                topic="Culture & Personality Probe",
                difficulty="Mid",
                question_text="Outside of pure coding, what hobbies or personal interests keep you curious and energized?",
                resume_context="Evaluating communication style and culture fit",
                expected_keywords=["hobbies", "passions", "learning", "collaboration"],
                rubric=fallback_rubric,
                followup_if_strong="How has that interest influenced your problem-solving style at work?",
                followup_if_weak="What do you enjoy doing most in your downtime?"
            ),
            QuestionItem(
                id=3,
                tier="Role Alignment",
                topic="Role Fit & Motivation",
                difficulty=target_seniority if target_seniority in ["Junior", "Mid", "Senior", "Lead", "Staff"] else "Senior",
                question_text=f"Why do you believe your skills make you a strong fit for this {role} position at {company}?",
                resume_context="Evaluating candidate alignment with JD requirements",
                expected_keywords=["fit", "motivation", "skills", "impact"],
                rubric=fallback_rubric,
                followup_if_strong="What specific engineering challenge here excites you the most?",
                followup_if_weak="Which requirement in the job description aligns best with your past work?"
            ),
            QuestionItem(
                id=4,
                tier="Work Experience",
                topic="Team Collaboration & Impact",
                difficulty="Mid",
                question_text="Tell me about a time you had an engineering disagreement with a teammate. How did you resolve it?",
                resume_context="Past work experience and team interaction check",
                expected_keywords=["collaboration", "resolution", "trade-offs", "communication"],
                rubric=fallback_rubric,
                followup_if_strong="How did that outcome improve your team's technical consensus long-term?",
                followup_if_weak="What steps did you take to reach a compromise?"
            ),
            QuestionItem(
                id=5,
                tier="Work Experience",
                topic="Organizational Impact & Delivery",
                difficulty="Senior",
                question_text="Describe a production incident where your service failed. How did you handle triage and root cause analysis?",
                resume_context="Production responsibility and incident management check",
                expected_keywords=["incident", "root cause", "post-mortem", "resilience"],
                rubric=fallback_rubric,
                followup_if_strong="What automated safeguards did you implement to ensure it never happens again?",
                followup_if_weak="How did you communicate the outage to stakeholders?"
            ),
            QuestionItem(
                id=6,
                tier="Project Deep Dive",
                topic="Project Architecture",
                difficulty="Senior",
                question_text="Walk me through the high-level architecture of your primary microservice platform project.",
                resume_context="Deep dive into top resume project",
                expected_keywords=["microservices", "architecture", "database", "API"],
                rubric=fallback_rubric,
                followup_if_strong="What was the single largest scale bottleneck you encountered in that design?",
                followup_if_weak="What basic framework or libraries did you rely on?"
            ),
            QuestionItem(
                id=7,
                tier="Project Deep Dive",
                topic="Project Implementation & Trade-offs",
                difficulty="Senior",
                question_text="In your data ingestion pipeline project, what trade-offs did you make between throughput and data consistency?",
                resume_context="Technical trade-off evaluation on resume project",
                expected_keywords=["trade-offs", "throughput", "consistency", "latency"],
                rubric=fallback_rubric,
                followup_if_strong="How would your design change if data volume doubled overnight?",
                followup_if_weak="Did you prioritize speed or exactness in that pipeline?"
            ),
            QuestionItem(
                id=8,
                tier="Project Deep Dive",
                topic="Technology Selection",
                difficulty="Mid",
                question_text="Why did you select your specific database choice over alternatives for that primary platform?",
                resume_context="Evaluating technical decision-making on resume project",
                expected_keywords=["database", "PostgreSQL", "schema", "indexing"],
                rubric=fallback_rubric,
                followup_if_strong="Under what workload conditions would that database choice fail?",
                followup_if_weak="What features of that database were most useful?"
            ),
            QuestionItem(
                id=9,
                tier="Core Technical",
                topic="Concurrency & Async Processing",
                difficulty="Mid",
                question_text="How does asynchronous execution process requests under high concurrency?",
                resume_context="Verification of async task execution",
                expected_keywords=["async", "await", "event loop", "non-blocking"],
                rubric=fallback_rubric,
                followup_if_strong="How do you handle CPU-bound tasks without blocking the event loop?",
                followup_if_weak="What is the difference between synchronous and asynchronous code?"
            ),
            QuestionItem(
                id=10,
                tier="Core Technical",
                topic="Database Query Optimization",
                difficulty="Senior",
                question_text="How do you debug and optimize a slow database query using execution plans?",
                resume_context="Database query optimization skills",
                expected_keywords=["EXPLAIN ANALYZE", "B-Tree index", "sequential scan", "query plan"],
                rubric=fallback_rubric,
                followup_if_strong="How do partial or composite indexes alter index scan choices in PostgreSQL?",
                followup_if_weak="What is an index and why does it speed up queries?"
            ),
            QuestionItem(
                id=11,
                tier="Core Technical",
                topic="Caching Strategies",
                difficulty="Mid",
                question_text="How do you prevent cache stampedes and thundering herd problems during traffic surges?",
                resume_context="Redis caching patterns",
                expected_keywords=["Redis", "Cache-Aside", "TTL jitter", "mutex lock"],
                rubric=fallback_rubric,
                followup_if_strong="How do you implement distributed locking via Redis safely?",
                followup_if_weak="What is TTL in a Redis cache?"
            ),
            QuestionItem(
                id=12,
                tier="Core Technical",
                topic="Distributed Messaging",
                difficulty="Mid",
                question_text="Compare message delivery guarantees and ordering in Kafka vs RabbitMQ.",
                resume_context="Async messaging experience",
                expected_keywords=["Kafka", "RabbitMQ", "partitions", "idempotency", "at-least-once"],
                rubric=fallback_rubric,
                followup_if_strong="How do you handle out-of-order event delivery in a distributed partition pipeline?",
                followup_if_weak="What is a message broker and why use queues?"
            ),
            QuestionItem(
                id=13,
                tier="Core Technical",
                topic="API Security & Rate Limiting",
                difficulty="Mid",
                question_text="How do you design a distributed rate limiter at the API gateway layer to protect downstream services?",
                resume_context="API gateway and security understanding",
                expected_keywords=["rate limit", "sliding window", "Redis", "API Gateway"],
                rubric=fallback_rubric,
                followup_if_strong="How do you handle rate limit synchronization across multiple gateway nodes?",
                followup_if_weak="What HTTP status code is returned when a client hits a rate limit?"
            ),
            QuestionItem(
                id=14,
                tier="System Design",
                topic="High Availability & Resilience",
                difficulty="Senior",
                question_text="How do you design a fault-tolerant system that gracefully handles downstream microservice outages?",
                resume_context="System design resilience check",
                expected_keywords=["circuit breaker", "retries", "fallback", "bulkhead"],
                rubric=fallback_rubric,
                followup_if_strong="How do you avoid cascading failures when downstream services recover?",
                followup_if_weak="What is a circuit breaker pattern in microservices?"
            ),
            QuestionItem(
                id=15,
                tier="System Design",
                topic="Scalability & Distributed State",
                difficulty="Senior",
                question_text="How do you ensure zero-downtime database schema migrations for high-traffic multi-tenant systems?",
                resume_context="Advanced distributed data engineering check",
                expected_keywords=["zero-downtime", "dual-write", "schema migration", "backward-compatible"],
                rubric=fallback_rubric,
                followup_if_strong="How do you verify data consistency during the dual-write phase?",
                followup_if_weak="Why can adding a column with a default value lock large tables?"
            )
        ]

        fallback_behavior = InterviewerBehavior(
            session_id=session_id,
            persona="Eva",
            target_company=company,
            candidate_name="Candidate",
            target_role=role,
            interviewer_system_prompt=fallback_system_prompt,
            behavior_rules=[
                "Maximum 1-2 sentences per response for low-latency streaming voice execution",
                "Maintain direct, professional, conversational roleplay persona",
                "Probe architectural trade-offs, edge cases, and failure modes"
            ]
        )

        return Stage2Output(
            session_id=session_id,
            resume_analysis=fallback_analysis,
            interview_questions=fallback_questions,
            interviewer_behavior=fallback_behavior
        )


# Backward compatibility alias
def generate_stage2_output(
    session_id: str,
    jd_text: str | dict[str, Any],
    resume_path: str,
    target_seniority: str = "Senior",
    output_dir: str = None
) -> Stage2Output:
    return Stage2Pipeline().run(session_id, jd_text, resume_path, target_seniority, output_dir)

def generate_fallback_stage2_output(
    session_id: str,
    target_seniority: str = "Senior"
) -> Stage2Output:
    return Stage2Pipeline.generate_fallback_output(session_id, target_seniority=target_seniority)
