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
except ImportError:
    try:
        from model.voice_to_voice_model.model.session_state import SessionState
    except ImportError:
        from session_state import SessionState


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


class StreamingTTSPlayer:
    """
    ISSUE-4/SUG-2 Fix: Producer-Consumer audio queue eliminating inter-chunk gaps.
    Uses a persistent sd.OutputStream consumer thread to play audio chunks
    continuously while a background producer generates Kokoro numpy arrays.
    Supports immediate stop via should_stop event draining and sd.stop().
    """
    def __init__(self):
        self.audio_queue: queue.Queue = queue.Queue(maxsize=8)

    def _drain_queue(self):
        """Empties the audio queue to unblock any waiting producers and stop playback."""
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
            except queue.Empty:
                break

    def speak_text(self, text_to_say: str, state: SessionState, voice_preset: str = "af_bella"):
        """Generates and plays TTS audio for a single text string via queue."""
        if not text_to_say.strip():
            return

        state.is_agent_speaking.set()

        try:
            clean_text = normalize_technical_text_for_tts(text_to_say)
            if not clean_text.strip():
                return

            generator = _get_pipeline()(clean_text, voice=voice_preset, speed=state.tts_speed)

            # Consumer thread: plays audio continuously, checks should_stop every chunk
            def _consumer():
                try:
                    with sd.OutputStream(samplerate=24000, channels=1, dtype='float32') as stream:
                        while True:
                            if state.should_stop.is_set():
                                break
                            chunk = None
                            while not state.should_stop.is_set():
                                try:
                                    chunk = self.audio_queue.get(timeout=0.2)
                                    break
                                except queue.Empty:
                                    pass
                            if chunk is None:
                                break
                            if state.should_stop.is_set():
                                break
                            if hasattr(chunk, "cpu"):
                                chunk = chunk.cpu().numpy()
                            audio_data = chunk.reshape(-1, 1).astype(np.float32)
                            stream.write(audio_data)
                except Exception as e:
                    print(f"[StreamingTTSPlayer Consumer Error] {e}", flush=True)
                finally:
                    if state.should_stop.is_set():
                        sd.stop()

            consumer = threading.Thread(target=_consumer, daemon=True)
            consumer.start()

            # Producer: generate Kokoro chunks and push to queue
            for _, _, audio_array in generator:
                if audio_array is None or state.should_stop.is_set():
                    break
                while not state.should_stop.is_set():
                    try:
                        self.audio_queue.put(audio_array, timeout=0.2)
                        break
                    except queue.Full:
                        pass

            # If stopped mid-speech, drain remaining chunks to unblock consumer
            if state.should_stop.is_set():
                self._drain_queue()
                sd.stop()

            self.audio_queue.put(None)  # Sentinel to signal completion
            consumer.join()

        except Exception as e:
            print(f"\n[StreamingTTSPlayer Error: {e!s}]", flush=True)

        finally:
            state.is_agent_speaking.clear()

    def play_stream(self, sentence_generator: Generator[str, None, None], state: SessionState, voice_preset: str = "af_bella"):
        """
        Plays a stream of sentences from an LLM token accumulator.
        Each sentence is normalized, synthesized, and queued for continuous playback.
        """
        if state.should_stop.is_set():
            return

        state.is_agent_speaking.set()

        try:
            def _consumer():
                try:
                    with sd.OutputStream(samplerate=24000, channels=1, dtype='float32') as stream:
                        while True:
                            if state.should_stop.is_set():
                                break
                            chunk = None
                            while not state.should_stop.is_set():
                                try:
                                    chunk = self.audio_queue.get(timeout=0.2)
                                    break
                                except queue.Empty:
                                    pass
                            if chunk is None:
                                break
                            if state.should_stop.is_set():
                                break
                            if hasattr(chunk, "cpu"):
                                chunk = chunk.cpu().numpy()
                            audio_data = chunk.reshape(-1, 1).astype(np.float32)
                            stream.write(audio_data)
                except Exception as e:
                    print(f"[StreamingTTSPlayer Consumer Error] {e}", flush=True)
                finally:
                    if state.should_stop.is_set():
                        sd.stop()

            consumer = threading.Thread(target=_consumer, daemon=True)
            consumer.start()

            for sentence in sentence_generator:
                if state.should_stop.is_set():
                    break
                clean_text = normalize_technical_text_for_tts(sentence)
                if not clean_text.strip():
                    continue
                for _, _, audio_array in _get_pipeline()(clean_text, voice=voice_preset, speed=state.tts_speed):
                    if audio_array is not None and not state.should_stop.is_set():
                        while not state.should_stop.is_set():
                            try:
                                self.audio_queue.put(audio_array, timeout=0.2)
                                break
                            except queue.Full:
                                pass
                    if state.should_stop.is_set():
                        break

            # If stopped mid-speech, drain remaining chunks to unblock consumer
            if state.should_stop.is_set():
                self._drain_queue()
                sd.stop()

            self.audio_queue.put(None)
            consumer.join()

        except Exception as e:
            print(f"\n[StreamingTTSPlayer Error: {e!s}]", flush=True)

        finally:
            state.is_agent_speaking.clear()


# ---- Backward-compatible wrapper for existing front.py code ----
_default_player: Optional[StreamingTTSPlayer] = None
_default_state: Optional[SessionState] = None

def init_speaker_compat(state: SessionState):
    """Initialize backward-compatible speaker with shared SessionState."""
    global _default_player, _default_state
    _default_player = StreamingTTSPlayer()
    _default_state = state

def speak_text(text_to_say, voice_preset="af_bella"):
    """Backward-compatible speak_text() using StreamingTTSPlayer internally."""
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
    """Immediately stops all TTS playback by draining the active player's queue."""
    if _default_player:
        _default_player._drain_queue()
    try:
        import sounddevice as sd
        sd.stop()
    except Exception:
        pass