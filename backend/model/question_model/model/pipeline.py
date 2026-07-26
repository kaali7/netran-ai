"""
Netran AI — Stage 2: Contextual Question & Behavioral Prompt Engine
Module: pipeline.py
Description: Master Stage2Pipeline orchestrator generating the 15-question tiered interview tree
             and custom latency-constrained system prompt via Gemini 3.6 Flash.
"""

import json
import logging
import os
import time
from typing import Optional
from google import genai
from google.genai import types

try:
    from .config import Stage2Config
    from .schemas import Stage2Output, QuestionItem
    from .prompts import STAGE2_FULL_PROMPT_TEMPLATE, FALLBACK_SYSTEM_PROMPT_TEMPLATE
    from .prompt_builder import PromptBuilder
    from .resume_parser import ResumeParser
    from .cache import Stage2Cache
except ImportError:
    try:
        from model.question_model.model.config import Stage2Config
        from model.question_model.model.schemas import Stage2Output, QuestionItem
        from model.question_model.model.prompts import STAGE2_FULL_PROMPT_TEMPLATE, FALLBACK_SYSTEM_PROMPT_TEMPLATE
        from model.question_model.model.prompt_builder import PromptBuilder
        from model.question_model.model.resume_parser import ResumeParser
        from model.question_model.model.cache import Stage2Cache
    except ImportError:
        from config import Stage2Config
        from schemas import Stage2Output, QuestionItem
        from prompts import STAGE2_FULL_PROMPT_TEMPLATE, FALLBACK_SYSTEM_PROMPT_TEMPLATE
        from prompt_builder import PromptBuilder
        from resume_parser import ResumeParser
        from cache import Stage2Cache

logger = logging.getLogger(__name__)


