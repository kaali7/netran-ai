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
    print("============================================================")
    print("Netran AI Stage 4 — Headless Pipeline Verification")
    print("============================================================")

    # 1. Locate available session directories
    base_input_dir = backend_dir / "model" / "reports_model" / "test" / "input"
    v2v_out_dir = backend_dir / "model" / "voice_to_voice_model" / "test" / "output"
    
    available_sessions = []
    
    if base_input_dir.exists():
        samples = [d for d in base_input_dir.iterdir() if d.is_dir()]
        samples.sort(key=lambda x: x.name)
        available_sessions.extend(samples)
        
    if v2v_out_dir.exists():
        v2v_sessions = [d for d in v2v_out_dir.iterdir() if d.is_dir()]
        v2v_sessions.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        available_sessions.extend(v2v_sessions)
        
    if not available_sessions:
        print("Error: No session input directories found to process.")
        sys.exit(1)
        
    print("Available Test Sessions:")
    for idx, sess in enumerate(available_sessions):
        source = "test/input" if sess.parent.name == "input" else "stage3/output"
        print(f" {idx + 1}. {sess.name}  [{source}]")
        
    choice = input(f"Select a session to evaluate (1-{len(available_sessions)}, default 1): ").strip()
    if not choice:
        choice = "1"
        
    try:
        selected_idx = int(choice) - 1
        if selected_idx < 0 or selected_idx >= len(available_sessions):
            raise ValueError
    except ValueError:
        print("Invalid choice, defaulting to 1.")
        selected_idx = 0
        
    session_dir = available_sessions[selected_idx]
    
    print("\n" + "=" * 60)
    print(f"Target Session Directory: {session_dir}")
    print("=" * 60)

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
            if getattr(turn1, "resume_verification_note", None):
                print(f"Resume Verification: {turn1.resume_verification_note}")


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
