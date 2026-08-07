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

    pause_tolerance_ms: int = 800      # Default ⚡ Fast Response (800ms / 0.8s)
    tts_speed: float = 1.00          # Dynamic Kokoro TTS synthesis speed factor
    current_tone: str = "direct"     # Master emotional tone attribute for turn synthesis
    selected_voice: str = "af_bella" # Selected Kokoro TTS voice preset
    input_mode: str = "VAD"          # Input mode: "VAD" or "PTT" (Push-To-Talk)
    ptt_active: threading.Event = field(default_factory=threading.Event)
    last_vocal_anchor: str = ""      # Tracks last anchor to enforce anti-repetition rotation
    speaker_verifier: object | None = None   # SpeakerVerifier instance (None if disabled)

