"""
Netran AI — Stage 3: Live Voice-to-Voice Loop
Module: session_state.py
Description: Thread-safe synchronization object shared across listener, speaker, and front.
             Replaces broken importlib-based echo gate with threading.Event primitives.
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
    pause_tolerance_ms: int = 1600   # Default ⚖️ Balanced (1.6s)
    tts_speed: float = 1.05          # Slightly faster for natural interviewer cadence
