"""
Netran AI — Stage 2: Contextual Question & Behavioral Prompt Engine
Module: question_generator.py
Description: Core reasoning engine using Gemini 3.6 Flash and Pydantic schemas to generate
             the 15-question tiered interview tree (`interview_questions.json`) and the custom
             latency-constrained system prompt (`system_prompt.txt`).
"""

import json
import logging
import os
from typing import Optional
from pydantic import ValidationError

from google import genai
from google.genai import types

from .config import GEMINI_API_KEY, GEMINI_MODEL
from .schemas import Stage2Output
from .prompt_builder import get_system_prompt_instructions
from .resume_parser import parse_resume
try:
    from .cache import get_cached_stage2_output, set_cached_stage2_output
except ImportError:
    try:
        from model.question_model.model.cache import get_cached_stage2_output, set_cached_stage2_output
    except ImportError:
        from cache import get_cached_stage2_output, set_cached_stage2_output

logger = logging.getLogger(__name__)

def generate_stage2_output(
    session_id: str,
    jd_text: str,
    resume_path: str,
    target_seniority: str = "Mid",
    output_dir: str = None
) -> Stage2Output:
    """
    Core reasoning engine leveraging Gemini to generate structured interview questions
    and the behavioral system prompt based on JD and Candidate Resume.
    """
    # 1. Parse the resume
    try:
        resume_text = parse_resume(resume_path)
    except Exception as e:
        logger.error(f"Failed to parse resume: {e}")
        raise

    # 2. Check SQLite cache first for instant re-runs (<1ms)
    cached_output = get_cached_stage2_output(
        jd_text=jd_text,
        resume_text=resume_text,
        target_seniority=target_seniority,
        session_id=session_id
    )
    if cached_output:
        logger.info("Loaded Stage 2 question tree & system prompt from SQLite cache!")
        if output_dir:
            _save_stage2_artifacts(output_dir, session_id, target_seniority, cached_output)
        return cached_output

    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not configured.")

    client = genai.Client(api_key=GEMINI_API_KEY)

    # 2. Build instructions for prompt generation
    prompt_instructions = get_system_prompt_instructions(target_seniority)

    # 3. Construct the full Gemini prompt
    full_prompt = f"""
You are an expert technical interviewer and AI system designer.
Your task is to analyze the Job Description (JD) and the Candidate's Resume to output a structured JSON containing:
1. An ordered Question Tree (15 questions).
2. The custom System Prompt for the AI interviewer.

### Candidate Resume:
```
{resume_text}
```

### Job Description / Key Pillars:
```
{jd_text}
```

### Instructions for Question Tree:
- Perform Skill Overlap & Gap Matrix mapping. 
- For Strong Overlap, generate high-difficulty production/debugging questions.
- For Missing / Unlisted Skills, generate foundational concept verification questions to detect technical blindspots.
- Probe specific projects from the resume.
- Generate exactly 15 questions, tiered as:
  * Tier 1 (Warmup/Foundations): Questions 1-2
  * Tier 2 (Core Arch/Production): Questions 3-12
  * Tier 3 (Advanced/System Design): Questions 13-15
- Difficulty levels must be "Junior", "Mid", or "Senior".
- Topics must be distinct technical domains.

### Instructions for System Prompt:
{prompt_instructions}

Return exactly the JSON object matching the requested schema.
"""

    logger.info("Calling Gemini for Stage 2 Question Generation...")
    
    try:
        response = None
        last_err = None
        for attempt in range(1, 4):
            try:
                response = client.models.generate_content(
                    model=GEMINI_MODEL,
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
                err_msg = str(e)
                logger.warning(f"Gemini API attempt {attempt}/3 error: {err_msg[:120]}")
                if attempt < 3:
                    import time
                    time.sleep(3 * attempt)

        if not response or not response.text:
            logger.warning(f"Gemini API quota exhausted or connection unavailable ({last_err}). Utilizing fallback question generator.")
            stage2_output = generate_fallback_stage2_output(session_id, target_seniority)
        else:
            stage2_output = Stage2Output.model_validate_json(response.text)
            stage2_output.session_id = session_id

        # Save successfully generated output to SQLite cache
        set_cached_stage2_output(jd_text, resume_text, target_seniority, stage2_output)

    except Exception as e:
        logger.warning(f"Gemini generation exception ({e}). Utilizing fallback question generator.")
        stage2_output = generate_fallback_stage2_output(session_id, target_seniority)

    # 4. Save artifacts if output_dir is provided
    if output_dir:
        _save_stage2_artifacts(output_dir, session_id, target_seniority, stage2_output)

    return stage2_output


def _save_stage2_artifacts(output_dir: str, session_id: str, target_seniority: str, stage2_output: Stage2Output):
    """Helper function to save interview_questions.json and interviewer_behavior.json artifacts."""
    os.makedirs(output_dir, exist_ok=True)
    
    # File 1: Generated 15-question interview tree
    questions_path = os.path.join(output_dir, "interview_questions.json")
    with open(questions_path, "w", encoding="utf-8") as f:
        json.dump([q.model_dump() for q in stage2_output.question_tree], f, indent=2)
        
    # File 2: LLM interviewer behavior & runtime system prompt
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

    # File 3: Plain text system prompt for voice loop
    prompt_path = os.path.join(output_dir, "system_prompt.txt")
    with open(prompt_path, "w", encoding="utf-8") as f:
        f.write(stage2_output.interviewer_system_prompt)
        
    logger.info(f"Stage 2 output artifacts saved to {output_dir}")


def generate_fallback_stage2_output(session_id: str, target_seniority: str = "Senior") -> Stage2Output:
    """Generates structured fallback Stage2Output when LLM API quota is exhausted or offline."""
    from .schemas import QuestionItem
    fallback_prompt = (
        f"You are Eva, a lead technical interviewer conducting a live technical interview for a {target_seniority} role. "
        "Keep all responses strictly to 1-2 concise, conversational sentences for low latency voice execution. "
        "Probe architectural trade-offs, edge cases, and technical implementation details."
    )
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
