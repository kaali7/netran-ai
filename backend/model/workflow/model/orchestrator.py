"""
Netran AI — Workflow Orchestrator
Module: orchestrator.py
Description: Master end-to-end pipeline coordinator linking Stage 1 (Research) -> Stage 2 (Question Engine)
             -> Stage 3 (Voice Interview) -> Stage 4 (Reports Engine) using clean, unified StagePipeline objects.
"""

import json
import logging
import os
from collections.abc import Callable
from datetime import datetime
from typing import Any

try:
    from .config import OUTPUT_BASE_DIR, PROCESS_BASE_DIR
    from .voice_engine import WorkflowVoiceEngine
except ImportError:
    from model.workflow.model.config import OUTPUT_BASE_DIR, PROCESS_BASE_DIR
    from model.workflow.model.voice_engine import WorkflowVoiceEngine

try:
    from model.research_model.model.pipeline import Stage1Pipeline
except ImportError:
    from research_model.model.pipeline import Stage1Pipeline

try:
    from model.question_model.model.pipeline import Stage2Pipeline
except ImportError:
    from question_model.model.pipeline import Stage2Pipeline

try:
    from model.reports_model.model.pipeline import Stage4Pipeline
except ImportError:
    from reports_model.model.pipeline import Stage4Pipeline

logger = logging.getLogger(__name__)


def create_workflow_directories(session_id: str | None = None) -> tuple[str, str, str]:
    if not session_id:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_id = f"sess_{timestamp}"
    process_dir = os.path.join(PROCESS_BASE_DIR, session_id)
    output_dir = os.path.join(OUTPUT_BASE_DIR, session_id)
    os.makedirs(process_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)
    return session_id, process_dir, output_dir


def run_full_pipeline(
    jd_text: str,
    resume_path: str,
    session_id: str | None = None,
    target_seniority: str = "Mid",
    max_questions: int | None = None,
    status_callback: Callable[[str, str, int, dict[str, Any]], None] | None = None,
    voice_callback: Callable[[int, str, str, str], None] | None = None,
    voice_engine_ref: list | None = None
) -> dict[str, Any]:
    """
    Master pipeline orchestrator running Stage 1 -> 2 -> 3 -> 4 using uniform StagePipelines.
    Middle processing artifacts are stored in process_dir (model/workflow/test/process/).
    Final report output artifacts are stored in output_dir (model/workflow/test/output/).
    """
    def notify(stage: str, msg: str, pct: int, payload: dict[str, Any] = None):
        logger.info(f"[{stage}] ({pct}%) {msg}")
        if status_callback:
            status_callback(stage, msg, pct, payload or {})

    session_id, process_dir, output_dir = create_workflow_directories(session_id)
    results = {"session_id": session_id, "process_dir": process_dir, "output_dir": output_dir, "session_dir": output_dir}

    # --- STAGE 1: RESEARCH MODEL ---
    notify("Stage 1: Research", "Initializing Market Intelligence & JD Analysis...", 5)
    stage1_pipeline = Stage1Pipeline()
    stage1_res = stage1_pipeline.run(
        jd_text=jd_text,
        status_callback=lambda msg: notify("Stage 1: Research", msg, 15),
        output_dir=process_dir
    )
    rubric = stage1_res.rubric if hasattr(stage1_res, 'rubric') else stage1_res
    results["rubric"] = rubric
    notify("Stage 1: Research", "Evaluation Rubric generated successfully!", 25, {"rubric": rubric.model_dump()})

    # --- STAGE 2: QUESTION ENGINE ---
    notify("Stage 2: Question Engine", "Generating role-specific Question Tree & System Prompt...", 30)
    stage2_pipeline = Stage2Pipeline()
    stage2_output = stage2_pipeline.run(
        session_id=session_id,
        jd_text=jd_text,
        resume_path=resume_path,
        target_seniority=target_seniority,
        output_dir=process_dir
    )
    if max_questions and max_questions < len(stage2_output.question_tree):
        stage2_output.question_tree = stage2_output.question_tree[:max_questions]
        questions_path = os.path.join(process_dir, "interview_questions.json")
        try:
            with open(questions_path, "w", encoding="utf-8") as f:
                json.dump([q.model_dump() for q in stage2_output.question_tree], f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to overwrite interview_questions.json with max_questions: {e}")

    results["stage2_output"] = stage2_output
    notify("Stage 2: Question Engine", f"Generated {len(stage2_output.question_tree)} questions & dynamic system prompt.", 50, {
        "questions": [q.model_dump() for q in stage2_output.question_tree],
        "system_prompt": stage2_output.interviewer_system_prompt
    })

    # --- STAGE 3: VOICE INTERVIEW LOOP ---
    notify("Stage 3: Voice Interview", "Initializing Voice-to-Voice Loop engine...", 55)
    engine = WorkflowVoiceEngine(session_dir=process_dir, session_id=session_id)
    engine.inject_question_tree(
        questions=[q.model_dump() for q in stage2_output.question_tree],
        system_prompt=stage2_output.interviewer_system_prompt
    )

    if voice_engine_ref is not None:
        voice_engine_ref.append(engine)

    stage3_max_turns = min(max_questions, len(stage2_output.question_tree)) if max_questions else len(stage2_output.question_tree)
    engine.run_interview(
        status_callback=voice_callback,
        max_turns=stage3_max_turns
    )
    notify("Stage 3: Voice Interview", "Voice interview completed & session manifest saved.", 85)

    # --- STAGE 4: REPORT ENGINE ---
    notify("Stage 4: Evaluation Report", "Synthesizing multimodal audio & technical report...", 90)
    stage4_pipeline = Stage4Pipeline()
    report_payload = stage4_pipeline.run(session_dir=process_dir, output_dir=output_dir)
    results["report"] = report_payload
    notify("Stage 4: Evaluation Report", "Final Candidate Evaluation Report generated successfully!", 100, {
        "report": report_payload.model_dump()
    })

    return results
