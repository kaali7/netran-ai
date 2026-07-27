"""
Netran AI — Stage 2: Contextual Question & Behavioral Prompt Engine
Module: test_pipeline.py
Description: Standalone Headless CLI test harness for Stage 2 Question Engine.
             Supports Stage 1 session output ingestion alongside sample test presets.
"""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path

# Adjust Python path for direct execution
current_dir = Path(__file__).resolve().parent
parent_dir = current_dir.parent
root_dir = parent_dir.parent
for d in [str(current_dir), str(parent_dir), str(root_dir)]:
    if d not in sys.path:
        sys.path.insert(0, d)

try:
    from .pipeline import Stage2Pipeline
    from .schemas import Stage2Output
except ImportError:
    try:
        from model.question_model.model.pipeline import Stage2Pipeline
        from model.question_model.model.schemas import Stage2Output
    except ImportError:
        from pipeline import Stage2Pipeline
        from schemas import Stage2Output

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

BASE_DIR = parent_dir  # model/question_model
TEST_INPUT_DIR = BASE_DIR / "test" / "input"
TEST_OUTPUT_DIR = BASE_DIR / "test" / "output"
STAGE1_OUTPUT_DIR = root_dir / "model" / "research_model" / "test" / "output"


def ensure_dirs():
    TEST_INPUT_DIR.mkdir(parents=True, exist_ok=True)
    TEST_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def list_sample_presets():
    ensure_dirs()
    presets = []

    # 1. Subdirectory presets (sample_backend, sample_frontend, sample_fullstack)
    for pdir in sorted(TEST_INPUT_DIR.glob("sample_*")):
        if pdir.is_dir():
            jd_file = pdir / "sample_job_detail.json"
            res_file = pdir / "sample_resume.json"
            if jd_file.exists() and res_file.exists():
                presets.append({
                    "name": f"Preset ({pdir.name}): Job Detail + Resume",
                    "jd_path": jd_file,
                    "resume_path": res_file
                })

    # 2. Stage 1 Output session files if present in research_model/test/output/
    if STAGE1_OUTPUT_DIR.exists():
        stage1_files = sorted(STAGE1_OUTPUT_DIR.glob("sess_*.json"), key=lambda f: f.name, reverse=True)
        for s1_file in stage1_files:
            # Pair with a default preset resume
            default_res = TEST_INPUT_DIR / "sample_backend" / "sample_resume.json"
            if default_res.exists():
                presets.append({
                    "name": f"Stage 1 Session ({s1_file.name}) + Sample Resume",
                    "jd_path": s1_file,
                    "resume_path": default_res
                })

    return presets


def load_preset_bundle(preset: dict) -> dict:
    with open(preset["jd_path"], "r", encoding="utf-8-sig") as f:
        jd_data = json.load(f)
    with open(preset["resume_path"], "r", encoding="utf-8-sig") as f:
        resume_data = json.load(f)

    jd_text_content = json.dumps(jd_data, indent=2) if isinstance(jd_data, dict) else str(jd_data)

    return {
        "company": jd_data.get("company", "Target Company") if isinstance(jd_data, dict) else "Target Company",
        "role": jd_data.get("role", "Target Role") if isinstance(jd_data, dict) else "Target Role",
        "target_seniority": jd_data.get("target_seniority", "Senior") if isinstance(jd_data, dict) else "Senior",
        "jd_text": jd_text_content,
        "resume_text": resume_data.get("resume_text", "") if isinstance(resume_data, dict) else str(resume_data)
    }


