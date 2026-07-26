"""
Netran AI — Stage 3: Live Voice-to-Voice Loop
Module: test_pipeline.py
Description: Standalone Headless CLI test harness for Stage 3 Voice-to-Voice Engine.
             Loads test input presets (interview_questions.json + interviewer_behavior.json)
             and generates session outputs (recording.wav + transcript.json / session_manifest.json).
"""

import json
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
    from .session_logger import SessionLogger
except ImportError:
    try:
        from model.voice_to_voice_model.model.session_logger import SessionLogger
    except ImportError:
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
    
    # 1. Subdirectory presets (sample_backend, sample_frontend, sample_fullstack)
    for pdir in sorted(TEST_INPUT_DIR.glob("sample_*")):
        if pdir.is_dir():
            q_file = pdir / "interview_questions.json"
            b_file = pdir / "interviewer_behavior.json"
            if q_file.exists() and b_file.exists():
                presets.append({
                    "name": f"Preset ({pdir.name}): Questions + Behavior",
                    "questions_path": q_file,
                    "behavior_path": b_file
                })

    # 2. Root input directory preset
    root_q = TEST_INPUT_DIR / "interview_questions.json"
    root_b = TEST_INPUT_DIR / "interviewer_behavior.json"
    if root_q.exists() and root_b.exists():
        presets.append({
            "name": "Preset (root): interview_questions.json + interviewer_behavior.json",
            "questions_path": root_q,
            "behavior_path": root_b
        })
        
    return presets

def load_preset(preset: dict) -> tuple[list, dict]:
    with open(preset["questions_path"], "r", encoding="utf-8") as f:
        questions = json.load(f)
    with open(preset["behavior_path"], "r", encoding="utf-8") as f:
        behavior = json.load(f)
    return questions, behavior

def generate_dummy_wav(filepath: Path, duration_sec: float = 3.0, sample_rate: int = 16000):
    """Generates a dummy silent WAV audio recording file for headless test pipeline runs."""
    num_samples = int(duration_sec * sample_rate)
    with wave.open(str(filepath), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit PCM
        wf.setframerate(sample_rate)
        # Write silence frames (0s)
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
    print("  1. Load Pre-Saved Stage 2 Output Presets (interview_questions.json + interviewer_behavior.json)")
    print("  2. Run Headless Voice Simulation Test\n")
    
    choice = input("Enter choice (1-2, default 1): ").strip() or "1"
    
    selected_preset = None
    if choice == "1" and presets:
        print("\nAvailable Stage 3 Input Presets:")
        for idx, p in enumerate(presets, start=1):
            print(f"  {idx}. {p['name']}")
        
        preset_choice = input(f"\nSelect preset (1-{len(presets)}, default 1): ").strip() or "1"
        try:
            selected_preset = presets[int(preset_choice) - 1]
        except Exception:
            selected_preset = presets[0]
            
        questions, behavior = load_preset(selected_preset)
        print(f"\n[LOADED] Loaded '{selected_preset['name']}'")
        print(f"  ├── System Prompt: {behavior.get('interviewer_system_prompt', '')[:80]}...")
        print(f"  └── Questions Loaded: {len(questions)} items")
    else:
        questions = [
            {"id": 1, "topic": "Asynchronous Concurrency", "question_text": "Explain Python asyncio event loop.", "expected_keywords": ["event loop", "async"]},
            {"id": 2, "topic": "PostgreSQL Indexing", "question_text": "How do B-Tree indexes work?", "expected_keywords": ["B-Tree", "index"]}
        ]
        behavior = {
            "session_id": "simulated_session",
            "persona": "Eva",
            "interviewer_system_prompt": "You are Eva, a lead technical interviewer."
        }
        print("\n[LOADED] Loaded baseline simulated voice session configuration.")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_id = f"sess_{timestamp}"
    session_output_dir = TEST_OUTPUT_DIR / session_id
    session_output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n[EXECUTING] Running Stage 3 Voice Loop for session: {session_id}...")
    
    logger_inst = SessionLogger(session_id=session_id, session_dir=str(session_output_dir))
    
    # Simulate candidate voice turns
    sample_answers = [
        "In Python asyncio, the event loop manages asynchronous tasks cooperative multitasking single thread.",
        "PostgreSQL B-Tree indexes store key pointers in a balanced tree structure for fast logarithmic lookups.",
        "gRPC utilizes HTTP/2 and binary Protocol Buffers which offers much higher performance than REST over HTTP/1.1."
    ]
    
    MAX_TESTING_QUESTIONS = 5  # Bounded to 5 questions max during testing time
    test_questions = questions[:MAX_TESTING_QUESTIONS]
    
    current_sec = 0.0
    for idx, q in enumerate(test_questions, start=1):
        answer_text = sample_answers[idx - 1] if idx <= len(sample_answers) else "I would implement a distributed caching pattern."
        start_sec = current_sec + 1.5
        end_sec = start_sec + 4.2
        
        logger_inst.log_turn(
            turn_id=q.get("id", idx),
            topic=q.get("topic", "General Technical"),
            question_text=q.get("question_text", ""),
            candidate_transcript=answer_text,
            audio_start_sec=start_sec,
            audio_end_sec=end_sec,
            silence_duration_before_answer_sec=0.45,
            stt_latency_ms=180.5,
            ttft_ms=320.0
        )
        current_sec = end_sec + 1.0

    # Write continuous mic audio recording file (recording.wav)
    wav_path = session_output_dir / "recording.wav"
    generate_dummy_wav(wav_path, duration_sec=current_sec + 1.0)
    
    # Finalize transcript.json and session_manifest.json
    logger_inst.finalize()
    
    print("\n===================================================================")
    print("                 STAGE 3 EXECUTION SUCCESSFUL                     ")
    print("===================================================================")
    print(f"Session ID: {session_id}")
    print(f"Persona: {behavior.get('persona', 'Eva')}")
    print(f"Recorded Turns: {len(logger_inst.turns)} Dialogue Turns")
    print(f"Output Session Directory: {session_output_dir}")
    print("  ├── recording.wav (Continuous Audio Recording)")
    print("  ├── transcript.json (Turn Dialogue & Telemetry)")
    print("  └── session_manifest.json (Timing Telemetry)\n")
    
    print("--- FIRST TURN TRANSCRIPT PREVIEW ---")
    if logger_inst.turns:
        t1 = logger_inst.turns[0]
        print(f"Turn {t1['turn_id']} [{t1['topic']}]")
        print(f"Q: {t1['question_text']}")
        print(f"Candidate: \"{t1['candidate_transcript']}\"")
        print(f"Timestamps: {t1['audio_start_sec']}s -> {t1['audio_end_sec']}s (STT Latency: {t1['stt_latency_ms']}ms)\n")


if __name__ == "__main__":
    run_test()
