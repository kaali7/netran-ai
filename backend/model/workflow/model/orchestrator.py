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
    from .cache import WorkflowCache
    from .config import OUTPUT_BASE_DIR, PROCESS_BASE_DIR
    from .voice_engine import WorkflowVoiceEngine
except ImportError:
    try:
        from model.workflow.model.cache import WorkflowCache
        from model.workflow.model.config import OUTPUT_BASE_DIR, PROCESS_BASE_DIR
        from model.workflow.model.voice_engine import WorkflowVoiceEngine
    except ImportError:
        from cache import WorkflowCache
        from config import OUTPUT_BASE_DIR, PROCESS_BASE_DIR
        from voice_engine import WorkflowVoiceEngine

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

try:
    from model.research_model.model.schemas import Stage1Output
except ImportError:
    from research_model.model.schemas import Stage1Output

try:
    from model.question_model.model.schemas import Stage2Output
except ImportError:
    from question_model.model.schemas import Stage2Output

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
    target_seniority: str = "Senior",
    max_questions: int | None = None,
    status_callback: Callable[[str, str, int, dict[str, Any]], None] | None = None,
    voice_callback: Callable[[int, str, str, str], None] | None = None,
    voice_engine_ref: list[Any] | None = None,
    force_refresh: bool = False,
    confirm_start_callback: Callable[[], bool] | None = None
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

    # --- WORKFLOW CACHE RETRIEVAL ---
    if not force_refresh:
        try:
            wf_cache = WorkflowCache()
            cached_wf = wf_cache.get(jd_text, resume_path, target_seniority)
            if cached_wf:
                notify("Stage 1: Research", "Loaded existing market rubric from Workflow Cache (<1ms)!", 25)
                s1_dict = cached_wf.get("stage1", {})
                stage1_res = Stage1Output.model_validate(s1_dict)
                Stage1Pipeline.save_artifacts(process_dir, stage1_res)

                notify("Stage 2: Question Engine", "Loaded 15-question tree & system prompt from Workflow Cache (<1ms)!", 50)
                s2_dict = cached_wf.get("stage2", {})
                s2_dict["session_id"] = session_id
                stage2_output = Stage2Output.model_validate(s2_dict)
                
                if max_questions and max_questions < len(stage2_output.interview_questions):
                    stage2_output.interview_questions = stage2_output.interview_questions[:max_questions]
                
                Stage2Pipeline.save_artifacts(process_dir, session_id, target_seniority, stage2_output)

                results["rubric"] = stage1_res.rubric if hasattr(stage1_res, 'rubric') else stage1_res
                results["stage2_output"] = stage2_output

                notify("Stage 2: Question Engine", f"Loaded {len(stage2_output.interview_questions)} questions & dynamic system prompt from cache.", 50, {
                    "questions": [q.model_dump() for q in stage2_output.interview_questions],
                    "system_prompt": stage2_output.interviewer_behavior.interviewer_system_prompt,
                    "resume_analysis": stage2_output.resume_analysis.model_dump() if hasattr(stage2_output, 'resume_analysis') and stage2_output.resume_analysis else None
                })

                # --- USER CONFIRMATION PAUSE ---
                if confirm_start_callback is not None:
                    notify("Stage 2: Question Engine", "Question tree & Resume analysis ready (Cached). Awaiting confirmation to start live interview...", 50)
                    should_proceed = confirm_start_callback()
                    if not should_proceed:
                        logger.info("Interview workflow paused/cancelled by user at Stage 2 QuestionScreen.")
                        return results

                # --- STAGE 3: VOICE INTERVIEW LOOP ---
                notify("Stage 3: Voice Interview", "Initializing Voice-to-Voice Loop engine...", 55)
                engine = WorkflowVoiceEngine(session_dir=process_dir, session_id=session_id)
                engine.inject_question_tree(
                    questions=[q.model_dump() for q in stage2_output.interview_questions],
                    system_prompt=stage2_output.interviewer_behavior.interviewer_system_prompt
                )

                if voice_engine_ref is not None:
                    voice_engine_ref.append(engine)

                stage3_max_turns = min(max_questions, len(stage2_output.interview_questions)) if max_questions else len(stage2_output.interview_questions)
                engine.run_interview(
                    status_callback=voice_callback,
                    max_turns=stage3_max_turns
                )
                notify("Stage 3: Voice Interview", "Voice interview completed & session manifest saved.", 85)

                # --- STAGE 4: EVALUATION & REPORT ENGINE ---
                notify("Stage 4: Evaluation Report", "Synthesizing multimodal audio & technical report...", 86)
                stage4_pipeline = Stage4Pipeline()

                def stage4_cb(current_track: int, total_tracks: int, msg: str):
                    pct = 86 + int((current_track / max(1, total_tracks)) * 12)
                    notify("Stage 4: Audio Track Processing", msg, pct, {
                        "track_current": current_track,
                        "track_total": total_tracks
                    })

                report_payload = stage4_pipeline.run(session_dir=process_dir, output_dir=output_dir, status_callback=stage4_cb)
                results["report"] = report_payload
                notify("Stage 4: Evaluation Report", "Candidate Evaluation Report generated cleanly!", 100, {
                    "report": report_payload.model_dump() if hasattr(report_payload, 'model_dump') else report_payload
                })

                return results
        except Exception as cache_err:
            logger.warning(f"Workflow cache lookup error ({cache_err}). Proceeding with standard execution.")

    # --- STAGE 1: RESEARCH ENGINE ---
    notify("Stage 1: Research", "Initializing Market Intelligence & JD Analysis...", 5)
    stage1_pipeline = Stage1Pipeline()
    stage1_res = stage1_pipeline.run(
        jd_text=jd_text,
        status_callback=lambda msg: notify("Stage 1: Research", msg, 15),
        output_dir=process_dir,
        force_refresh=force_refresh
    )
    rubric = stage1_res.rubric if hasattr(stage1_res, 'rubric') else stage1_res
    results["rubric"] = rubric
    notify("Stage 1: Research", "Evaluation Rubric generated successfully!", 25, {"rubric": rubric.model_dump()})

    # --- STAGE 2: QUESTION ENGINE ---
    notify("Stage 2: Question Engine", "Generating role-specific Question Tree & System Prompt...", 30)
    stage2_pipeline = Stage2Pipeline()
    stage2_output = stage2_pipeline.run(
        session_id=session_id,
        jd_input=stage1_res.model_dump() if hasattr(stage1_res, 'model_dump') else jd_text,
        resume_path=resume_path,
        target_seniority=target_seniority,
        output_dir=process_dir
    )
    if max_questions and max_questions < len(stage2_output.interview_questions):
        stage2_output.interview_questions = stage2_output.interview_questions[:max_questions]
        questions_path = os.path.join(process_dir, "interview_questions.json")
        try:
            with open(questions_path, "w", encoding="utf-8") as f:
                json.dump([q.model_dump() for q in stage2_output.interview_questions], f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to overwrite interview_questions.json with max_questions: {e}")

    results["stage2_output"] = stage2_output
    notify("Stage 2: Question Engine", f"Generated {len(stage2_output.interview_questions)} questions & dynamic system prompt.", 50, {
        "questions": [q.model_dump() for q in stage2_output.interview_questions],
        "system_prompt": stage2_output.interviewer_behavior.interviewer_system_prompt,
        "resume_analysis": stage2_output.resume_analysis.model_dump() if hasattr(stage2_output, 'resume_analysis') and stage2_output.resume_analysis else None
    })

    # Cache full workflow metadata
    try:
        wf_cache = WorkflowCache()
        wf_cache.set(
            jd_text=jd_text,
            resume_path=resume_path,
            target_seniority=target_seniority,
            session_id=session_id,
            stage1_output=stage1_res,
            stage2_output=stage2_output
        )
    except Exception as e:
        logger.warning(f"Failed to record session in WorkflowCache: {e}")

    # --- USER CONFIRMATION PAUSE ---
    if confirm_start_callback is not None:
        notify("Stage 2: Question Engine", "Question tree & Resume analysis ready. Awaiting confirmation to start live interview...", 50)
        should_proceed = confirm_start_callback()
        if not should_proceed:
            logger.info("Interview workflow paused/cancelled by user at Stage 2 QuestionScreen.")
            return results

    # --- STAGE 3: VOICE INTERVIEW LOOP ---
    notify("Stage 3: Voice Interview", "Initializing Voice-to-Voice Loop engine...", 55)
    engine = WorkflowVoiceEngine(session_dir=process_dir, session_id=session_id)
    engine.inject_question_tree(
        questions=[q.model_dump() for q in stage2_output.interview_questions],
        system_prompt=stage2_output.interviewer_behavior.interviewer_system_prompt
    )

    if voice_engine_ref is not None:
        voice_engine_ref.append(engine)

    stage3_max_turns = min(max_questions, len(stage2_output.interview_questions)) if max_questions else len(stage2_output.interview_questions)
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