if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def run_test():
    print("===================================================================")
    print("      NETRAN AI -- STAGE 2: QUESTION ENGINE TEST HARNESS (CLI)     ")
    print("===================================================================\n")

    presets = list_sample_presets()

    print("Select Input Mode:")
    print("  1. Load Pre-Saved Test Presets (sample_job_detail.json + sample_resume.json)")
    print("  2. Paste Custom JD & Resume Interactively\n")

    choice = input("Enter choice (1-2, default 1): ").strip() or "1"

    input_data = {}
    source_name = ""

    if choice == "1" and presets:
        print("\nAvailable Pre-Saved Test Presets:")
        for idx, p in enumerate(presets, start=1):
            print(f"  {idx}. {p['name']}")

        file_choice = input(f"\nSelect dummy preset (1-{len(presets)}, default 1): ").strip() or "1"
        try:
            selected_preset = presets[int(file_choice) - 1]
            input_data = load_preset_bundle(selected_preset)
            source_name = selected_preset['name']
            print(f"\n[LOADED] Loaded '{selected_preset['name']}'")
        except Exception:
            selected_preset = presets[0]
            input_data = load_preset_bundle(selected_preset)
            source_name = selected_preset['name']
            print(f"\n[LOADED] Defaulted to '{selected_preset['name']}'")

    else:
        print("\nPaste Job Description / Stage 1 Output text below (Press Ctrl+Z then Enter on Windows to finish):")
        jd_lines = []
        try:
            while True:
                line = input()
                jd_lines.append(line)
        except EOFError:
            pass
        jd_text = "\n".join(jd_lines).strip()

        print("\nPaste Candidate Resume text below (Press Ctrl+Z then Enter on Windows to finish):")
        resume_lines = []
        try:
            while True:
                line = input()
                resume_lines.append(line)
        except EOFError:
            pass
        resume_text = "\n".join(resume_lines).strip()

        seniority = input("\nEnter Target Seniority (Junior, Mid, Senior - default Senior): ").strip() or "Senior"

        input_data = {
            "company": "Custom Company",
            "role": "Custom Role",
            "target_seniority": seniority,
            "jd_text": jd_text,
            "resume_text": resume_text
        }
        source_name = "custom_pasted_input"

        if not jd_text or not resume_text:
            print("\n[ERROR] Missing JD or Resume text. Exiting.")
            return

    # Temporary resume file for parser input
    temp_resume_path = TEST_INPUT_DIR / "_temp_resume.txt"
    with open(temp_resume_path, "w", encoding="utf-8") as f:
        f.write(input_data.get("resume_text", ""))

    session_id = f"sess_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    session_output_dir = TEST_OUTPUT_DIR / session_id

    print(f"\n[EXECUTING] Running Stage 2 Question Generation for session: {session_id}...")

    try:
        pipeline = Stage2Pipeline()
        output: Stage2Output = pipeline.run(
            session_id=session_id,
            jd_input=input_data.get("jd_text", ""),
            resume_path=str(temp_resume_path),
            target_seniority=input_data.get("target_seniority", "Senior"),
            output_dir=str(session_output_dir)
        )

        # Clean up temporary resume file
        if temp_resume_path.exists():
            try:
                temp_resume_path.unlink()
            except Exception:
                pass

        print("\n===================================================================")
        print("                 STAGE 2 EXECUTION SUCCESSFUL                     ")
        print("===================================================================")
        print(f"Session ID: {output.session_id}")
        print(f"Matched Resume Skills: {len(output.resume_analysis.matched_skills)}")
        print(f"Identified Skill Gaps: {len(output.resume_analysis.missing_or_gap_skills)}")
        print(f"Generated Question Tree: {len(output.interview_questions)} Tiered Questions")
        print(f"System Prompt Persona: {output.interviewer_behavior.persona}")
        print(f"Output Session Directory: {session_output_dir}")
        print("  ├── resume_analysis.json")
        print("  ├── interview_questions.json")
        print("  ├── interviewer_behavior.json")
        print("  └── system_prompt.txt\n")

        print("--- FIRST QUESTION PREVIEW WITH RUBRICS & FOLLOW-UPS ---")
        if output.interview_questions:
            q1 = output.interview_questions[0]
            print(f"Topic: {q1.topic} [{q1.difficulty}] ({q1.tier})")
            print(f"Q: {q1.question_text}")
            print(f"Keywords: {', '.join(q1.expected_keywords)}")
            print(f"Bar-Raiser Indicator: {q1.rubric.bar_raiser_indicators[0] if q1.rubric.bar_raiser_indicators else 'N/A'}")
            print(f"Follow-up if Strong: {q1.followup_if_strong}")
            print(f"Follow-up if Weak: {q1.followup_if_weak}\n")

    except Exception as e:
        print(f"\n❌ Stage 2 Pipeline Test Failed: {e}")
        logger.exception(e)


if __name__ == "__main__":
    run_test()
