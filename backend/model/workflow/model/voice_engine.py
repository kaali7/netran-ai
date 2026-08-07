"""
Netran AI — Workflow Orchestrator
Module: voice_engine.py
Description: Stage 3 voice loop adapter that injects Stage 2's dynamic prompt (`system_prompt.txt`)
             into Ollama Qwen2.5 persona, iterates through the 15-question tree (`interview_questions.json`),
             and manages continuous mic audio recording.
"""

import json
import logging
import os
import threading
import time
from collections.abc import Callable
from typing import Any

try:
    from .config import OLLAMA_MODEL
except ImportError:
    pass

try:
    from model.voice_to_voice_model.model import brain
    from model.voice_to_voice_model.model.listener import (
        ContinuousMicWriter,
        listen_and_transcribe,
    )
    from model.voice_to_voice_model.model.session_logger import SessionLogger
    from model.voice_to_voice_model.model.speaker import (
        preload_models as preload_speaker,
    )
    from model.voice_to_voice_model.model.speaker import speak_text
except ImportError:
    from voice_to_voice_model.model import brain
    from voice_to_voice_model.model.listener import (
        ContinuousMicWriter,
        listen_and_transcribe,
    )
    from voice_to_voice_model.model.session_logger import SessionLogger
    from voice_to_voice_model.model.speaker import speak_text

logger = logging.getLogger(__name__)

