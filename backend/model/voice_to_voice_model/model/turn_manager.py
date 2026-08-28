"""
Netran AI — Stage 3: Live Voice-to-Voice Loop
Module: turn_manager.py
Description: Explicit Conversation State Machine and Turn Management subsystem.
             Decouples raw Voice Activity Detection (VAD) from conversation control.
             Synchronizes browser TTS audio playback with listener enablement,
             manages post-playback echo guards, and tracks latency telemetry.
"""

import logging
import os
import threading
import time
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class ConversationState(str, Enum):
    """Explicit conversational state machine for Netran voice sessions."""
    READY = "READY"
    EVA_SPEAKING = "EVA_SPEAKING"          # TTS is actively generating / streaming audio chunks
    PLAYBACK_ACTIVE = "PLAYBACK_ACTIVE"    # Frontend browser is actively playing Eva's audio
    ECHO_GUARD = "ECHO_GUARD"              # Brief silence guard window after playback finishes
    LISTENING = "LISTENING"                # VAD is actively listening for candidate speech
    CANDIDATE_SPEAKING = "CANDIDATE_SPEAKING"  # Candidate speech detected and accumulating
    THINKING = "THINKING"                  # Speech endpointed; STT / LLM inference running
    COMPLETED = "COMPLETED"                # Interview concluded


