"""
Netran AI — Stage 3: Live Voice-to-Voice Loop
Module: speaker.py
Description: Streaming neural TTS playback engine using Kokoro-82M (af_bella voice)
             with producer-consumer audio queue, technical text normalizer, and
             SessionState-based echo gate tracking.

Full-Duplex Barge-In Architecture (v2):
  - frames_per_buffer reduced to 512 (~21ms) to minimize OS hardware buffer lag.
  - _play_loop writes audio in 1024-sample sub-chunks, checking interrupt_event
    between each write for <42ms granular abort.
  - stop_immediately() calls stream.stop_stream() + stream.start_stream() to
    hard-flush the WASAPI/ALSA/CoreAudio driver buffer.
  - speak_clause() checks both self.interrupt_event and state.interrupt_event so
    TTS synthesis aborts on the first barge-in signal from the listener.
"""

import queue
import re
import threading
import warnings
from typing import Optional

# Suppress PyTorch RNN and weight_norm deprecation noise
warnings.filterwarnings("ignore", category=UserWarning, module="torch.nn.modules.rnn")
warnings.filterwarnings("ignore", category=FutureWarning, module="torch.nn.utils.weight_norm")

import numpy as np
import sounddevice as sd
from kokoro import KPipeline

try:
    from .benchmark import Benchmark
    from .brain import TextSanitizer, get_speed_for_tone
    from .config import KOKORO_MODEL
    from .session_state import SessionState
except ImportError:
    try:
        from model.voice_to_voice_model.model.benchmark import Benchmark
        from model.voice_to_voice_model.model.brain import TextSanitizer, get_speed_for_tone
        from model.voice_to_voice_model.model.config import KOKORO_MODEL
        from model.voice_to_voice_model.model.session_state import SessionState
    except ImportError:
        from benchmark import Benchmark
        from brain import TextSanitizer, get_speed_for_tone
        from config import KOKORO_MODEL
        from session_state import SessionState


# Lazy-init sentinel: the heavy Kokoro model is only loaded on the FIRST call.
_kokoro_pipeline = None