class Stage2Pipeline:
    """Master pipeline execution class for Stage 2 (Question & Behavioral Prompt Engine)."""

    def __init__(self, config: Optional[Stage2Config] = None):
        self.config = config or Stage2Config.from_env()
        self.cache = Stage2Cache()
        self.resume_parser = ResumeParser()
        self.prompt_builder = PromptBuilder()

    def run(
        self,
        session_id: str,
        jd_text: str,
        resume_path: str,
        target_seniority: str = "Mid",
        output_dir: Optional[str] = None
    ) -> Stage2Output:
        """
        Core reasoning engine leveraging Gemini to generate structured interview questions
        and the behavioral system prompt based on JD and Candidate Resume.
        """
        # 1. Parse resume
        try:
            resume_text = self.resume_parser.parse(resume_path)
        except Exception as e:
            logger.error(f"Failed to parse resume: {e}")
            raise

        # 2. Check SQLite cache first for instant re-runs (<1ms)
        cached_output = self.cache.get(
            jd_text=jd_text,
            resume_text=resume_text,
            target_seniority=target_seniority,
            session_id=session_id
        )
        if cached_output:
            logger.info("Loaded Stage 2 question tree & system prompt from SQLite cache!")
            if output_dir:
                self.save_artifacts(output_dir, session_id, target_seniority, cached_output)
            return cached_output

        api_key = self.config.gemini_api_key
        model = self.config.gemini_model or "gemini-3.6-flash"

        if not api_key:
            raise ValueError("GEMINI_API_KEY is not configured.")

        client = genai.Client(api_key=api_key)
        prompt_instructions = self.prompt_builder.build_instructions(target_seniority)

        full_prompt = STAGE2_FULL_PROMPT_TEMPLATE.format(
            resume_text=resume_text,
            jd_text=jd_text,
            prompt_instructions=prompt_instructions
        )

        logger.info("Calling Gemini for Stage 2 Question Generation...")
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
                stage2_output = self.generate_fallback_output(session_id, target_seniority)
            else:
                stage2_output = Stage2Output.model_validate_json(response.text)
                stage2_output.session_id = session_id

            # Save to SQLite cache
            self.cache.set(jd_text, resume_text, target_seniority, stage2_output)

        except Exception as e:
            logger.warning(f"Gemini generation exception ({e}). Utilizing fallback generator.")
            stage2_output = self.generate_fallback_output(session_id, target_seniority)

        if output_dir:
            self.save_artifacts(output_dir, session_id, target_seniority, stage2_output)

        return stage2_output

    @staticmethod
    def save_artifacts(output_dir: str, session_id: str, target_seniority: str, stage2_output: Stage2Output):
        """Saves interview_questions.json, interviewer_behavior.json, and system_prompt.txt."""
        os.makedirs(output_dir, exist_ok=True)

        questions_path = os.path.join(output_dir, "interview_questions.json")
        with open(questions_path, "w", encoding="utf-8") as f:
            json.dump([q.model_dump() for q in stage2_output.question_tree], f, indent=2)

        behavior_path = os.path.join(output_dir, "interviewer_behavior.json")
        behavior_payload = {
            "session_id": session_id,
            "persona": "Eva",
            "target_seniority": target_seniority,
            "interviewer_system_prompt": stage2_output.interviewer_system_prompt,
            "behavior_rules": [
              "Maximum 1-2 sentences per response for low-latency streaming voice execution",
              "Maintain direct, professional, conversational roleplay persona",
              "Probe architectural trade-offs, edge cases, and failure modes"
            ]
        }
        with open(behavior_path, "w", encoding="utf-8") as f:
            json.dump(behavior_payload, f, indent=2)

        prompt_path = os.path.join(output_dir, "system_prompt.txt")
        with open(prompt_path, "w", encoding="utf-8") as f:
            f.write(stage2_output.interviewer_system_prompt)

        logger.info(f"Stage 2 output artifacts saved to {output_dir}")

    @staticmethod
    def generate_fallback_output(session_id: str, target_seniority: str = "Senior") -> Stage2Output:
        """Generates structured fallback Stage2Output when LLM API is unavailable."""
        fallback_prompt = FALLBACK_SYSTEM_PROMPT_TEMPLATE.format(target_seniority=target_seniority)
        fallback_questions = [
            QuestionItem(id=1, topic="Asynchronous Execution", difficulty="Junior", question_text="Explain the Python asyncio event loop and cooperative multitasking.", expected_keywords=["event loop", "async", "await"], resume_reference=None),
            QuestionItem(id=2, topic="Database Indexing", difficulty="Junior", question_text="How do B-Tree indexes operate in PostgreSQL?", expected_keywords=["B-Tree", "indexing", "lookup"], resume_reference=None),
            QuestionItem(id=3, topic="REST vs gRPC", difficulty="Mid", question_text="What are the trade-offs between gRPC and RESTful HTTP APIs?", expected_keywords=["Protobuf", "gRPC", "HTTP/2"], resume_reference=None),
            QuestionItem(id=4, topic="Caching Strategies", difficulty="Mid", question_text="How do you handle cache invalidation and thundering herd in Redis?", expected_keywords=["Redis", "cache-aside", "TTL"], resume_reference=None),
            QuestionItem(id=5, topic="Message Queues", difficulty="Mid", question_text="Compare Apache Kafka and RabbitMQ for distributed messaging.", expected_keywords=["Kafka", "partitions", "RabbitMQ"], resume_reference=None),
            QuestionItem(id=6, topic="Microservices Design", difficulty="Mid", question_text="How do you enforce idempotency in background microservice tasks?", expected_keywords=["idempotency", "UUID", "state"], resume_reference=None),
            QuestionItem(id=7, topic="Database Connection Pooling", difficulty="Mid", question_text="How does PgBouncer prevent database connection starvation?", expected_keywords=["PgBouncer", "connection pool", "PostgreSQL"], resume_reference=None),
            QuestionItem(id=8, topic="Docker Containerization", difficulty="Mid", question_text="How do multi-stage Docker builds reduce image size?", expected_keywords=["multi-stage", "Docker", "caching"], resume_reference=None),
            QuestionItem(id=9, topic="Kubernetes Scaling", difficulty="Mid", question_text="Explain how Horizontal Pod Autoscaler (HPA) triggers pod scaling.", expected_keywords=["HPA", "metrics", "Kubernetes"], resume_reference=None),
            QuestionItem(id=10, topic="System Security", difficulty="Mid", question_text="How do you secure inter-service communication with mTLS?", expected_keywords=["mTLS", "certificates", "TLS"], resume_reference=None),
            QuestionItem(id=11, topic="CI/CD Pipelines", difficulty="Mid", question_text="How do rolling deployments ensure zero downtime?", expected_keywords=["rolling update", "blue-green", "deployment"], resume_reference=None),
            QuestionItem(id=12, topic="State Management", difficulty="Mid", question_text="How do you maintain state consistency across distributed databases?", expected_keywords=["Saga pattern", "transactions", "eventual consistency"], resume_reference=None),
            QuestionItem(id=13, topic="System Architecture", difficulty="Senior", question_text="Design a scalable backend processing 50,000 requests per second.", expected_keywords=["load balancing", "sharding", "rate limiting"], resume_reference=None),
            QuestionItem(id=14, topic="Distributed Locks", difficulty="Senior", question_text="How does Redlock guarantee distributed locking across Redis nodes?", expected_keywords=["Redlock", "DLM", "quorum"], resume_reference=None),
            QuestionItem(id=15, topic="Observability & Tracing", difficulty="Senior", question_text="How does OpenTelemetry propagate trace context across microservices?", expected_keywords=["OpenTelemetry", "trace ID", "spans"], resume_reference=None),
        ]
        return Stage2Output(
            session_id=session_id,
            interviewer_system_prompt=fallback_prompt,
            question_tree=fallback_questions
        )


# Backward compatibility wrappers
def generate_stage2_output(
    session_id: str,
    jd_text: str,
    resume_path: str,
    target_seniority: str = "Mid",
    output_dir: str = None
) -> Stage2Output:
    return Stage2Pipeline().run(session_id, jd_text, resume_path, target_seniority, output_dir)

def generate_fallback_stage2_output(session_id: str, target_seniority: str = "Senior") -> Stage2Output:
    return Stage2Pipeline.generate_fallback_output(session_id, target_seniority)