class WorkflowVoiceEngine:
    """
    Adapter and controller for Stage 3 Voice-to-Voice Interview Loop.
    Injects dynamic system prompt and question tree from Stage 2.
    Auto-stops after 15 turns or when stop_event is set.
    """
    def __init__(self, session_dir: str, session_id: str):
        self.session_dir = session_dir
        self.session_id = session_id
        self.stop_event = threading.Event()
        
        self.questions_path = os.path.join(session_dir, "interview_questions.json")
        self.prompt_path = os.path.join(session_dir, "system_prompt.txt")
        self.wav_path = os.path.join(session_dir, "continuous_mic_input.wav")
        
        self.question_tree: list[dict[str, Any]] = []
        self.system_prompt_text: str = ""
        self._load_stage2_artifacts()
        
    def _load_stage2_artifacts(self):
        if os.path.exists(self.questions_path):
            with open(self.questions_path, "r", encoding="utf-8") as f:
                self.question_tree = json.load(f)
        else:
            logger.warning(f"Question tree not found at {self.questions_path}")
            
        if os.path.exists(self.prompt_path):
            with open(self.prompt_path, "r", encoding="utf-8") as f:
                self.system_prompt_text = f.read()
        else:
            logger.warning(f"System prompt not found at {self.prompt_path}")

    def inject_question_tree(self, questions: list[dict[str, Any]], system_prompt: str):
        """
        Injects Stage 2 question tree and system prompt directly in-memory.
        Called by the orchestrator to bypass disk-based loading and ensure
        the voice engine always uses the correct freshly generated questions
        for this session (not cached or leftover disk files).
        """
        self.question_tree = questions
        self.system_prompt_text = system_prompt
        logger.info(f"Injected {len(questions)} questions & system prompt in-memory from Stage 2.")

    def run_interview(
        self,
        status_callback: Callable[[int, str, str, str], None] | None = None,
        max_turns: int = 15
    ):
        """
        Executes the voice-to-voice interview loop turn-by-turn.
        
        status_callback signature:
            callback(turn_id, state_label, current_question, candidate_transcript)
        """
        logger.info(f"Starting Voice Interview for session {self.session_id}")
        
        # 1. Override brain system prompt with Stage 2 dynamic prompt
        if self.system_prompt_text:
            brain.SYSTEM_PROMPT = {
                "role": "system",
                "content": self.system_prompt_text
            }
            logger.info("Injected dynamic system prompt into Ollama brain persona.")
            
        session_log = SessionLogger(session_id=self.session_id, session_dir=self.session_dir)
        mic_writer = ContinuousMicWriter(filepath=self.wav_path)
        mic_writer.start()
        
        conversation_history: list[dict[str, str]] = []
        total_questions = len(self.question_tree) if self.question_tree else max_turns
        total_turns = min(max_turns, total_questions)
        
        try:
            for turn_idx in range(1, total_turns + 1):
                if self.stop_event.is_set():
                    logger.info("Interview stopped by user request.")
                    break
                    
                q_item = self.question_tree[turn_idx - 1] if turn_idx <= len(self.question_tree) else {}
                topic = q_item.get("topic", "Technical Assessment")
                question_text = q_item.get("question_text", f"Question #{turn_idx}")
                
                logger.info(f"--- TURN {turn_idx}/{total_turns}: [{topic}] ---")
                
                # Eva speaks the current question from the tree
                # (UI question box only updates here so it matches what Eva is actually saying)
                if status_callback:
                    status_callback(turn_idx, "SPEAKING_QUESTION", question_text, "")
                    
                if turn_idx == 1:
                    speak_text(f"Welcome! Let's begin your technical interview. First question: {question_text}")
                else:
                    speak_text(question_text)
                    
                if self.stop_event.is_set():
                    break
                    
                # Now listening — UI confirms we're waiting for the candidate's answer
                if status_callback:
                    status_callback(turn_idx, "LISTENING_CANDIDATE", question_text, "")
                    
                audio_start_perf = session_log.elapsed_sec()
                
                transcription_result = listen_and_transcribe()
                if isinstance(transcription_result, dict):
                    candidate_transcript = transcription_result.get("text", "").strip()
                    stt_latency = transcription_result.get("latency_ms", 0.0)
                    silence_before = transcription_result.get("silence_duration_before_answer", 0.0)
                else:
                    candidate_transcript = str(transcription_result or "").strip()
                    stt_latency = 0.0
                    silence_before = 0.0
                
                audio_end_perf = session_log.elapsed_sec()
                logger.info(f"Candidate Turn {turn_idx} STT: '{candidate_transcript}'")
                
                if status_callback:
                    status_callback(turn_idx, "PROCESSING_RESPONSE", question_text, candidate_transcript)
                
                # Build acknowledgment prompt — brain gives a 1-sentence reaction only, NOT another question.
                # The next question will always come from the tree in the next loop iteration.
                ack_history = conversation_history.copy()
                ack_history.append({
                    "role": "user",
                    "content": (
                        f"[Candidate answered Q{turn_idx}: \"{candidate_transcript}\". "
                        f"Give ONE short acknowledgment sentence (max 15 words). Do NOT ask another question yet.]"
                    )
                })
                
                ttft_start = time.perf_counter()
                eva_ack = ""
                
                for token in brain.generate_eva_response(ack_history):
                    eva_ack += token
                    if self.stop_event.is_set():
                        break
                        
                ttft_ms = (time.perf_counter() - ttft_start) * 1000.0
                
                # Store real candidate answer in full history
                conversation_history.append({"role": "user", "content": candidate_transcript})
                conversation_history.append({"role": "assistant", "content": eva_ack})
                
                session_log.log_turn(
                    turn_id=turn_idx,
                    topic=topic,
                    question_text=question_text,
                    candidate_transcript=candidate_transcript,
                    audio_start_sec=audio_start_perf,
                    audio_end_sec=audio_end_perf,
                    silence_duration_before_answer_sec=silence_before,
                    stt_latency_ms=stt_latency,
                    ttft_ms=ttft_ms
                )
                
                # Show transcript update with candidate answer + Eva's short ack
                if status_callback:
                    status_callback(turn_idx, "EVA_RESPONDING", question_text, f"{candidate_transcript}\n\n[Eva]: {eva_ack}")
                    
                # Eva speaks the acknowledgment only (NOT the next question — that comes next loop)
                if eva_ack and not self.stop_event.is_set():
                    speak_text(eva_ack)
                    
            # Final closing message
            if not self.stop_event.is_set():
                speak_text("Thank you for your time today. That concludes our technical interview. Good luck!")
                
        except Exception as e:
            logger.error(f"Error during voice interview loop: {e}", exc_info=True)
        finally:
            mic_writer.stop()
            session_log.finalize()
            logger.info("Voice interview execution finished.")

    def stop(self):
        """Stops the voice interview loop immediately and unblocks microphone listening."""
        self.stop_event.set()
        try:
            from model.voice_to_voice_model.model.listener import trigger_speech_done
            trigger_speech_done()
        except Exception:
            try:
                from listener import trigger_speech_done
                trigger_speech_done()
            except Exception:
                pass
