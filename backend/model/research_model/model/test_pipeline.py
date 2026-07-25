"""
Netran AI — Stage 1: JD Research & Market Intelligence Engine
Module: test_pipeline.py
Description: Standalone Headless CLI test harness for verifying Stage 1 JD research,
             market intelligence retrieval, and rubric synthesis.
"""

import os
import sys
import logging
from datetime import datetime
from pathlib import Path

# Add backend root to sys.path for clean import resolution
ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

try:
    from model.research_model.model.pipeline import run_pipeline
    from model.research_model.model.schemas import Stage1Output
except ImportError:
    from pipeline import run_pipeline
    from schemas import Stage1Output

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
TEST_INPUT_DIR = BASE_DIR / "test" / "input"
TEST_OUTPUT_DIR = BASE_DIR / "test" / "output"

def ensure_dirs():
    TEST_INPUT_DIR.mkdir(parents=True, exist_ok=True)
    TEST_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def list_sample_inputs():
    ensure_dirs()
    files = list(TEST_INPUT_DIR.glob("*.json")) + list(TEST_INPUT_DIR.glob("*.txt"))
    return sorted(files, key=lambda f: f.name)

def read_input_file(fpath: Path) -> str:
    with open(fpath, "r", encoding="utf-8") as f:
        content = f.read().strip()
    if fpath.suffix.lower() == ".json":
        try:
            data = json.loads(content)
            if isinstance(data, dict):
                return data.get("jd_text", content)
        except Exception:
            pass
    return content

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

def run_test():
    print("===================================================================")
    print("      NETRAN AI -- STAGE 1: RESEARCH MODEL TEST HARNESS (CLI)      ")
    print("===================================================================\n")
    
    sample_files = list_sample_inputs()
    
    print("Select Input Mode:")
    print("  1. Load Pre-Saved Dummy Sample File (JSON)")
    print("  2. Paste Custom Job Description Text Interactively\n")
    
    choice = input("Enter choice (1-2, default 1): ").strip() or "1"
    
    jd_text = ""
    source_name = ""
    
    if choice == "1" and sample_files:
        print("\nAvailable Pre-Saved Dummy Input Files:")
        for idx, fpath in enumerate(sample_files, start=1):
            print(f"  {idx}. {fpath.name}")
        
        file_choice = input(f"\nSelect dummy file (1-{len(sample_files)}, default 1): ").strip() or "1"
        try:
            selected_file = sample_files[int(file_choice) - 1]
            jd_text = read_input_file(selected_file)
            source_name = selected_file.name
            print(f"\n[LOADED] Loaded '{selected_file.name}' ({len(jd_text)} chars)")
        except Exception:
            selected_file = sample_files[0]
            jd_text = read_input_file(selected_file)
            source_name = selected_file.name
            print(f"\n[LOADED] Defaulted to '{selected_file.name}' ({len(jd_text)} chars)")
            
    else:
        print("\nPaste Job Description text below (Press Ctrl+Z then Enter on Windows to finish):")
        lines = []
        try:
            while True:
                line = input()
                lines.append(line)
        except EOFError:
            pass
        jd_text = "\n".join(lines).strip()
        source_name = "custom_pasted_jd"
        
        if not jd_text:
            print("\n[ERROR] No text provided. Exiting.")
            return
            
        save_choice = input("\nSave pasted input into test/input/ as JSON for future reuse? (y/N): ").strip().lower()
        if save_choice == "y":
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            saved_filename = f"custom_jd_{timestamp}.json"
            save_path = TEST_INPUT_DIR / saved_filename
            payload = {
                "company": "Target Company",
                "role": "Custom Role",
                "target_seniority": "Senior",
                "jd_text": jd_text
            }
            with open(save_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)
            print(f"[SAVED] Saved pasted input JSON to {save_path}")

    session_id = f"sess_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    session_output_file = TEST_OUTPUT_DIR / f"{session_id}.json"
    
    print(f"\n[EXECUTING] Running Stage 1 Research Pipeline for session: {session_id}...")
    
    try:
        output: Stage1Output = run_pipeline(
            jd_text=jd_text,
            status_callback=lambda msg: print(f"  -> {msg}"),
            output_dir=str(session_output_file)
        )
        
        print("\n===================================================================")
        print("                 STAGE 1 PIPELINE EXECUTION SUCCESS                ")
        print("===================================================================")
        print(f"  • Session ID:       {session_id}")
        print(f"  • Target Role:      {output.parsed_jd.role}")
        print(f"  • Company:          {output.parsed_jd.company}")
        print(f"  • Tech Stack:       {', '.join(output.parsed_jd.tech_stack)}")
        print(f"  • Search Queries:   {output.parsed_jd.search_queries}")
        print(f"  • Web Sources:      {len(output.search_context)} retrieved snippets")
        print(f"  • Rubric Pillars:   {len(output.rubric.keyTechnicalPillars)} core pillars")
        print(f"  • Topics Generated: {len(output.rubric.expectedInterviewTopics)} categories")
        print(f"  • Output Directory: {session_output_dir}")
        print("-------------------------------------------------------------------")
        
        if output.search_context:
            print("\n🌐 RETRIEVED WEB INTELLIGENCE SOURCES:")
            for idx, item in enumerate(output.search_context[:3], start=1):
                print(f"  [{idx}] {item.get('title', 'N/A')}")
                print(f"      URL:     {item.get('url', 'N/A')}")
                snippet = item.get('content', '')[:120].replace('\n', ' ')
                print(f"      Snippet: {snippet}...\n")

        print("🎯 SYNTHESIZED ASSESSMENT RUBRIC OVERVIEW:")
        print(f"  Overview: {output.rubric.roleOverview[:200]}...\n")
        
        print(f"✅ All artifacts saved to: {session_output_dir}")
        
    except Exception as e:
        logger.error(f"❌ Stage 1 Pipeline Test Failed: {e}", exc_info=True)

if __name__ == "__main__":
    run_test()
