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
from typing import Any, Dict

from google import genai
from google.genai import types

try:
    from .cache import Stage2Cache
    from .config import Stage2Config
    from .prompt_builder import Stage2PromptBuilder
    from .prompts import FALLBACK_SYSTEM_PROMPT_TEMPLATE, STAGE2_FULL_PROMPT_TEMPLATE
    from .resume_parser import ResumeParser
    from .schemas import (
        AnswerRubric,
        InterviewerBehavior,
        QuestionItem,
        ResumeAnalysis,
        SkillGap,
        SkillMatch,
        Stage2Output,
    )
except ImportError:
    try:
        from model.question_model.model.cache import Stage2Cache
        from model.question_model.model.config import Stage2Config
        from model.question_model.model.prompt_builder import Stage2PromptBuilder
        from model.question_model.model.prompts import (
            FALLBACK_SYSTEM_PROMPT_TEMPLATE,
            STAGE2_FULL_PROMPT_TEMPLATE,
        )
        from model.question_model.model.resume_parser import ResumeParser
        from model.question_model.model.schemas import (
            AnswerRubric,
            InterviewerBehavior,
            QuestionItem,
            ResumeAnalysis,
            SkillGap,
            SkillMatch,
            Stage2Output,
        )
    except ImportError:
        from cache import Stage2Cache
        from config import Stage2Config
        from prompt_builder import Stage2PromptBuilder
        from prompts import FALLBACK_SYSTEM_PROMPT_TEMPLATE, STAGE2_FULL_PROMPT_TEMPLATE
        from resume_parser import ResumeParser
        from schemas import (
            AnswerRubric,
            InterviewerBehavior,
            QuestionItem,
            ResumeAnalysis,
            SkillGap,
            SkillMatch,
            Stage2Output,
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
        jd_input: str | Dict[str, Any],
        resume_path: str,
        target_seniority: str = "Senior",
        output_dir: str | None = None
    ) -> Stage2Output:
        """
        Core reasoning engine leveraging Gemini to generate structured resume analysis,
        15 tiered branching questions with rubrics, and the interviewer behavior prompt.
        """
        # 1. Standardize job context from input (raw text, dict, or Stage 1 JSON)
        job_dict: Dict[str, Any] = {}
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

        api_key = self.config.gemini_api_key
        model = self.config.gemini_model or "gemini-3.6-flash"

        if not api_key:
            raise ValueError("GEMINI_API_KEY is not configured.")

        client = genai.Client(api_key=api_key)
        prompt_instructions = self.prompt_builder.build_instructions(effective_seniority)

        full_prompt = STAGE2_FULL_PROMPT_TEMPLATE.format(
            resume_text=resume_text,
            stage1_rubric_json=job_context["rubric_json"],
            prompt_instructions=prompt_instructions
        )

        logger.info("Calling Gemini 3.6 Flash for Stage 2 Synthesis...")
        try:
            response = None
            last_err = None
            for attempt in range(1, 4):
                try:
                    response = client.models.generate_content(
                        model=model,
                        contents=full_prompt,
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json",
                            response_schema=Stage2Output,
                            temperature=0.2,
                        )
                    )
                    if response and response.text:
                        break
                except Exception as e:
                    last_err = e
                    logger.warning(f"Gemini API attempt {attempt}/3 error: {str(e)[:120]}")
                    if attempt < 3:
                        time.sleep(3 * attempt)

            if not response or not response.text:
                logger.warning(f"Gemini API quota exhausted or unavailable ({last_err}). Utilizing fallback generator.")
                stage2_output = self.generate_fallback_output(
                    session_id=session_id,
                    company=job_context.get("company", "Target Company"),
                    role=job_context.get("role", "Target Role"),
                    target_seniority=effective_seniority
                )
            else:
                stage2_output = Stage2Output.model_validate_json(response.text)
                stage2_output.session_id = session_id

            # Save to SQLite cache
            self.cache.set(jd_text_for_hash, resume_text, effective_seniority, stage2_output)

        except Exception as e:
            logger.warning(f"Gemini generation exception ({e}). Utilizing fallback generator.")
            stage2_output = self.generate_fallback_output(
                session_id=session_id,
                company=job_context.get("company", "Target Company"),
                role=job_context.get("role", "Target Role"),
                target_seniority=effective_seniority
            )

        if output_dir:
            self.save_artifacts(output_dir, session_id, effective_seniority, stage2_output)

        return stage2_output

    @staticmethod
    def save_artifacts(output_dir: str, session_id: str, target_seniority: str, stage2_output: Stage2Output):
        """
        Saves all 4 Stage 2 session artifacts into output_dir:
        1. resume_analysis.json
        2. interview_questions.json
        3. interviewer_behavior.json
        4. system_prompt.txt
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

        # 4. system_prompt.txt
        prompt_path = os.path.join(output_dir, "system_prompt.txt")
        with open(prompt_path, "w", encoding="utf-8") as f:
            f.write(stage2_output.interviewer_behavior.interviewer_system_prompt)

        logger.info(f"Stage 2 output session artifacts saved to {output_dir}")

    @staticmethod
    def generate_fallback_output(
        session_id: str,
        company: str = "Target Company",
        role: str = "Target Role",
        target_seniority: str = "Senior"
    ) -> Stage2Output:
        """Generates structured fallback Stage2Output when LLM API is unavailable."""
        fallback_system_prompt = FALLBACK_SYSTEM_PROMPT_TEMPLATE.format(
            company_name=company,
            role_title=role,
            target_seniority=target_seniority
        )

        fallback_analysis = ResumeAnalysis(
            matched_skills=[
                SkillMatch(skill="Python / Modern Tech Stack", resume_evidence="Demonstrated on candidate projects", proficiency_tier="Production Master"),
                SkillMatch(skill="REST / Microservices Architecture", resume_evidence="Built API microservices", proficiency_tier="Intermediate")
            ],
            missing_or_gap_skills=[
                SkillGap(missing_skill="High-Scale Distributed Caching", jd_importance="Critical", probing_strategy="Probe Redis cache-aside & TTL invalidation patterns.")
            ],
            resume_red_flags=["Vague metrics for database CPU reduction under load."],
            key_projects_to_probe=["Primary backend microservice platform", "Data ingestion pipeline"]
        )

        fallback_rubric = AnswerRubric(
            poor_answer_indicators=["Generic definitions without code or metrics", "Inability to explain trade-offs"],
            good_answer_indicators=["Explains architecture clearly with correct terminology", "Cites production experiences"],
            bar_raiser_indicators=["Proactively discusses failure modes, memory leaks, trade-offs, and scale limits"]
        )

        fallback_questions = [
            QuestionItem(
                id=1,
                tier="Tier 1 (Warmup)",
                topic="Architecture Foundations",
                difficulty=target_seniority if target_seniority in ["Junior", "Mid", "Senior", "Lead", "Staff"] else "Senior",
                question_text=f"Walk me through the high-level architecture of your primary project for the {role} position.",
                resume_context="Warmup check on core project experience",
                expected_keywords=["architecture", "microservices", "API", "database"],
                rubric=fallback_rubric,
                followup_if_strong="What was the single most difficult architectural bottleneck you encountered?",
                followup_if_weak="What basic framework or libraries did you rely on for routing and data validation?"
            ),
            QuestionItem(
                id=2,
                tier="Tier 1 (Warmup)",
                topic="Concurrency & Event Loop",
                difficulty="Mid",
                question_text="How does asynchronous execution process requests under high concurrency?",
                resume_context="Verification of async task execution",
                expected_keywords=["async", "await", "event loop", "non-blocking"],
                rubric=fallback_rubric,
                followup_if_strong="How do you handle CPU-bound tasks without blocking the main event loop?",
                followup_if_weak="What is the difference between synchronous and asynchronous code?"
            ),
            QuestionItem(
                id=3,
                tier="Tier 2 (Core Production)",
                topic="Database Engineering",
                difficulty="Senior",
                question_text="How do you debug and optimize a slow database query using execution plans?",
                resume_context="Database query optimization skills",
                expected_keywords=["EXPLAIN ANALYZE", "B-Tree index", "sequential scan", "query plan"],
                rubric=fallback_rubric,
                followup_if_strong="How do partial indexes or composite indexes alter index scan choices in PostgreSQL?",
                followup_if_weak="What is an index and why does it speed up SELECT queries?"
            ),
            QuestionItem(
                id=4,
                tier="Tier 2 (Core Production)",
                topic="Caching Strategies",
                difficulty="Mid",
                question_text="How do you prevent cache stampedes and thundering herd problems during traffic surges?",
                resume_context="Redis caching patterns",
                expected_keywords=["Redis", "Cache-Aside", "TTL jitter", "mutex lock"],
                rubric=fallback_rubric,
                followup_if_strong="How do you implement distributed locking via Redis or Redlock safely?",
                followup_if_weak="What is TTL in a Redis cache?"
            ),
            QuestionItem(
                id=5,
                tier="Tier 2 (Core Production)",
                topic="Distributed Messaging",
                difficulty="Mid",
                question_text="Compare message delivery guarantees and ordering in Kafka vs RabbitMQ.",
                resume_context="Async messaging experience",
                expected_keywords=["Kafka", "RabbitMQ", "partitions", "idempotency", "at-least-once"],
                rubric=fallback_rubric,
                followup_if_strong="How do you handle out-of-order event delivery in a distributed partition pipeline?",
                followup_if_weak="What is a message broker and why use queues?"
            ),
        ]

        # Populate remaining 10 questions to guarantee 15 questions total
        for qid in range(6, 16):
            q_tier = "Tier 2 (Core Production)" if qid <= 12 else "Tier 3 (System Design)"
            q_diff = "Senior" if qid >= 12 else "Mid"
            fallback_questions.append(
                QuestionItem(
                    id=qid,
                    tier=q_tier,
                    topic=f"System Design Topic {qid}",
                    difficulty=q_diff,
                    question_text=f"Technical assessment question {qid} for {role}: How do you ensure high availability and resilience under peak traffic?",
                    resume_context="General backend resilience check",
                    expected_keywords=["resilience", "scalability", "load balancing", "failover"],
                    rubric=fallback_rubric,
                    followup_if_strong="How would you design zero-downtime database schema migrations?",
                    followup_if_weak="How do health checks help load balancers detect failed nodes?"
                )
            )

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
    jd_text: str | Dict[str, Any],
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
