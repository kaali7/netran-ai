"""
Netran AI — Stage 3: Live Voice-to-Voice Loop
Module: test_pipeline.py
Description: Standalone Headless CLI test harness for Stage 3 Voice-to-Voice Engine.
             Loads Stage 2 artifacts via schemas.load_stage2_bundle and executes
             the QuestionManager state machine and session manifest logger.
"""

import logging
import struct
import sys
import wave
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
    from .question_manager import QuestionManager
    from .schemas import InterviewQuestionInput, InterviewerBehaviorInput, Stage2SessionBundle, load_stage2_bundle
    from .session_logger import SessionLogger
except ImportError:
    try:
        from model.voice_to_voice_model.model.question_manager import QuestionManager
        from model.voice_to_voice_model.model.schemas import (
            InterviewQuestionInput,
            InterviewerBehaviorInput,
            Stage2SessionBundle,
            load_stage2_bundle,
        )
        from model.voice_to_voice_model.model.session_logger import SessionLogger
    except ImportError:
        from question_manager import QuestionManager
        from schemas import InterviewQuestionInput, InterviewerBehaviorInput, Stage2SessionBundle, load_stage2_bundle
        from session_logger import SessionLogger

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

BASE_DIR = parent_dir  # model/voice_to_voice_model
TEST_INPUT_DIR = BASE_DIR / "test" / "input"
TEST_OUTPUT_DIR = BASE_DIR / "test" / "output"


def ensure_dirs():
    TEST_INPUT_DIR.mkdir(parents=True, exist_ok=True)
    TEST_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def list_sample_presets():
    ensure_dirs()
    presets = []

    # Subdirectory presets (sample_backend, sample_frontend, sample_fullstack)
    for pdir in sorted(TEST_INPUT_DIR.glob("sample_*")):
        if pdir.is_dir():
            q_file = pdir / "interview_questions.json"
            b_file = pdir / "interviewer_behavior.json"
            if q_file.exists() and b_file.exists():
                presets.append({
                    "name": f"Preset ({pdir.name})",
                    "path": pdir
                })

    # Root input directory preset
    root_q = TEST_INPUT_DIR / "interview_questions.json"
    root_b = TEST_INPUT_DIR / "interviewer_behavior.json"
    if root_q.exists() and root_b.exists():
        presets.append({
            "name": "Preset (root)",
            "path": TEST_INPUT_DIR
        })

    return presets


