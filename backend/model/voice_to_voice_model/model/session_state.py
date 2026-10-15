"""
Netran AI — Stage 3: Live Voice-to-Voice Loop
Module: session_state.py
Description: Thread-safe synchronization object shared across listener, speaker, and front.
             Replaces broken importlib-based echo gate with threading.Event primitives.
             Includes interrupt_event for full-duplex barge-in interruption architecture.
"""

import threading
from dataclasses import dataclass, field


@dataclass
class SessionState:
    """Thread-safe synchronization object shared across listener, speaker, and front."""
    is_agent_speaking: threading.Event = field(default_factory=threading.Event)
    is_candidate_speaking: threading.Event = field(default_factory=threading.Event)
    should_stop: threading.Event = field(default_factory=threading.Event)
    force_speech_done: threading.Event = field(default_factory=threading.Event)

    # Full-duplex barge-in interrupt signal.
    # Set by listener.py when speech_prob > 0.65 during agent speech.
    # Checked by brain.py (per token), speaker.py (per sub-chunk), and speak_clause.
    # Must be cleared by front.py before each new LLM generation turn.
    interrupt_event: threading.Event = field(default_factory=threading.Event)

    # Cooldown prevents a single loud frame from triggering multiple rapid interrupts.
    interrupt_cooldown_sec: float = 0.3

    # Monotonic timestamp of the last barge-in interrupt (time.monotonic()).
    # Updated by listener.py on each successful barge-in trigger.
    last_interrupt_time: float = 0.0

    # FIX-B: Raised to 1800ms for web interview sessions.
    # WebSocket audio delivery introduces ~100–200ms of buffering latency through the
    # recv_worker → audio_queue → ws_stream_producer → listener chain. Furthermore, when
    # candidates wear headphones, the absence of room reverberation drops RMS to absolute zero
    # immediately upon brief natural thinking pauses. 1800ms (1.8s) provides natural human
    # conversational breathing room, preventing premature cutoffs mid-sentence.
    # Desktop/CLI sessions (no ws_audio_queue) reset to 800ms in listener.py finally block.
    pause_tolerance_ms: int = 1800     # Default — Web-safe (1800ms / 1.8s)
    tts_speed: float = 1.00          # Dynamic Kokoro TTS synthesis speed factor
    current_tone: str = "direct"     # Master emotional tone attribute for turn synthesis
    selected_voice: str = "af_bella" # Selected Kokoro TTS voice preset
    ptt_active: threading.Event = field(default_factory=threading.Event)
    last_vocal_anchor: str = ""      # Tracks last anchor to enforce anti-repetition rotation
    speaker_verifier: object | None = None   # SpeakerVerifier instance (None if disabled)
    turn_manager: object | None = None       # TurnManager instance (explicit state machine)
    enable_thought_classifier: bool = False  # Enable thought completion check for web if desired
    input_mode: str = "VAD"          # "VAD" (default) or "PTT"

    # FIX-A: Noise floor calibration cache — shared across all listen_and_transcribe() turns.
    # On the first turn, listener.py computes ambient_floor, start/continue RMS gates, and
    # optionally a NoiseReducer from 30 frames (~960ms) of startup silence. These are then
    # stored here so that subsequent turns SKIP the 960ms calibration window entirely.
    # Without caching, calibration runs at the beginning of EVERY turn and flushes the first
    # ~960ms of the candidate's audio from the queue before VAD even starts — causing the
    # leading edge of the candidate's response to be silently discarded, which then triggers
    # a premature "silence" endpoint while they are still mid-sentence.
    calibration_done: bool = False           # True after first successful calibration
    cached_ambient_floor: float = 0.008     # Fallback default until first calibration
    cached_start_rms_gate: float = 0.020    # RMS gate to start speech capture
    cached_continue_rms_gate: float = 0.014 # RMS gate to continue speech capture
    cached_noise_reducer: object | None = None  # NoiseReducer instance (desktop only)

    # Thread-safe Pause/Resume & Restart primitives for live web interviews
    is_paused: threading.Event = field(default_factory=threading.Event)
    restart_requested: threading.Event = field(default_factory=threading.Event)

    def pause(self):
        """Pauses STT listening and triggers interrupt on active speech synthesis."""
        self.is_paused.set()
        self.interrupt_event.set()

    def resume(self):
        """Resumes active STT listening and turn processing."""
        self.is_paused.clear()
        self.interrupt_event.clear()

    def request_restart(self):
        """Signals engine to interrupt current turn and restart interview from Turn 0."""
        self.restart_requested.set()
        self.interrupt_event.set()

    def clear_restart(self):
        """Clears the restart signal after engine has reset session state."""
        self.restart_requested.clear()
        self.interrupt_event.clear()

