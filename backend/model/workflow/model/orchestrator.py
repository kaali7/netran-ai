"""
Netran AI — Workflow Orchestrator
Module: orchestrator.py
Description: Master end-to-end pipeline coordinator linking Stage 1 (Research) -> Stage 2 (Question Engine)
             -> Stage 3 (Voice Interview) -> Stage 4 (Reports Engine) in background threads with live UI progress callbacks.
"""

import os
import json
import time
import logging
from datetime import datetime
from typing import Callable, Optional, Dict, Any

try:
    from .config import SESSIONS_BASE_DIR, PROCESS_BASE_DIR, OUTPUT_BASE_DIR
    from .voice_engine import WorkflowVoiceEngine
except ImportError:
    try:
        from model.workflow.model.config import SESSIONS_BASE_DIR, PROCESS_BASE_DIR, OUTPUT_BASE_DIR
        from model.workflow.model.voice_engine import WorkflowVoiceEngine
    except ImportError:
        from config import SESSIONS_BASE_DIR, PROCESS_BASE_DIR, OUTPUT_BASE_DIR
        from voice_engine import WorkflowVoiceEngine

try:
    import model.research_model.model.pipeline as research_pipeline
except ImportError:
    try:
        import research_model.model.pipeline as research_pipeline
    except ImportError:
        import pipeline as research_pipeline

try:
    import model.question_model.model.question_generator as question_generator
except ImportError:
    import question_model.model.question_generator as question_generator

try:
    import model.reports_model.model.report_builder as report_builder
except ImportError:
    import reports_model.model.report_builder as report_builder

logger = logging.getLogger(__name__)

def create_workflow_directories(session_id: Optional[str] = None) -> tuple[str, str, str]:
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
    session_id: Optional[str] = None,
    target_seniority: str = "Mid",
    max_questions: Optional[int] = None,
    status_callback: Optional[Callable[[str, str, int, Dict[str, Any]], None]] = None,
    voice_callback: Optional[Callable[[int, str, str, str], None]] = None,
    voice_engine_ref: Optional[list] = None
) -> Dict[str, Any]:
    """
    Master pipeline orchestrator running Stage 1 -> 2 -> 3 -> 4.
    Middle processing artifacts are stored in process_dir (model/workflow/test/process/).
    Final report output artifacts are stored in output_dir (model/workflow/test/output/).
    """
    def notify(stage: str, msg: str, pct: int, payload: Dict[str, Any] = None):
        logger.info(f"[{stage}] ({pct}%) {msg}")
        if status_callback:
            status_callback(stage, msg, pct, payload or {})

    session_id, process_dir, output_dir = create_workflow_directories(session_id)
    results = {"session_id": session_id, "process_dir": process_dir, "output_dir": output_dir, "session_dir": output_dir}
    
    # --- STAGE 1: RESEARCH MODEL ---
    notify("Stage 1: Research", "Initializing Market Intelligence & JD Analysis...", 5)
    stage1_res = research_pipeline.run_pipeline(
        jd_text=jd_text,
        status_callback=lambda msg: notify("Stage 1: Research", msg, 15),
        output_dir=process_dir
    )
    rubric = stage1_res.rubric if hasattr(stage1_res, 'rubric') else stage1_res
    results["rubric"] = rubric
    notify("Stage 1: Research", "Evaluation Rubric generated successfully!", 25, {"rubric": rubric.model_dump()})
    
    # --- STAGE 2: QUESTION ENGINE ---
    notify("Stage 2: Question Engine", "Generating role-specific Question Tree & System Prompt...", 30)
    stage2_output = question_generator.generate_stage2_output(
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
    
    # Inject Stage 2 question tree directly in-memory — do NOT read from disk.
    # This ensures the voice engine always uses the freshly generated (or cache-retrieved)
    # question tree for this specific session, not any leftover file from a previous run.
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
    report_payload = report_builder.build_report(session_dir=process_dir, output_dir=output_dir)
    results["report"] = report_payload
    notify("Stage 4: Evaluation Report", "Final Candidate Evaluation Report generated successfully!", 100, {
        "report": report_payload.model_dump()
    })
    
    return results
