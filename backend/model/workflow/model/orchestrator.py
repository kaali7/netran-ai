"""
Netran AI — Workflow Orchestrator
Module: orchestrator.py
Description: Master end-to-end pipeline coordinator linking Stage 1 (Research) -> Stage 2 (Question Engine)
             -> Stage 3 (Voice Interview) -> Stage 4 (Reports Engine) in background threads with live UI progress callbacks.
"""

import os
import time
import logging
from datetime import datetime
from typing import Callable, Optional, Dict, Any

from config import SESSIONS_BASE_DIR
import model.pipeline as research_pipeline
import question_model.model.question_generator as question_generator
import reports_model.model.report_builder as report_builder
from voice_engine import WorkflowVoiceEngine

logger = logging.getLogger(__name__)

def create_session_directory(session_id: Optional[str] = None) -> tuple[str, str]:
    if not session_id:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_id = f"sess_{timestamp}"
    session_dir = os.path.join(SESSIONS_BASE_DIR, session_id)
    os.makedirs(session_dir, exist_ok=True)
    return session_id, session_dir

def run_full_pipeline(
    jd_text: str,
    resume_path: str,
    session_id: Optional[str] = None,
    target_seniority: str = "Mid",
    status_callback: Optional[Callable[[str, str, int, Dict[str, Any]], None]] = None,
    voice_callback: Optional[Callable[[int, str, str, str], None]] = None,
    voice_engine_ref: Optional[list] = None
) -> Dict[str, Any]:
    """
    Master pipeline orchestrator running Stage 1 -> 2 -> 3 -> 4.
    
    status_callback signature:
        callback(stage_name, message, progress_pct, payload)
    """
    def notify(stage: str, msg: str, pct: int, payload: Dict[str, Any] = None):
        logger.info(f"[{stage}] ({pct}%) {msg}")
        if status_callback:
            status_callback(stage, msg, pct, payload or {})

    session_id, session_dir = create_session_directory(session_id)
    results = {"session_id": session_id, "session_dir": session_dir}
    
    # --- STAGE 1: RESEARCH MODEL ---
    notify("Stage 1: Research", "Initializing Market Intelligence & JD Analysis...", 5)
    rubric = research_pipeline.run_pipeline(
        jd_text=jd_text,
        status_callback=lambda msg: notify("Stage 1: Research", msg, 15)
    )
    results["rubric"] = rubric
    notify("Stage 1: Research", "Evaluation Rubric generated successfully!", 25, {"rubric": rubric.model_dump()})
    
    # --- STAGE 2: QUESTION ENGINE ---
    notify("Stage 2: Question Engine", "Generating role-specific Question Tree & System Prompt...", 30)
    stage2_output = question_generator.generate_stage2_output(
        session_id=session_id,
        jd_text=jd_text,
        resume_path=resume_path,
        target_seniority=target_seniority,
        output_dir=session_dir
    )
    results["stage2_output"] = stage2_output
    notify("Stage 2: Question Engine", f"Generated {len(stage2_output.question_tree)} questions & dynamic system prompt.", 50, {
        "questions": [q.model_dump() for q in stage2_output.question_tree],
        "system_prompt": stage2_output.interviewer_system_prompt
    })
    
    # --- STAGE 3: VOICE INTERVIEW LOOP ---
    notify("Stage 3: Voice Interview", "Initializing Voice-to-Voice Loop engine...", 55)
    engine = WorkflowVoiceEngine(session_dir=session_dir, session_id=session_id)
    if voice_engine_ref is not None:
        voice_engine_ref.append(engine)
        
    engine.run_interview(
        status_callback=voice_callback,
        max_turns=len(stage2_output.question_tree)
    )
    notify("Stage 3: Voice Interview", "Voice interview completed & session manifest saved.", 85)
    
    # --- STAGE 4: REPORT ENGINE ---
    notify("Stage 4: Evaluation Report", "Synthesizing multimodal audio & technical report...", 90)
    report_payload = report_builder.build_report(session_dir=session_dir)
    results["report"] = report_payload
    notify("Stage 4: Evaluation Report", "Final Candidate Evaluation Report generated successfully!", 100, {
        "report": report_payload.model_dump()
    })
    
    return results
