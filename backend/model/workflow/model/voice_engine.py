import os
import json
import time
import logging
import threading
from typing import Callable, Optional, List, Dict, Any

from config import OLLAMA_MODEL

# Imports from voice_to_voice_model (injected via sys.path)
import brain
from listener import listen_and_transcribe, ContinuousMicWriter
from speaker import speak_text, preload_models as preload_speaker
from session_logger import SessionLogger

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
        
        self.question_tree: List[Dict[str, Any]] = []
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

    def run_interview(
        self,
        status_callback: Optional[Callable[[int, str, str, str], None]] = None,
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
        
        conversation_history: List[Dict[str, str]] = []
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
                
                if status_callback:
                    status_callback(turn_idx, "SPEAKING_QUESTION", question_text, "")
                    
                # Eva asks question
                if turn_idx == 1:
                    initial_greeting = f"Welcome! Let's get started with your technical interview. First question: {question_text}"
                    speak_text(initial_greeting)
                else:
                    speak_text(question_text)
                    
                if self.stop_event.is_set():
                    break
                    
                # Candidate response listening
                if status_callback:
                    status_callback(turn_idx, "LISTENING_CANDIDATE", question_text, "")
                    
                audio_start_perf = session_log.elapsed_sec()
                
                transcription_result = listen_and_transcribe()
                candidate_transcript = transcription_result.get("text", "").strip()
                stt_latency = transcription_result.get("latency_ms", 0.0)
                silence_before = transcription_result.get("silence_duration_before_answer", 0.0)
                
                audio_end_perf = session_log.elapsed_sec()
                
                logger.info(f"Candidate Turn {turn_idx} STT: '{candidate_transcript}'")
                
                if status_callback:
                    status_callback(turn_idx, "PROCESSING_RESPONSE", question_text, candidate_transcript)
                    
                conversation_history.append({"role": "user", "content": candidate_transcript})
                
                # Brain reasoning
                ttft_start = time.perf_counter()
                eva_response = ""
                
                for token in brain.generate_eva_response(conversation_history):
                    eva_response += token
                    if self.stop_event.is_set():
                        break
                        
                ttft_ms = (time.perf_counter() - ttft_start) * 1000.0
                
                conversation_history.append({"role": "assistant", "content": eva_response})
                
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
                
                if status_callback:
                    status_callback(turn_idx, "EVA_RESPONDING", question_text, candidate_transcript)
                    
                if eva_response and not self.stop_event.is_set():
                    speak_text(eva_response)
                    
            # Final closing
            if not self.stop_event.is_set():
                speak_text("Thank you for your time today. That concludes our technical interview. Good luck!")
                
        except Exception as e:
            logger.error(f"Error during voice interview loop: {e}", exc_info=True)
        finally:
            mic_writer.stop()
            session_log.finalize()
            logger.info("Voice interview execution finished.")

    def stop(self):
        self.stop_event.set()