def _get_pipeline():
    """Returns the shared Kokoro pipeline, initializing it on first use."""
    global _kokoro_pipeline
    if _kokoro_pipeline is None:
        print("Loading Kokoro TTS model into memory (offline mode)...", flush=True)
        _kokoro_pipeline = KPipeline(lang_code="a", repo_id=KOKORO_MODEL)
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
    Persistent PyAudio streaming TTS player with full-duplex barge-in support.

    Key design changes for instant interrupt:
    - frames_per_buffer=512 minimizes the OS hardware buffer (~21ms at 24kHz).
    - _play_loop writes audio in 1024-sample sub-chunks, checking interrupt_event
      between each write — maximum interrupt lag is one sub-chunk (~42ms).
    - stop_immediately() hard-resets the OS audio driver via stop_stream()/start_stream()
      rather than only draining the Python queue.
    """
    def __init__(self):
        import pyaudio
        self.audio_queue = queue.Queue(maxsize=32)
        self.interrupt_event = threading.Event()
        self.p = pyaudio.PyAudio()

        # frames_per_buffer=512 → ~21ms hardware buffer (was 2048 → ~85ms).
        # This minimises how much audio is already committed to the OS driver
        # when a barge-in fires. The tradeoff is slightly higher CPU callback rate.
        self.stream = self.p.open(
            format=pyaudio.paFloat32,
            channels=1,
            rate=24000,
            output=True,
            frames_per_buffer=512
        )
        self.is_running = True
        self.worker_thread = threading.Thread(target=self._play_loop, daemon=True)
        self.worker_thread.start()

    def _play_loop(self):
        """
        Consumer thread: drains audio_queue and writes to the PyAudio stream.

        Audio is written in 1024-sample sub-chunks (~42ms at 24kHz) so the
        interrupt_event can be checked between writes for granular abort capability.
        """
        SUB_CHUNK_SAMPLES = 1024  # ~42ms at 24kHz — granularity of interrupt checking
        while self.is_running:
            try:
                chunk = self.audio_queue.get(timeout=0.02)
                if chunk is not None:
                    chunk_bytes = chunk if isinstance(chunk, (bytes, bytearray)) else chunk.tobytes()
                    # Write in small sub-chunks, checking interrupt between each
                    bytes_per_sample = 4  # float32 = 4 bytes
                    step = SUB_CHUNK_SAMPLES * bytes_per_sample
                    for i in range(0, len(chunk_bytes), step):
                        if self.interrupt_event.is_set() or not self.is_running:
                            break
                        sub = chunk_bytes[i:i + step]
                        if sub:
                            self.stream.write(sub)
                    self.audio_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                print(f"[PersistentSpeaker Consumer Error] {e}", flush=True)

    def _drain_queue(self):
        """Drains all pending audio chunks from the Python software queue."""
        drained = 0
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
                self.audio_queue.task_done()
                drained += 1
            except queue.Empty:
                break
        if drained:
            print(f"[PersistentSpeaker] Drained {drained} queued audio chunks.", flush=True)

    def stop_immediately(self, state: Optional[SessionState] = None):
        """
        Full-duplex barge-in hardware flush.

        Step 1 — Set interrupt flag so _play_loop exits the current sub-chunk write.
        Step 2 — Drain Python queue so no buffered audio re-queues.
        Step 3 — Hard-reset the OS audio driver buffer via stop_stream()/start_stream().
                  This flushes ~21ms of committed audio in the WASAPI/ALSA/CoreAudio buffer.
        Step 4 — Clear agent speaking flag so listener resumes normal capture mode.
        """
        self.interrupt_event.set()
        self._drain_queue()

        # Hard-flush OS audio driver buffer (WASAPI/ALSA/CoreAudio)
        try:
            self.stream.stop_stream()
            self.stream.start_stream()
            print("[PersistentSpeaker] Hardware audio buffer flushed.", flush=True)
        except Exception as exc:
            print(f"[PersistentSpeaker] Buffer reset error (non-fatal): {exc}", flush=True)

        if state:
            state.is_agent_speaking.clear()
        elif _default_state:
            _default_state.is_agent_speaking.clear()

    def speak_clause(self, clause: str, state: SessionState, voice_preset: str = "af_bella", tone: Optional[str] = None):
        """
        Synthesize a single clause and enqueue audio chunks for playback.

        Checks both self.interrupt_event (hardware flush signal) and
        state.interrupt_event (barge-in signal from listener/brain) before
        synthesis and between each audio chunk, so TTS aborts within one
        Kokoro generation step (<50ms typically).
        Applies dynamic Kokoro speed factor resolved from tone attribute.
        """
        def _is_interrupted() -> bool:
            return (
                self.interrupt_event.is_set()
                or state.should_stop.is_set()
                or state.interrupt_event.is_set()
            )

        if not clause.strip() or _is_interrupted():
            return

        effective_voice = getattr(state, "selected_voice", voice_preset) if voice_preset == "af_bella" else voice_preset
        effective_tone = tone or getattr(state, "current_tone", "direct")
        clean_text = TextSanitizer.clean_for_tts(clause, tone=effective_tone)
        clean_text = normalize_technical_text_for_tts(clean_text)
        if not clean_text.strip():
            return

        try:
            speed = get_speed_for_tone(effective_tone, default_speed=state.tts_speed)
            generator = _get_pipeline()(clean_text, voice=effective_voice, speed=speed)

            for _, _, audio_array in generator:
                if audio_array is None or _is_interrupted():
                    break

                if hasattr(audio_array, "cpu"):
                    audio_array = audio_array.cpu().numpy()

                audio_data = audio_array.astype(np.float32)

                # Record true Time-To-First-Audio (TTFA) on first synthesized audio chunk
                if Benchmark.get_start_time("ttfa"):
                    ttfa_ms = Benchmark.end("ttfa")
                    Benchmark.last_ttfa_ms = ttfa_ms
                    print(f"[Benchmark] Time-To-First-Audio (TTFA): {ttfa_ms:.1f}ms", flush=True)

                while not _is_interrupted():
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
        state.interrupt_event.clear()
        state.is_agent_speaking.set()
        self.speak_clause(text_to_say, state, voice_preset)
        state.is_agent_speaking.clear()

    def close(self):
        """Shuts down the playback worker thread and releases PyAudio resources."""
        self.is_running = False
        self.interrupt_event.set()
        if self.worker_thread.is_alive():
            self.worker_thread.join(timeout=1.0)
        try:
            self.stream.stop_stream()
            self.stream.close()
        except Exception:
            pass
        try:
            self.p.terminate()
        except Exception:
            pass


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
        pipeline = _get_pipeline()
        for _, _, audio_array in pipeline(text_to_say, voice=voice_preset, speed=1.05):
            if audio_array is None:
                continue
            if hasattr(audio_array, "cpu"):
                audio_array = audio_array.cpu().numpy()
            sd.play(audio_array, samplerate=24000)
            sd.wait()


def force_stop_all():
    """Immediately stops all TTS playback by flushing the active player's queue and halting output."""
    if _default_player:
        _default_player.stop_immediately(_default_state)
    else:
        try:
            sd.stop()
        except Exception:
            pass