class TurnManager:
    """
    Manages conversational turn state, playback synchronization events from the client,
    barge-in eligibility, and latency budgeting telemetry across turns.
    """

    def __init__(
        self,
        session_id: str = "",
        is_web_mode: bool = True,
        echo_guard_sec: float | None = None,
        exec_logger: Any = None,
    ):
        self.session_id = session_id
        self.is_web_mode = is_web_mode
        self.exec_logger = exec_logger
        self._lock = threading.RLock()

        # Echo guard duration after frontend signals playback_finished:
        # Default: 150ms for Web (pure sync + minimal acoustic margin), 300ms for Desktop
        if echo_guard_sec is not None:
            self.echo_guard_sec = echo_guard_sec
        else:
            env_val = os.getenv("ECHO_GUARD_MS")
            if env_val:
                try:
                    self.echo_guard_sec = float(env_val) / 1000.0
                except ValueError:
                    self.echo_guard_sec = 0.15 if is_web_mode else 0.30
            else:
                self.echo_guard_sec = 0.15 if is_web_mode else 0.30

        self.state: ConversationState = ConversationState.READY
        self.current_turn_id: int = 0

        # Synchronization primitives
        self.playback_started_event = threading.Event()
        self.playback_finished_event = threading.Event()
        self.listening_enabled_event = threading.Event()
        self.candidate_speaking_event = threading.Event()
        self.speech_endpoint_event = threading.Event()

        # Telemetry & Latency timestamps (monotonic)
        self.turn_timestamps: dict[int, dict[str, float]] = {}

        # Adaptive speech level tracking (RMS samples during candidate speech)
        self.speech_rms_history: list[float] = []

    def set_exec_logger(self, exec_logger: Any):
        """Sets or updates the execution logger."""
        self.exec_logger = exec_logger

    def _log_event(self, event_type: str, details: dict[str, Any] | None = None):
        if self.exec_logger:
            self.exec_logger.log_event("TURN_MANAGER", event_type, details or {})

    def on_tts_start(self, turn_id: int):
        """
        Called when Eva starts generating and streaming TTS audio for a turn.
        Resets playback synchronization events and sets state to EVA_SPEAKING.
        """
        with self._lock:
            self.current_turn_id = turn_id
            self.state = ConversationState.EVA_SPEAKING

            self.playback_started_event.clear()
            self.playback_finished_event.clear()
            self.listening_enabled_event.clear()
            self.candidate_speaking_event.clear()
            self.speech_endpoint_event.clear()

            now = time.monotonic()
            if turn_id not in self.turn_timestamps:
                self.turn_timestamps[turn_id] = {}
            self.turn_timestamps[turn_id]["tts_start"] = now

            self._log_event("TTS_START", {"turn_id": turn_id, "state": self.state.value})
            logger.info(f"[TurnManager] Turn {turn_id}: State -> EVA_SPEAKING (TTS Generation Started)")

    def on_tts_end(self, turn_id: int):
        """
        Called when the backend completes generating and enqueuing all TTS chunks.
        """
        with self._lock:
            now = time.monotonic()
            if turn_id in self.turn_timestamps:
                self.turn_timestamps[turn_id]["tts_end"] = now

            self._log_event("TTS_GENERATION_END", {"turn_id": turn_id})
            logger.info(f"[TurnManager] Turn {turn_id}: TTS Audio Generation Completed")

    def on_playback_started(self, turn_id: int):
        """
        Called when the frontend WebSocket client reports that browser audio playback has started.
        Transitions state to PLAYBACK_ACTIVE.
        """
        with self._lock:
            if self.state in [ConversationState.EVA_SPEAKING, ConversationState.READY]:
                self.state = ConversationState.PLAYBACK_ACTIVE

            self.playback_started_event.set()

            now = time.monotonic()
            if turn_id in self.turn_timestamps:
                self.turn_timestamps[turn_id]["playback_start"] = now

            self._log_event("PLAYBACK_STARTED", {"turn_id": turn_id, "state": self.state.value})
            logger.info(f"[TurnManager] Turn {turn_id}: State -> PLAYBACK_ACTIVE (Client Playing Audio)")

    def on_playback_finished(self, turn_id: int):
        """
        Called when the frontend WebSocket client reports that browser audio playback has completely finished.
        Enters ECHO_GUARD, waits for the configured guard duration, then enables LISTENING.
        """
        with self._lock:
            self.playback_finished_event.set()
            self.state = ConversationState.ECHO_GUARD

            now = time.monotonic()
            if turn_id in self.turn_timestamps:
                self.turn_timestamps[turn_id]["playback_finish"] = now

            self._log_event("PLAYBACK_FINISHED", {
                "turn_id": turn_id,
                "state": self.state.value,
                "echo_guard_sec": self.echo_guard_sec
            })
            logger.info(
                f"[TurnManager] Turn {turn_id}: State -> ECHO_GUARD "
                f"(Playback Finished; guard={self.echo_guard_sec * 1000:.0f}ms)"
            )

        # Transition from ECHO_GUARD -> LISTENING after guard interval
        def _clear_echo_guard():
            if self.echo_guard_sec > 0:
                time.sleep(self.echo_guard_sec)
            with self._lock:
                if self.state == ConversationState.ECHO_GUARD:
                    self.state = ConversationState.LISTENING
                    self.listening_enabled_event.set()
                    now_list = time.monotonic()
                    if turn_id in self.turn_timestamps:
                        self.turn_timestamps[turn_id]["vad_enabled"] = now_list
                    self._log_event("VAD_ENABLED", {"turn_id": turn_id, "state": self.state.value})
                    logger.info(f"[TurnManager] Turn {turn_id}: State -> LISTENING (Microphone & VAD Active)")

        threading.Thread(target=_clear_echo_guard, daemon=True).start()

    def reset_to_listening(self):
        """Forces the conversation state back to LISTENING so the microphone/VAD immediately accepts candidate speech."""
        with self._lock:
            self.state = ConversationState.LISTENING
            self.listening_enabled_event.set()
            self.candidate_speaking_event.clear()
            self.speech_endpoint_event.clear()
            self._log_event("RESET_TO_LISTENING", {"turn_id": self.current_turn_id, "state": self.state.value})
            logger.info(f"[TurnManager] Turn {self.current_turn_id}: State -> LISTENING (Manual / Fallback Reset)")

    def wait_for_listening_ready(self, timeout: float = 20.0) -> bool:
        """
        Blocks until the frontend reports playback finished and the echo guard expires.
        Includes a safety fallback timeout so desktop mode or dropped client packets
        never cause an indefinite hang.
        """
        with self._lock:
            if self.state in [ConversationState.READY, ConversationState.LISTENING]:
                return True

        if not self.is_web_mode:
            # In desktop / sounddevice mode, listening starts as soon as speaker stream finishes
            with self._lock:
                self.state = ConversationState.LISTENING
                self.listening_enabled_event.set()
                return True

        # In Web mode, wait for client playback_finished + echo guard
        logger.info(
            f"[TurnManager] Turn {self.current_turn_id}: Waiting for client playback_finished "
            f"(timeout={timeout}s)..."
        )
        ready = self.listening_enabled_event.wait(timeout=timeout)
        if not ready:
            logger.warning(
                f"[TurnManager] Turn {self.current_turn_id}: Timed out waiting for client playback_finished! "
                f"Forcing transition to LISTENING state."
            )
            with self._lock:
                self.state = ConversationState.LISTENING
                self.listening_enabled_event.set()
                self._log_event("VAD_FORCE_ENABLED_TIMEOUT", {"turn_id": self.current_turn_id})
            return False

        return True

    def on_speech_start(self):
        """
        Called by listener.py when candidate speech start is confirmed.
        Transitions state to CANDIDATE_SPEAKING.
        """
        with self._lock:
            self.state = ConversationState.CANDIDATE_SPEAKING
            self.candidate_speaking_event.set()

            now = time.monotonic()
            if self.current_turn_id in self.turn_timestamps:
                self.turn_timestamps[self.current_turn_id]["speech_start"] = now

            self._log_event("SPEECH_START", {"turn_id": self.current_turn_id, "state": self.state.value})
            logger.info(f"[TurnManager] Turn {self.current_turn_id}: State -> CANDIDATE_SPEAKING")

    def on_speech_end(self):
        """
        Called when candidate speech ends (silence endpoint detected).
        Transitions state to THINKING.
        """
        with self._lock:
            self.state = ConversationState.THINKING
            self.speech_endpoint_event.set()

            now = time.monotonic()
            if self.current_turn_id in self.turn_timestamps:
                self.turn_timestamps[self.current_turn_id]["speech_end"] = now

            self._log_event("SPEECH_END", {"turn_id": self.current_turn_id, "state": self.state.value})
            logger.info(f"[TurnManager] Turn {self.current_turn_id}: State -> THINKING (STT/LLM Processing)")

    def on_barge_in(self):
        """
        Called when candidate interrupts Eva during PLAYBACK_ACTIVE.
        Immediately stops Eva playback and transitions state to CANDIDATE_SPEAKING.
        """
        with self._lock:
            self.state = ConversationState.CANDIDATE_SPEAKING
            self.playback_finished_event.set()
            self.listening_enabled_event.set()
            self.candidate_speaking_event.set()

            now = time.monotonic()
            if self.current_turn_id in self.turn_timestamps:
                self.turn_timestamps[self.current_turn_id]["barge_in"] = now

            self._log_event("BARGE_IN_TRIGGERED", {"turn_id": self.current_turn_id})
            logger.info(f"[TurnManager] Turn {self.current_turn_id}: Barge-In Interrupt! State -> CANDIDATE_SPEAKING")

    def is_candidate_allowed_to_speak(self) -> bool:
        """
        VAD Guard: Determines if candidate speech endpointing and accumulation are permitted.
        Returns True ONLY in LISTENING or CANDIDATE_SPEAKING states.
        """
        with self._lock:
            return self.state in [ConversationState.LISTENING, ConversationState.CANDIDATE_SPEAKING]

    def is_barge_in_allowed(self) -> bool:
        """
        Barge-In Guard: Determines if speech during Eva's turn is treated as a valid barge-in.
        Returns True ONLY when browser audio playback is actively playing.
        """
        with self._lock:
            return self.state == ConversationState.PLAYBACK_ACTIVE

    def record_speech_rms(self, rms_val: float):
        """Records RMS sample of active candidate speech for adaptive threshold calibration."""
        if rms_val > 0.001:
            self.speech_rms_history.append(rms_val)
            if len(self.speech_rms_history) > 200:
                self.speech_rms_history = self.speech_rms_history[-200:]

    def get_estimated_speech_level(self) -> float | None:
        """Computes 25th percentile of observed candidate speech RMS."""
        if len(self.speech_rms_history) < 10:
            return None
        import numpy as np
        return float(np.percentile(self.speech_rms_history, 25))

    def get_latency_telemetry(self, turn_id: int) -> dict[str, float]:
        """Calculates precise millisecond latency breakdown for a given turn."""
        t = self.turn_timestamps.get(turn_id, {})
        metrics: dict[str, float] = {}

        if "tts_start" in t and "tts_end" in t:
            metrics["tts_gen_duration_ms"] = (t["tts_end"] - t["tts_start"]) * 1000.0

        if "tts_end" in t and "playback_start" in t:
            metrics["playback_startup_lag_ms"] = (t["playback_start"] - t["tts_end"]) * 1000.0

        if "playback_start" in t and "playback_finish" in t:
            metrics["eva_playback_duration_ms"] = (t["playback_finish"] - t["playback_start"]) * 1000.0

        if "playback_finish" in t and "vad_enabled" in t:
            metrics["echo_guard_duration_ms"] = (t["vad_enabled"] - t["playback_finish"]) * 1000.0

        if "vad_enabled" in t and "speech_start" in t:
            metrics["candidate_response_lag_ms"] = (t["speech_start"] - t["vad_enabled"]) * 1000.0

        if "speech_start" in t and "speech_end" in t:
            metrics["candidate_speech_duration_ms"] = (t["speech_end"] - t["speech_start"]) * 1000.0

        return metrics
