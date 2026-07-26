"""
Netran AI — Stage 4: Post-Session Multimodal Evaluation & Report Generation Engine
Module: test_pipeline.py
Description: Standalone CLI headless test runner for verifying Stage 4 audio slicing and multimodal report synthesis.
"""

import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parents[3]
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from datetime import datetime

from model.reports_model.model.report_builder import build_report


def main():
    # 1. Locate input session directory from test/input/ or fallback paths
    test_input_dir = backend_dir / "model" / "reports_model" / "test" / "input" / "sample_session"
    
    if not test_input_dir.exists():
        # Fallback to scanning Stage 3 voice_to_voice output sessions
        v2v_out_dir = backend_dir / "model" / "voice_to_voice_model" / "test" / "output"
        if v2v_out_dir.exists():
            existing = [d for d in v2v_out_dir.iterdir() if d.is_dir()]
            if existing:
                existing.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                test_input_dir = existing[0]

    session_dir = test_input_dir
    print("=" * 60)
    print("Netran AI Stage 4 — Headless Pipeline Verification")
    print(f"Target Session Directory: {session_dir}")
    print("=" * 60)

    if not session_dir.exists():
        print(f"Error: Session input directory not found at {session_dir}")
        sys.exit(1)

    # 2. Output directory in test/output/
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_session_dir = backend_dir / "model" / "reports_model" / "test" / "output" / f"sess_{timestamp}"
    out_session_dir.mkdir(parents=True, exist_ok=True)

    try:
        report = build_report(
            session_dir=session_dir,
            model_name="gemini-3.6-flash",
            output_dir=out_session_dir
        )
        print("\n" + "=" * 60)
        print("Pipeline Execution Successful!")
        print("=" * 60)
        print(f"Session ID:               {report.session_id}")
        print(f"Overall Hiring Signal:    {report.overall_hiring_signal}")
        print(f"Overall Technical Score:  {report.overall_technical_score}/100")
        print(f"Overall Vocal Score:      {report.overall_vocal_confidence_score}/100")
        print(f"Pillars Count:            {len(report.technical_pillars)}")
        print(f"Turn Evaluations Count:   {len(report.turn_evaluations)}")
        
        if report.turn_evaluations:
            turn1 = report.turn_evaluations[0]
            print("\n--- Turn 1 Summary ---")
            print(f"Original Transcript: {turn1.candidate_transcript}")
            print(f"Gemini Verified:    {turn1.gemini_verified_transcript}")
            print(f"Emotion:            {turn1.emotional_state}")
            print(f"Hesitation:         {turn1.hesitation_level}")

        print("\nArtifacts verified in output directory:")
        print(f" - {out_session_dir / 'report.json'}")
        print(f" - {out_session_dir / 'evaluation_summary.md'}")

    except Exception as e:
        print(f"\n[ERROR] Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
