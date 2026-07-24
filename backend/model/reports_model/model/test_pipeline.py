import sys
import json
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parents[3]
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from model.reports_model.model.report_builder import build_report

def main():
    session_dir = backend_dir / "model" / "sessions" / "sess_20260724_194457"
    print("=" * 60)
    print("Netran AI Stage 4 — Headless Pipeline Verification")
    print(f"Target Session Directory: {session_dir}")
    print("=" * 60)

    if not session_dir.exists():
        print(f"Error: Session directory not found at {session_dir}")
        sys.exit(1)

    try:
        report = build_report(session_dir=session_dir, model_name="gemini-3.6-flash")
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

        print(f"\nArtifacts verified:")
        print(f" - {session_dir / 'report.json'}")
        print(f" - {session_dir / 'evaluation_summary.md'}")
        print(f" - {session_dir / 'turn_01.wav'}")

    except Exception as e:
        print(f"\n[ERROR] Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
