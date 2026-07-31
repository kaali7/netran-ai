"""
Netran AI — Stage 3: Live Voice-to-Voice Loop
Module: speaker.py
Description: Streaming neural TTS playback engine using Kokoro-82M (af_bella voice)
             with producer-consumer audio queue, technical text normalizer, and
             SessionState-based echo gate tracking.
"""

import queue
import re
import threading
from typing import Generator, Optional

import numpy as np
import sounddevice as sd
from kokoro import KPipeline

try:
    from .session_state import SessionState
    from .brain import TextSanitizer
except ImportError:
    try:
        from model.voice_to_voice_model.model.session_state import SessionState
        from model.voice_to_voice_model.model.brain import TextSanitizer
    except ImportError:
        from session_state import SessionState
        from brain import TextSanitizer


# Lazy-init sentinel: the heavy Kokoro model is only loaded on the FIRST call.
_kokoro_pipeline = None


def _get_pipeline():
    """Returns the shared Kokoro pipeline, initializing it on first use."""
    global _kokoro_pipeline
    if _kokoro_pipeline is None:
        print("Loading Kokoro TTS model into memory...")
        _kokoro_pipeline = KPipeline(lang_code="a")
    return _kokoro_pipeline


def preload_models():
    """Preloads the heavy TTS models into memory."""
    print("Pre-heating Kokoro TTS engine...", flush=True)
    _get_pipeline()


def normalize_technical_text_for_tts(text: str) -> str:
    """
    ISSUE-8/SUG-4 Fix: Prevents broken TTS pauses on technical syntax.
    Converts version numbers, framework names, and protocol identifiers
    into speakable plain English before Kokoro synthesis.
    """
    if not text:
        return ""
    text = re.sub(r'(\w+)\.js\b', r'\1 js', text, flags=re.IGNORECASE)       # Next.js → Next js
    text = re.sub(r'(\d+)\.(\d+)', r'\1 point \2', text)                      # 3.11 → 3 point 11
    text = re.sub(r'HTTP/(\d+)\.(\d+)', r'HTTP \1 point \2', text)            # HTTP/1.1 → HTTP 1 point 1
    text = re.sub(r'gRPC', 'G R P C', text)                                   # gRPC → G R P C
    text = re.sub(r'PostgreSQL', 'Postgres Q L', text, flags=re.IGNORECASE)   # PostgreSQL → Postgres Q L
    return text


class PersistentSpeaker:
    """
    Persistent PyAudio streaming TTS player.
    Keeps a background output stream open to eliminate TTFA latency.
    """
    def __init__(self):
        import pyaudio
        self.audio_queue = queue.Queue(maxsize=32)
        self.interrupt_event = threading.Event()
        self.p = pyaudio.PyAudio()
        
        self.stream = self.p.open(
            format=pyaudio.paFloat32,
            channels=1,
            rate=24000,
            output=True,
            frames_per_buffer=2048
        )
        self.is_running = True
        self.worker_thread = threading.Thread(target=self._play_loop, daemon=True)
        self.worker_thread.start()

    def _play_loop(self):
        while self.is_running:
            try:
                chunk = self.audio_queue.get(timeout=0.05)
                if chunk is not None:
                    self.stream.write(chunk.tobytes())
            except queue.Empty:
                continue
            except Exception as e:
                print(f"[PersistentSpeaker Consumer Error] {e}", flush=True)

    def _drain_queue(self):
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
            except queue.Empty:
                break

    def stop_immediately(self, state: Optional[SessionState] = None):
        """Instantly flush queue. Stream remains open."""
        self.interrupt_event.set()
        self._drain_queue()
        
        try:
            self.stream.stop_stream()
            self.stream.start_stream()
        except Exception:
            pass
            
        if state:
            state.is_agent_speaking.clear()
        elif _default_state:
            _default_state.is_agent_speaking.clear()

    def speak_clause(self, clause: str, state: SessionState, voice_preset: str = "af_bella"):
        if not clause.strip() or self.interrupt_event.is_set() or state.should_stop.is_set():
            return
            
        clean_text = TextSanitizer.clean_for_tts(clause)
        clean_text = normalize_technical_text_for_tts(clean_text)
        if not clean_text.strip():
            return
            
        try:
            generator = _get_pipeline()(clean_text, voice=voice_preset, speed=state.tts_speed)
            
            for _, _, audio_array in generator:
                if audio_array is None or self.interrupt_event.is_set() or state.should_stop.is_set():
                    break
                
                if hasattr(audio_array, "cpu"):
                    audio_array = audio_array.cpu().numpy()
                
                audio_data = audio_array.astype(np.float32)
                
                while not (self.interrupt_event.is_set() or state.should_stop.is_set()):
                    try:
                        self.audio_queue.put(audio_data, timeout=0.1)
                        break
                    except queue.Full:
                        pass
        except Exception as e:
            print(f"\n[PersistentSpeaker Error: {e!s}]", flush=True)

    def speak_text(self, text_to_say: str, state: SessionState, voice_preset: str = "af_bella"):
        """Maintains backward compatibility for full phrases."""
        self.interrupt_event.clear()
        state.is_agent_speaking.set()
        self.speak_clause(text_to_say, state, voice_preset)
        state.is_agent_speaking.clear()

# ---- Backward-compatible wrapper for existing front.py code ----
_default_player: Optional[PersistentSpeaker] = None
_default_state: Optional[SessionState] = None

def init_speaker_compat(state: SessionState):
    """Initialize backward-compatible speaker with shared SessionState."""
    global _default_player, _default_state
    _default_player = PersistentSpeaker()
    _default_state = state

def get_default_player():
    return _default_player

def speak_text(text_to_say, voice_preset="af_bella"):
    """Backward-compatible speak_text() using PersistentSpeaker internally."""
    if _default_player and _default_state:
        _default_player.speak_text(text_to_say, _default_state, voice_preset)
    else:
        # Fallback: original serial playback if init_speaker_compat() wasn't called
        import sounddevice as sd
        pipeline = _get_pipeline()
        for _, _, audio_array in pipeline(text_to_say, voice=voice_preset, speed=1.05):
            if audio_array is None:
                continue
            if hasattr(audio_array, "cpu"):
                audio_array = audio_array.cpu().numpy()
            sd.play(audio_array, samplerate=24000)
            sd.wait()

# Provide IS_AGENT_SPEAKING flag for backward compatibility
class DummyEvent:
    def is_set(self): return False
IS_AGENT_SPEAKING = DummyEvent()

def force_stop_all():
    """Immediately stops all TTS playback by draining the active player's queue and halting output."""
    if _default_player:
        _default_player.stop_immediately(_default_state)
    else:
        try:
            import sounddevice as sd
            sd.stop()
        except Exception:
            pass