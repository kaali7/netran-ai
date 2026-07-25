"""
Netran AI — Stage 2: Contextual Question & Behavioral Prompt Engine
Module: test_pipeline.py
Description: Standalone Headless CLI test harness for Stage 2 question tree and prompt generation.
             Supports preset dummy JSON selection, interactive custom input, and single JSON output saving.
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime

# Adjust Python path for direct execution
current_dir = Path(__file__).resolve().parent
parent_dir = current_dir.parent
root_dir = parent_dir.parent
for d in [str(current_dir), str(parent_dir), str(root_dir)]:
    if d not in sys.path:
        sys.path.insert(0, d)

try:
    from .question_generator import generate_stage2_output
    from .schemas import Stage2Output
except ImportError:
    try:
        from model.question_model.model.question_generator import generate_stage2_output
        from model.question_model.model.schemas import Stage2Output
    except ImportError:
        from question_generator import generate_stage2_output
        from schemas import Stage2Output

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

BASE_DIR = parent_dir  # model/question_model
TEST_INPUT_DIR = BASE_DIR / "test" / "input"
TEST_OUTPUT_DIR = BASE_DIR / "test" / "output"

def ensure_dirs():
    TEST_INPUT_DIR.mkdir(parents=True, exist_ok=True)
    TEST_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def list_sample_inputs():
    ensure_dirs()
    files = list(TEST_INPUT_DIR.glob("*.json")) + list(TEST_INPUT_DIR.glob("*.txt"))
    return sorted(files, key=lambda f: f.name)

def read_input_json(fpath: Path) -> dict:
    with open(fpath, "r", encoding="utf-8") as f:
        content = f.read().strip()
    try:
        data = json.loads(content)
        if isinstance(data, dict):
            return data
    except Exception:
        pass
    return {"jd_text": content, "resume_text": "", "target_seniority": "Senior"}

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

def run_test():
    print("===================================================================")
    print("      NETRAN AI -- STAGE 2: QUESTION ENGINE TEST HARNESS (CLI)     ")
    print("===================================================================\n")
    
    sample_files = list_sample_inputs()
    
    print("Select Input Mode:")
    print("  1. Load Pre-Saved Dummy Sample File (JSON)")
    print("  2. Paste Custom JD & Resume Interactively\n")
    
    choice = input("Enter choice (1-2, default 1): ").strip() or "1"
    
    input_data = {}
    source_name = ""
    
    if choice == "1" and sample_files:
        print("\nAvailable Pre-Saved Dummy Input Files:")
        for idx, fpath in enumerate(sample_files, start=1):
            print(f"  {idx}. {fpath.name}")
        
        file_choice = input(f"\nSelect dummy file (1-{len(sample_files)}, default 1): ").strip() or "1"
        try:
            selected_file = sample_files[int(file_choice) - 1]
            input_data = read_input_json(selected_file)
            source_name = selected_file.name
            print(f"\n[LOADED] Loaded '{selected_file.name}'")
        except Exception:
            selected_file = sample_files[0]
            input_data = read_input_json(selected_file)
            source_name = selected_file.name
            print(f"\n[LOADED] Defaulted to '{selected_file.name}'")
            
    else:
        print("\nPaste Job Description text below (Press Ctrl+Z then Enter on Windows to finish):")
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
            
        save_choice = input("\nSave pasted input into test/input/ as JSON for future reuse? (y/N): ").strip().lower()
        if save_choice == "y":
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            saved_filename = f"custom_stage2_{timestamp}.json"
            save_path = TEST_INPUT_DIR / saved_filename
            with open(save_path, "w", encoding="utf-8") as f:
                json.dump(input_data, f, indent=2)
            print(f"[SAVED] Saved pasted input JSON to {save_path}")

    # Temporary resume file for parser input
    temp_resume_path = TEST_INPUT_DIR / "_temp_resume.txt"
    with open(temp_resume_path, "w", encoding="utf-8") as f:
        f.write(input_data.get("resume_text", ""))

    session_id = f"sess_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    session_output_file = TEST_OUTPUT_DIR / f"{session_id}.json"
    
    print(f"\n[EXECUTING] Running Stage 2 Question Generation for session: {session_id}...")
    
    try:
        output: Stage2Output = generate_stage2_output(
            session_id=session_id,
            jd_text=input_data.get("jd_text", ""),
            resume_path=str(temp_resume_path),
            target_seniority=input_data.get("target_seniority", "Senior"),
            output_dir=str(session_output_file)
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
        print(f"Generated Question Tree: {len(output.question_tree)} Tiered Questions")
        print(f"System Prompt Length: {len(output.interviewer_system_prompt)} characters")
        print(f"Saved Output JSON: {session_output_file}\n")
        
        print("--- FIRST QUESTION PREVIEW ---")
        if output.question_tree:
            q1 = output.question_tree[0]
            print(f"Topic: {q1.topic} [{q1.difficulty}]")
            print(f"Q: {q1.question_text}")
            print(f"Keywords: {', '.join(q1.expected_keywords)}\n")
            
    except Exception as e:
        print(f"\n❌ Stage 2 Pipeline Test Failed: {e}")
        logger.exception(e)


if __name__ == "__main__":
    run_test()
