"""
Netran AI — Stage 3: Live Voice-to-Voice Loop
Module: voice_engine.py
Description: Stage 3 voice loop adapter that injects Stage 2's dynamic prompt (`interviewer_behavior.json`)
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
    from . import brain
    from .listener import ContinuousMicWriter, listen_and_transcribe
    from .question_manager import QuestionManager
    from .schemas import InterviewQuestionInput
    from .session_logger import SessionLogger
    from .session_state import SessionState
    from .speaker import preload_models as preload_speaker
    from .speaker import speak_text
    from .execution_logger import ExecutionLogger
except ImportError:
    try:
        from model.voice_to_voice_model.model import brain
        from model.voice_to_voice_model.model.listener import (
            ContinuousMicWriter,
            listen_and_transcribe,
        )
        from model.voice_to_voice_model.model.question_manager import QuestionManager
        from model.voice_to_voice_model.model.schemas import InterviewQuestionInput
        from model.voice_to_voice_model.model.session_logger import SessionLogger
        from model.voice_to_voice_model.model.session_state import SessionState
        from model.voice_to_voice_model.model.speaker import (
            preload_models as preload_speaker,
        )
        from model.voice_to_voice_model.model.speaker import speak_text
        from model.voice_to_voice_model.model.execution_logger import ExecutionLogger
    except ImportError:
        import brain
        from listener import ContinuousMicWriter, listen_and_transcribe
        from question_manager import QuestionManager
        from schemas import InterviewQuestionInput
        from session_logger import SessionLogger
        from session_state import SessionState
        from speaker import preload_models as preload_speaker
        from speaker import speak_text
        from execution_logger import ExecutionLogger

logger = logging.getLogger(__name__)


class WorkflowVoiceEngine:
    """
    Adapter and controller for Stage 3 Voice-to-Voice Interview Loop.
    Injects dynamic system prompt and question tree from Stage 2.
    Auto-stops after max_turns or when stop_event is set.
    """
    def __init__(self, session_dir: str, session_id: str):
        self.session_dir = session_dir
        self.session_id = session_id
        self.stop_event = threading.Event()
        
        self.questions_path = os.path.join(session_dir, "interview_questions.json")
        self.behavior_path = os.path.join(session_dir, "interviewer_behavior.json")
        self.wav_path = os.path.join(session_dir, "continuous_mic_input.wav")
        
        self.question_tree: list[dict[str, Any]] = []
        self.system_prompt_text: str = ""
        self.session_state = SessionState()
        self._load_stage2_artifacts()
        
    def _load_stage2_artifacts(self):
        if os.path.exists(self.questions_path):
            with open(self.questions_path, "r", encoding="utf-8") as f:
                self.question_tree = json.load(f)
        else:
            logger.warning(f"Question tree not found at {self.questions_path}")
            
        if os.path.exists(self.behavior_path):
            with open(self.behavior_path, "r", encoding="utf-8") as f:
                behavior_data = json.load(f)
                self.system_prompt_text = behavior_data.get("interviewer_system_prompt", "")
        else:
            logger.warning(f"Interviewer behavior not found at {self.behavior_path}")

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
        max_turns: int = 15,
        ws_audio_queue: Any = None,
        ws_audio_out_queue: Any = None
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
        exec_logger = ExecutionLogger(session_id=self.session_id, session_dir=self.session_dir)
        exec_logger.log_event("BACKEND_ENGINE", "ENGINE_START", {"max_turns": max_turns})
        
        mic_writer = ContinuousMicWriter(filepath=self.wav_path)
        mic_writer.start()
        
        # Initialize dedicated speaker for this session
        try:
            from .speaker import PersistentSpeaker
            self.speaker = PersistentSpeaker(ws_audio_out_queue=ws_audio_out_queue)
        except Exception as e:
            logger.error(f"Failed to init speaker: {e}")
            self.speaker = None

        def speak_text(text: str):
            if self.speaker:
                self.speaker.interrupt_event.clear()
                self.session_state.interrupt_event.clear()
                self.session_state.is_agent_speaking.set()
                self.speaker.speak_clause(text, self.session_state, "af_bella")
                self.speaker.wait_until_done()
                self.session_state.is_agent_speaking.clear()
            else:
                from .speaker import speak_text as fallback_speak
                fallback_speak(text, "af_bella")
        
        conversation_history: list[dict[str, str]] = []
        
        # Initialize QuestionManager
        question_objects = []
        logger.info(f"[DEBUG] self.question_tree type: {type(self.question_tree)}")
        if isinstance(self.question_tree, dict) and "questions" in self.question_tree:
            q_list = self.question_tree["questions"]
        elif isinstance(self.question_tree, dict) and "question_tree" in self.question_tree:
            q_list = self.question_tree["question_tree"]
        else:
            q_list = self.question_tree

        logger.info(f"[DEBUG] q_list length: {len(q_list) if q_list else 0}")
        
        for q in (q_list or []):
            try:
                question_objects.append(InterviewQuestionInput(**q))
            except Exception as e:
                logger.error(f"Failed to map question: {e}")

        
        qm_qs = question_objects[:max_turns] if max_turns > 0 else question_objects
        question_manager = QuestionManager(qm_qs)
        
        try:
            initial_q = question_manager.get_current_question()
            if initial_q:
                import datetime
                hour = datetime.datetime.now().hour
                time_greeting = "Good morning" if hour < 12 else "Good afternoon" if hour < 18 else "Good evening"
                initial_greeting = f"{time_greeting}. I'm Eva, your technical interviewer today. How are you doing?"
                
                logger.info("--- TURN 0: [ICEBREAKER] ---")
                if status_callback:
                    status_callback(0, "SPEAKING_QUESTION", initial_greeting, "")
                    
                speak_text(initial_greeting)
                conversation_history.append({"role": "assistant", "content": initial_greeting})

            _dead_mic_retries = 0
            turn_idx = 0
            
            while not self.stop_event.is_set() and not question_manager.is_finished():
                turn_idx += 1
                curr_q = question_manager.get_current_question()
                topic = curr_q.topic if curr_q else "Interview"
                
                logger.info(f"--- TURN {turn_idx}: [{topic}] ---")
                
                if status_callback:
                    status_callback(turn_idx, "LISTENING_CANDIDATE", "", "")
                    
                def vad_callback(data: dict[str, Any]):
                    if exec_logger:
                        exec_logger.log_event("BACKEND_ENGINE", f"VAD_{data.get('state', 'UNKNOWN')}", data)
                    if status_callback:
                        import json
                        status_callback(turn_idx, f"AUDIO_LEVEL|{json.dumps(data)}", "", "")
                
                if exec_logger:
                    exec_logger.log_event("BACKEND_ENGINE", "STT_START", {"turn_id": turn_idx})
                
                audio_start_perf = session_log.elapsed_sec()
                transcription_result = listen_and_transcribe(
                    state=self.session_state,
                    ws_audio_queue=ws_audio_queue,
                    ui_callback=vad_callback
                )
                
                if isinstance(transcription_result, dict):
                    candidate_transcript = transcription_result.get("text", "").strip()
                    stt_latency = transcription_result.get("latency_ms", 0.0)
                    silence_before = transcription_result.get("silence_duration_before_answer", 0.0)
                else:
                    candidate_transcript = str(transcription_result or "").strip()
                    stt_latency = 0.0
                    silence_before = 0.0
                
                audio_end_perf = session_log.elapsed_sec()
                
                if exec_logger:
                    exec_logger.log_event("BACKEND_ENGINE", "STT_COMPLETE", {
                        "turn_id": turn_idx,
                        "transcript_length": len(candidate_transcript),
                        "stt_latency_ms": stt_latency,
                        "silence_before_sec": silence_before
                    })
                    
                logger.info(f"Candidate Turn {turn_idx} STT: '{candidate_transcript}'")
                
                if not candidate_transcript:
                    _dead_mic_retries += 1
                    if _dead_mic_retries >= 3:
                        logger.warning("Empty transcript 3 times. Stopping.")
                        self.stop_event.set()
                        break
                    continue
                    
                _dead_mic_retries = 0

                if "stop interview" in candidate_transcript.lower() or "end interview" in candidate_transcript.lower():
                    logger.info("Candidate requested to stop the interview.")
                    speak_text("Alright, stopping the interview. Thank you for your time.")
                    self.stop_event.set()
                    break
                
                if status_callback:
                    status_callback(turn_idx, "PROCESSING_RESPONSE", "", candidate_transcript)
                
                branch_taken = question_manager.evaluate_transcript(candidate_transcript)
                llm_prompt, target_question = question_manager.format_prompt_context(
                    branch_taken, candidate_transcript, resume_highlights=None
                )
                
                ack_history = list(conversation_history)
                ack_history.append({"role": "user", "content": candidate_transcript})
                ack_history.append({"role": "user", "content": llm_prompt})
                
                if exec_logger:
                    exec_logger.log_event("BACKEND_ENGINE", "LLM_START", {"turn_id": turn_idx, "prompt_length": len(llm_prompt)})
                
                ttft_start = time.perf_counter()
                try:
                    _, eva_response = brain.generate_eva_response(ack_history)
                except Exception:
                    eva_response = "Got it. Let's move on. " + (target_question or "")
                ttft_ms = (time.perf_counter() - ttft_start) * 1000.0
                
                if exec_logger:
                    exec_logger.log_event("BACKEND_ENGINE", "LLM_COMPLETE", {
                        "turn_id": turn_idx,
                        "response_length": len(eva_response),
                        "ttft_ms": ttft_ms
                    })
                
                conversation_history.append({"role": "user", "content": candidate_transcript})
                conversation_history.append({"role": "assistant", "content": eva_response})
                
                session_log.log_turn(
                    turn_id=turn_idx,
                    topic=topic,
                    question_text=target_question or "N/A",
                    candidate_transcript=candidate_transcript,
                    audio_start_sec=audio_start_perf,
                    audio_end_sec=audio_end_perf,
                    silence_duration_before_answer_sec=silence_before,
                    stt_latency_ms=stt_latency,
                    ttft_ms=ttft_ms
                )
                
                if status_callback:
                    status_callback(turn_idx, f"EVA_RESPONDING_BRANCH|{branch_taken}", target_question, f"{candidate_transcript}\n\n[Eva]: {eva_response}")
                    
                if exec_logger:
                    exec_logger.log_event("BACKEND_ENGINE", "TTS_START", {"turn_id": turn_idx})
                
                if not self.stop_event.is_set():
                    speak_text(eva_response)
                    
                if exec_logger:
                    exec_logger.log_event("BACKEND_ENGINE", "TTS_COMPLETE", {"turn_id": turn_idx})
                    
        except Exception as e:
            logger.error(f"Error during voice interview loop: {e}", exc_info=True)
        finally:
            if self.speaker:
                self.speaker.close()
            mic_writer.stop()
            session_log.finalize()
            if exec_logger:
                exec_logger.log_event("BACKEND_ENGINE", "ENGINE_STOP", {})
            logger.info("Voice interview execution finished.")

    def stop(self):
        """Stops the voice interview loop immediately and unblocks microphone listening."""
        self.stop_event.set()
        if hasattr(self, 'session_state'):
            self.session_state.force_speech_done.set()