def generate_dummy_wav(filepath: Path, duration_sec: float = 3.0, sample_rate: int = 16000):
    """Generates a dummy silent WAV audio recording file for headless test pipeline runs."""
    num_samples = int(duration_sec * sample_rate)
    with wave.open(str(filepath), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit PCM
        wf.setframerate(sample_rate)
        data = struct.pack("<" + "h" * num_samples, *([0] * num_samples))
        wf.writeframes(data)


if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def run_test():
    print("===================================================================")
    print("      NETRAN AI -- STAGE 3: VOICE-TO-VOICE LOOP TEST HARNESS       ")
    print("===================================================================\n")

    presets = list_sample_presets()

    print("Select Input Mode:")
    print("  1. Load Stage 2 Artifact Bundle (sample_backend / sample_frontend / sample_fullstack)")
    print("  2. Run Headless Voice Simulation Test\n")

    try:
        choice = input("Enter choice (1-2, default 1): ").strip() or "1"
    except (EOFError, Exception):
        choice = "1"

    if choice == "1" and presets:
        print("\nAvailable Stage 3 Input Presets:")
        for idx, p in enumerate(presets, start=1):
            print(f"  {idx}. {p['name']}")

        try:
            preset_choice = input(f"\nSelect preset (1-{len(presets)}, default 1): ").strip() or "1"
        except (EOFError, Exception):
            preset_choice = "1"

        try:
            selected_preset = presets[int(preset_choice) - 1]
        except Exception:
            selected_preset = presets[0]

        bundle = load_stage2_bundle(selected_preset["path"])
        print(f"\n[LOADED BUNDLE] Ingested Stage 2 bundle from '{selected_preset['name']}'")
        print(f"  ├── Persona: {bundle.behavior.persona}")
        print(f"  ├── Questions: {len(bundle.questions)} items")
        print(f"  └── System Prompt: {bundle.system_prompt[:80]}...")

    else:
        # Fallback baseline bundle
        behavior = InterviewerBehaviorInput(
            session_id="simulated_session",
            persona="Eva",
            interviewer_system_prompt="You are Eva, lead technical interviewer."
        )
        questions = [
            InterviewQuestionInput(
                id=1,
                topic="Asynchronous Python",
                question_text="Explain Python asyncio event loop.",
                expected_keywords=["event loop", "asyncio", "run_in_executor"],
                followup_if_strong="How does run_in_executor work under the hood?",
                followup_if_weak="What is the difference between time.sleep and asyncio.sleep?"
            ),
            InterviewQuestionInput(
                id=2,
                topic="PostgreSQL Indexing",
                question_text="How do B-Tree indexes work in PostgreSQL?",
                expected_keywords=["B-Tree", "index", "lookup"],
                followup_if_strong="How do write operations affect B-Tree index page splits?",
                followup_if_weak="When should you avoid adding an index to a column?"
            )
        ]
        bundle = Stage2SessionBundle(
            behavior=behavior,
            questions=questions,
            system_prompt=behavior.interviewer_system_prompt
        )
        print("\n[LOADED BUNDLE] Ingested baseline simulated voice session bundle.")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_id = f"sess_{timestamp}"
    session_output_dir = TEST_OUTPUT_DIR / session_id
    session_output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n[EXECUTING] Running Stage 3 Voice Loop for session: {session_id}...")

    logger_inst = SessionLogger(session_id=session_id, session_dir=str(session_output_dir))
    qm = QuestionManager(questions=bundle.questions)

    # Simulated candidate transcripts for testing adaptive branching
    sample_answers = [
        "In Python asyncio, the single-threaded event loop manages non-blocking tasks. We use run_in_executor for blocking I/O calls.",
        "PostgreSQL B-Tree index stores key pointers in balanced trees.",
        "gRPC utilizes HTTP/2 and Protobuf binary frames for low latency service to service communication."
    ]

    MAX_TESTING_QUESTIONS = 5  # Bounded to 5 questions max for testing
    current_sec = 0.0
    turn_counter = 1

    while not qm.is_finished() and turn_counter <= MAX_TESTING_QUESTIONS:
        q = qm.get_current_question()
        if not q:
            break

        answer_text = sample_answers[turn_counter - 1] if turn_counter <= len(sample_answers) else "I would implement a distributed caching strategy."

        # Evaluate candidate transcript using QuestionManager state machine
        branch_taken = qm.evaluate_transcript(answer_text)
        llm_prompt, target_question = qm.format_prompt_context(branch_taken, answer_text)

        start_sec = current_sec + 1.5
        end_sec = start_sec + 4.2

        logger_inst.log_turn(
            turn_id=turn_counter,
            question_id=q.id,
            topic=q.topic,
            question_text=q.question_text,
            candidate_transcript=answer_text,
            audio_start_sec=start_sec,
            audio_end_sec=end_sec,
            silence_duration_before_answer_sec=0.45,
            stt_latency_ms=180.5,
            ttft_ms=320.0,
            evaluation_branch_taken=branch_taken,
            eva_reasoning="Mocked reasoning based on candidate answer.",
            eva_reply=target_question
        )

        current_sec = end_sec + 1.0
        turn_counter += 1
        qm.advance_question()

    # Generate continuous mic audio recording file (recording.wav)
    wav_path = session_output_dir / "recording.wav"
    generate_dummy_wav(wav_path, duration_sec=current_sec + 1.0)

    # Finalize session_manifest.json artifact
    logger_inst.finalize()

    print("\n===================================================================")
    print("                 STAGE 3 EXECUTION SUCCESSFUL                     ")
    print("===================================================================")
    print(f"Session ID: {session_id}")
    print(f"Persona: {bundle.behavior.persona}")
    print(f"Recorded Turns: {len(logger_inst.turns)} Dialogue Turns")
    print(f"Output Session Directory: {session_output_dir}")
    print("  ├── recording.wav (Continuous Gain-Boosted Audio)")
    print("  └── session_manifest.json (Unified Manifest Telemetry)\n")

    print("--- TURN 1 PREVIEW & BRANCHING LOG ---")
    if logger_inst.turns:
        t1 = logger_inst.turns[0].model_dump()
        print(f"Turn {t1['turn_id']} [{t1['topic']}]")
        print(f"Q: {t1['question_text']}")
        print(f"Candidate: \"{t1['candidate_transcript']}\"")
        print(f"Branch Taken: {t1['evaluation_branch_taken']}")
        print(f"Timestamps: {t1['audio_start_sec']}s -> {t1['audio_end_sec']}s\n")


if __name__ == "__main__":
    run_test()
