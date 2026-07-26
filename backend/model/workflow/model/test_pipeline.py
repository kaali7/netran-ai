"""
Netran AI — Unified Workflow Orchestrator
Module: test_pipeline.py
Description: Standalone CLI headless test runner for verifying the complete 4-stage pipeline execution
             (Stage 1 Research -> Stage 2 Questions -> Stage 3 Voice -> Stage 4 Reports).
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parents[3]
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from model.workflow.model.orchestrator import run_full_pipeline
from model.workflow.model.sample_data import get_sample_jd_text, SAMPLE_RESUME_PATH

def main():
    print("=" * 65)
    print("Netran AI Workflow Orchestrator — Headless Pipeline Verification")
    print("=" * 65)

    # 1. Locate sample input files from test/input/sample_session/ or fallback paths
    input_dir = backend_dir / "model" / "workflow" / "test" / "input" / "sample_session"
    
    jd_text = ""
    resume_path = str(SAMPLE_RESUME_PATH)

    if input_dir.exists():
        sample_jd_file = input_dir / "sample_jd.txt"
        if sample_jd_file.exists():
            with open(sample_jd_file, "r", encoding="utf-8", errors="ignore") as f:
                jd_text = f.read()

        sample_resume_file = input_dir / "sample_resume.txt"
        if sample_resume_file.exists():
            resume_path = str(sample_resume_file)

    if not jd_text:
        jd_text = get_sample_jd_text()

    # 2. Output directory in model/workflow/test/output/sess_<timestamp>/
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_id = f"sess_{timestamp}"
    test_out_dir = backend_dir / "model" / "workflow" / "test" / "output" / session_id
    test_out_dir.mkdir(parents=True, exist_ok=True)

    print(f"Target Session ID: {session_id}")
    print(f"Target Session Output Directory: {test_out_dir}")
    print(f"Testing Mode: Bounded to 5 Questions Max (Fast Test Scoping)")
    print("=" * 65)

    def status_callback(stage, msg, pct, payload):
        print(f" [{pct:3d}%] [{stage}] {msg}")

    try:
        results = run_full_pipeline(
            jd_text=jd_text,
            resume_path=resume_path,
            session_id=session_id,
            target_seniority="Senior",
            max_questions=5,  # Bound to 5 questions max for fast automated test run
            status_callback=status_callback
        )

        print("\n" + "=" * 65)
        print("Full Workflow Pipeline Verification Successful!")
        print("=" * 65)
        print(f"Session ID: {results.get('session_id')}")
        print(f"Session Directory: {results.get('session_dir')}")

        report = results.get("report")
        if report:
            print(f"\n--- Final Synthesis Summary ---")
            print(f"Hiring Signal:    {report.overall_hiring_signal}")
            print(f"Technical Score:  {report.overall_technical_score}/100")
            print(f"Vocal Score:      {report.overall_vocal_confidence_score}/100")

    except Exception as e:
        print(f"\n[ERROR] Workflow pipeline test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
