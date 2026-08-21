"""
Netran AI — Stage 3: Live Voice-to-Voice Loop
Module: listener.py
Description: Audio capture engine utilizing sounddevice, Silero VAD ONNX inference,
             dynamic peak auto-gain normalization, Faster-Whisper int8 STT,
             asynchronous continuous PCM mic WAV streaming, and Whisper hallucination filtering.

Full-Duplex Barge-In Architecture (v3 — TRUE FIX):
  - Root cause: listen_and_transcribe() is called AFTER speak_text() returns,
    so the microphone was never open while Eva was playing audio.
    Barge-in code inside listen_and_transcribe could never fire.
  - Fix: BargeInWatcher opens its OWN independent sounddevice input stream in a
    background daemon thread and runs Silero VAD concurrently with TTS playback.
    front.py starts the watcher BEFORE speaking and stops it after the audio drains.
  - When speech_prob > 0.65, BargeInWatcher sets state.interrupt_event,
    calls force_stop_all() to hardware-flush audio, and exits.
  - listen_and_transcribe() then captures the candidate's barge-in speech normally.
"""

import atexit
import queue
import wave
import threading
import time
import os
import sys
import warnings
import collections
from pathlib import Path
from dotenv import load_dotenv

# Force offline mode for Hugging Face / Transformers before imports
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

# Load backend root .env file
env_path = Path(__file__).resolve().parent.parent.parent.parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

with warnings.catch_warnings():
    warnings.simplefilter("ignore", DeprecationWarning)
    import audioop

import numpy as np
import onnxruntime as ort
import sounddevice as sd
from faster_whisper import WhisperModel

try:
    from .benchmark import Benchmark
    from .config import WHISPER_MODEL, MIC_DEVICE_INDEX, auto_select_mic_device
    from .session_state import SessionState
    from .turn_classifier import check_thought_completion
    try:
        from .speaker_verifier import SpeakerVerifier
    except ImportError:
        SpeakerVerifier = None
except ImportError:
    try:
        from model.voice_to_voice_model.model.benchmark import Benchmark
        from model.voice_to_voice_model.model.config import (
            WHISPER_MODEL,
            MIC_DEVICE_INDEX,
            auto_select_mic_device,
        )
        from model.voice_to_voice_model.model.session_state import SessionState
        from model.voice_to_voice_model.model.turn_classifier import (
            check_thought_completion,
        )
        try:
            from model.voice_to_voice_model.model.speaker_verifier import SpeakerVerifier
        except ImportError:
            SpeakerVerifier = None
    except ImportError:
        from benchmark import Benchmark
        from config import WHISPER_MODEL, MIC_DEVICE_INDEX, auto_select_mic_device
        from session_state import SessionState
        from turn_classifier import check_thought_completion
        try:
            from speaker_verifier import SpeakerVerifier
        except ImportError:
            SpeakerVerifier = None


# Global setup
VAD_MODEL_PATH = os.path.join(os.path.dirname(__file__), "silero_vad.onnx")

print("Loading Silero VAD model...", flush=True)
# Disable logging/profiling in onnxruntime to keep output clean
ort_opts = ort.SessionOptions()
ort_opts.log_severity_level = 3
vad_session = ort.InferenceSession(VAD_MODEL_PATH, ort_opts)

# Loads from local offline snapshot path directly
print(f"Loading Faster-Whisper model ({WHISPER_MODEL})...", flush=True)
whisper_model = WhisperModel(WHISPER_MODEL, device="cpu", compute_type="int8", cpu_threads=4)
print("Models loaded successfully!", flush=True)

# Auto-select the best available physical microphone at startup.
# Stored globally so both listen_and_transcribe() and BargeInWatcher use the same device.
MIC_DEVICE = MIC_DEVICE_INDEX if MIC_DEVICE_INDEX is not None else auto_select_mic_device()

# Known Whisper hallucinations on silence or background static
WHISPER_HALLUCINATION_PATTERNS = {
    "thank you.", "thanks for watching.", "subscribe to my channel.",
    "you", "thank you very much.", "bye.", "so", "am", "oh.", "next.",
    "thanks.", "bye bye.", "see you next time.", "please subscribe.",
    "like and subscribe.", "thank you for watching.", "oh", "next",
    "uh", "um", "ah", "ah.", "huh", "huh.", "okay.", "okay", "yes.", "no."
}

def is_valid_transcript(text: str) -> bool:
    """Filters empty strings, single filler letters, and Whisper silent hallucinations."""
    clean = text.strip().lower()
    if not clean or clean in WHISPER_HALLUCINATION_PATTERNS:
        return False
    
    # Filter out pure underscore/punctuation hallucinations caused by heavy static
    if all(char in "_ .-" for char in clean):
        return False
        
    words = clean.split()
    if len(words) < 2 and clean not in {"yes", "no", "sure", "ok", "correct", "yeah", "nope", "fastapi", "python"}:
        return False
    return True



class NoiseReducer:
    """
    Wiener filter + spectral gating noise suppression using noisereduce library.

    Handles BOTH stationary noise (fan, AC, HVAC) AND transient bursts
    (keyboard clicks, mouse, door slams) that the old FFT power subtraction missed.

    Initialized during calibration with a noise profile from silence frames.
    Applied per-chunk to the VAD input frame BEFORE Silero VAD inference.
    """

    def __init__(self, noise_clip: np.ndarray, sr: int = 16000):
        """
        Args:
            noise_clip: 1D float32 array of ambient noise audio captured
                        during calibration (~960ms of silence).
            sr: Sample rate (must be 16000 for Silero VAD compatibility).
        """
        self.noise_clip = noise_clip
        self.sr = sr

    def suppress(self, frame: np.ndarray) -> np.ndarray:
        """
        Applies noise suppression to a single 32ms frame (512 samples at 16kHz).

        Uses stationary=True for consistent stationary noise removal with
        the calibrated noise profile. prop_decrease=0.85 keeps 15% of noise
        energy to prevent musical noise artifacts.

        Args:
            frame: float32 array of exactly 512 samples.

        Returns:
            Noise-suppressed float32 frame, same length as input.
        """
        try:
            import noisereduce as nr
            reduced = nr.reduce_noise(
                y=frame,
                sr=self.sr,
                y_noise=self.noise_clip,
                stationary=True,
                prop_decrease=0.85,
                n_fft=512,
                hop_length=128,
            )
            return reduced.astype(np.float32)
        except Exception:
            return frame




def _transcribe_audio_buffer(audio_buffer, whisper_prompt=""):
    if not audio_buffer:
        return ""
    audio_array = np.concatenate(audio_buffer)
    alpha = 0.995
    filtered = np.empty_like(audio_array)
    filtered[0] = 0.0
    for i in range(1, len(audio_array)):
        filtered[i] = alpha * (filtered[i - 1] + audio_array[i] - audio_array[i - 1])
    audio_array = filtered

    final_gain = 1.0
    utterance_peak = float(np.max(np.abs(audio_array)))
    if utterance_peak > 0.0001:
        final_gain = min(0.9 / utterance_peak, 15.0)
        audio_array = audio_array * final_gain

    segments, _ = whisper_model.transcribe(
        audio_array,
        language="en",
        initial_prompt=whisper_prompt,
        beam_size=1,
        best_of=1,
        temperature=0.0,
        condition_on_previous_text=False,
        no_speech_threshold=0.6,
        hallucination_silence_threshold=2.0,
        vad_filter=False,
        compression_ratio_threshold=2.4,
    )
    return "".join([segment.text for segment in segments]).strip()


def listen_and_transcribe(
    ui_callback=None,
    mic_writer=None,
    state: SessionState = None,
    whisper_prompt="",
    speaker_verifier=None,
    ws_audio_queue=None,
):
    """
    Opens the microphone, uses Silero VAD (or Push-To-Talk mode) to detect speech start and end,
    respects the echo gate via SessionState, transcribes the speech using Faster-Whisper,
    and optionally streams raw frames to continuous mic writer.
    """
    # Audio hardware recording constraints
    CHANNELS = 1
    RATE = 16000     # 16kHz for VAD and Whisper
    CHUNK = 512      # Silero VAD v4 requires EXACTLY 512 samples at 16kHz
    assert CHUNK == 512, f"[VAD Guard] Silero VAD requires exactly 512 samples at 16kHz, got {CHUNK}"

    device_info = sd.query_devices(MIC_DEVICE) if MIC_DEVICE is not None else sd.query_devices(sd.default.device[0])
    native_rate = int(device_info.get("default_samplerate", 16000))
    if native_rate <= 0:
        native_rate = 16000
    CHUNK_NATIVE = int(CHUNK * native_rate / RATE)


    # --- Robust microphone stream initialization ---
    stream = None
    native_rate = RATE
    CHUNK_NATIVE = CHUNK
    
    audio_queue = queue.Queue()
    stop_producer = threading.Event()

    if ws_audio_queue is not None:
        print("[Listener] Using WebSocket audio stream...", flush=True)
        def ws_stream_producer():
            """Producer Thread: Continuously drains audio from WebSocket queue and buffers CHUNK samples."""
            import numpy as np
            buffer_arr = np.array([], dtype=np.float32)
            while not stop_producer.is_set():
                try:
                    # Raw PCM Int16 bytes from frontend Worklet
                    raw_bytes = ws_audio_queue.get(timeout=0.1)
                    if not raw_bytes:
                        continue
                    # Convert Int16 bytes to float32
                    int16_arr = np.frombuffer(raw_bytes, dtype=np.int16)
                    float32_arr = int16_arr.astype(np.float32) / 32768.0
                    buffer_arr = np.concatenate((buffer_arr, float32_arr))
                    
                    while len(buffer_arr) >= CHUNK_NATIVE:
                        chunk_to_send = buffer_arr[:CHUNK_NATIVE]
                        buffer_arr = buffer_arr[CHUNK_NATIVE:]
                        audio_queue.put(chunk_to_send.reshape(-1, 1))
                except queue.Empty:
                    continue
                except Exception as err:
                    print(f"[WS Producer Error] {err}", flush=True)
                    
        producer_thread = threading.Thread(target=ws_stream_producer, daemon=True)
        producer_thread.start()
    else:
        for attempt in range(3):
            try:
                # Attempt Method B: native OS resampling (works beautifully on MME/DirectSound)
                stream = sd.InputStream(
                    samplerate=RATE,
                    channels=CHANNELS,
                    dtype='float32',
                    blocksize=CHUNK,
                    device=MIC_DEVICE,
                )
                native_rate = RATE
                CHUNK_NATIVE = CHUNK
                break
            except sd.PortAudioError:
                try:
                    # Fallback Method A: WASAPI strictly requires native rate
                    device_info = sd.query_devices(MIC_DEVICE) if MIC_DEVICE is not None else sd.query_devices(sd.default.device[0])
                    native_rate = int(device_info.get("default_samplerate", 16000))
                    if native_rate <= 0:
                        native_rate = 16000
                    CHUNK_NATIVE = int(CHUNK * native_rate / RATE)
                    
                    stream = sd.InputStream(
                        samplerate=native_rate,
                        channels=CHANNELS,
                        dtype='float32',
                        blocksize=CHUNK_NATIVE,
                        device=MIC_DEVICE,
                    )
                    break
                except Exception as e:
                    if attempt < 2:
                        print(f"[VAD] Mic locked, retrying... ({e})")
                        time.sleep(0.3)
                    else:
                        raise RuntimeError(f"Could not open microphone after 3 attempts: {e}")
            except Exception as e:
                if attempt < 2:
                    print(f"[VAD] Mic locked, retrying... ({e})")
                    time.sleep(0.3)
                else:
                    raise RuntimeError(f"Could not open microphone after 3 attempts: {e}")

        stream.start()
        print(
            f"[Listener] Mic stream opened: device={MIC_DEVICE}, "
            f"native_rate={native_rate}Hz, chunk={CHUNK_NATIVE} samples",
            flush=True
        )

        def mic_stream_producer():
            """Producer Thread: Continuously drains audio hardware buffer."""
            while not stop_producer.is_set():
                try:
                    raw_data, overflowed = stream.read(CHUNK_NATIVE)
                    audio_queue.put(raw_data)
                except Exception as err:
                    if not stream.active:
                        break
                    print(f"[Producer Thread Warning] {err}", flush=True)

        producer_thread = threading.Thread(target=mic_stream_producer, daemon=True)
        producer_thread.start()

    if ui_callback:
        ui_callback({
            "type": "audio_level",
            "rms": 0.0,
            "vad_prob": 0.0,
            "state": "Listening... Speak into your microphone"
        })

    is_ptt = bool(state and getattr(state, "input_mode", "VAD") == "PTT")
    if is_ptt:
        print("\n[Push-To-Talk Active] Hold PTT button or Spacebar to speak...", flush=True)
    else:
        print("\n[Listening...] Speak into your microphone now.", flush=True)

    # --- INLINE NOISE FLOOR CALIBRATION ---
    # Perform calibration using the ALREADY RUNNING producer queue.
    # This completely eliminates PortAudio hook lockups caused by rapid stream open/close events on Windows.
    _ratecv_state = None   # Persistent audioop.ratecv interpolation state across chunks
    ambient_floor = 0.008
    noise_reducer = None
    
    env_override = os.environ.get("NOISE_FLOOR_OVERRIDE", "").strip()
    if env_override:
        try:
            ambient_floor = float(env_override)
            print(f"[Calibration] NOISE_FLOOR_OVERRIDE active: {ambient_floor:.5f}", flush=True)
        except ValueError:
            pass
    else:
        num_frames = 30
        print(f"[Calibration] Sampling inline noise profile ({num_frames * 32}ms)...", flush=True)
        rms_samples = []
        clean_frames = []
        
        # Drain any immediate garbage frames
        while not audio_queue.empty():
            try: audio_queue.get_nowait()
            except queue.Empty: break
            
        for _ in range(num_frames):
            try:
                raw_data = audio_queue.get(timeout=1.0)
                original_frame = raw_data.flatten()
                
                if native_rate == 48000 and RATE == 16000:
                    original_frame = original_frame.reshape(-1, 3).mean(axis=1).astype(np.float32)
                elif native_rate != RATE:
                    pcm16 = (original_frame * 32767.0).astype(np.int16)
                    resampled_pcm, _ratecv_state = audioop.ratecv(
                        pcm16.tobytes(), 2, 1, native_rate, RATE, _ratecv_state
                    )
                    original_frame = np.frombuffer(resampled_pcm, dtype=np.int16).astype(np.float32) / 32767.0
                    
                frame = original_frame.copy()
                if len(frame) >= CHUNK:
                    frame = frame[:CHUNK]
                else:
                    frame = np.pad(frame, (0, CHUNK - len(frame)), mode='constant')
                    
                rms_samples.append(float(np.sqrt(np.mean(frame ** 2))))
                clean_frames.append(frame)
            except queue.Empty:
                break
                
        if rms_samples:
            ambient_floor = float(np.percentile(rms_samples, 90))
            ambient_floor = min(ambient_floor, 0.040)
            ambient_floor = max(ambient_floor, 0.002)
            print(
                f"[Calibration] Noise floor = {ambient_floor:.5f}  "
                f"(min={min(rms_samples):.5f}  max={max(rms_samples):.5f}  p90={ambient_floor:.5f})",
                flush=True,
            )
            if clean_frames:
                try:
                    noise_clip = np.concatenate(clean_frames)
                    noise_reducer = NoiseReducer(noise_clip=noise_clip, sr=RATE)
                    print(f"[Calibration] NoiseReducer initialized ({len(clean_frames)} frames)", flush=True)
                except Exception as nr_exc:
                    print(f"[Calibration] Could not init NoiseReducer ({nr_exc})", flush=True)
        else:
            print("[Calibration] Timed out waiting for audio frames. Using default 0.008 floor.", flush=True)

    _start_rms_gate    = max(ambient_floor * 2.5, 0.012)
    _continue_rms_gate = max(ambient_floor * 1.8, 0.010)
    print(
        f"[Calibration] Gates → start_rms={_start_rms_gate:.5f}  "
        f"continue_rms={_continue_rms_gate:.5f}  "
        f"noise_suppress={'ON' if noise_reducer is not None else 'OFF'}",
        flush=True,
    )
    
    audio_buffer = []
    _cached_interim_transcript = None
    pre_speech_buffer = collections.deque(maxlen=15)  # 480ms ring buffer
    has_spoken = False
    has_extended_silence = False
    speech_start_candidate_frames = 0
    rms_start_candidate_frames = 0     # RMS-only speech start fallback counter
    silence_frames_counter = 0
    _diag_frame_counter = 0            # Periodic VAD diagnostic counter
    _echo_guard_until = 0.0   # Monotonic timestamp for post-TTS silence guard window

    # Defaults if state isn't provided (for standalone tests) — 800ms default pause tolerance (25 frames * 32ms)
    max_silence_frames = 25 if state is None else max(8, state.pause_tolerance_ms // 32)
    MIN_SPEECH_FRAMES = 15   # Must accumulate at least 15 frames (~480ms) before endpointing is allowed
    total_frames_counter = 0
    MAX_RECORDING_FRAMES = 1875  # 60s hard timeout (1875 * 32ms = 60,000ms) — applies AFTER speech starts
    MAX_IDLE_WAIT_SEC = 90.0     # 90s hard timeout — applies BEFORE speech starts (waiting for first word)


    if state:
        state.is_candidate_speaking.clear()
        state.force_speech_done.clear()

    # Initialize VAD state tensors (Silero VAD v3 ONNX: only state is required, no context)
    vad_state = np.zeros((2, 1, 128), dtype=np.float32)
    sr_scalar = np.array(RATE, dtype=np.int64)
    # Streaming IIR DC blocker state (applied per-frame BEFORE VAD to remove DC offset).
    # Carries state across chunks for temporal continuity (Rule 11 compliant).
    _dc_prev_in = 0.0
    _dc_prev_out = 0.0
    
    # _ratecv_state is already initialized by calibration
    _listen_start_time = time.monotonic()  # Wall-clock start for pre-speech idle timeout


    try:
        while True:
            # Check external stop or manual submit flags
            if state:
                if state.should_stop.is_set():
                    break
                if state.force_speech_done.is_set():
                    print("[Manual Done Speaking Triggered! Processing speech...]", flush=True)
                    state.force_speech_done.clear()
                    break

            # 1. Read raw PCM data from Producer Queue
            try:
                raw_data = audio_queue.get(timeout=0.1)
                original_frame = raw_data.flatten()
            except queue.Empty:
                continue

            # Anti-aliased integer decimation for 48kHz -> 16kHz
            if native_rate == 48000 and RATE == 16000:
                original_frame = original_frame.reshape(-1, 3).mean(axis=1).astype(np.float32)
            elif native_rate != RATE:
                pcm16 = (original_frame * 32767.0).astype(np.int16)
                resampled_pcm, _ratecv_state = audioop.ratecv(
                    pcm16.tobytes(), 2, 1, native_rate, RATE, _ratecv_state
                )
                original_frame = np.frombuffer(resampled_pcm, dtype=np.int16).astype(np.float32) / 32767.0

            # --- Audio Pre-Gain ---
            # For physical desktop mic hardware (low gain capture at -78.4 dBFS),
            # apply 20x gain multiplier. For WebSockets (standard normalized browser audio),
            # keep 1.0x gain to prevent background noise from saturating the continuation gate.
            pre_gain = 1.0 if ws_audio_queue is not None else 20.0
            original_frame = original_frame * pre_gain
            
            # 2. Prepare VAD frame: apply streaming DC blocker BEFORE Silero VAD.
            #    Silero VAD is trained on zero-centered audio. Even a tiny DC offset
            #    (+0.005) causes the RNN hidden state to saturate -> prob = 0.000.
            #    The IIR high-pass (alpha=0.995, ~5Hz cutoff) removes DC drift while
            #    preserving speech energy, maintaining temporal continuity across chunks.
            vad_frame = original_frame.copy()
            _dc_alpha = 0.995
            for _s in range(len(vad_frame)):
                _in_val = float(vad_frame[_s])
                _dc_prev_out = _dc_alpha * (_dc_prev_out + _in_val - _dc_prev_in)
                _dc_prev_in = _in_val
                vad_frame[_s] = _dc_prev_out
            if len(vad_frame) < CHUNK:
                vad_frame = np.pad(vad_frame, (0, CHUNK - len(vad_frame)), mode='edge')

            # Compute RMS on the VAD (raw) frame for gate decisions
            rms = float(np.sqrt(np.mean(vad_frame ** 2)))

            # --- Noise suppression DEFERRED to post-buffer (Bug #2 fix) ---
            # Noise reduction is now applied ONCE on the full contiguous buffer
            # before STT, eliminating windowing artifacts.

            proc_frame = np.clip(vad_frame.copy(), -1.0, 1.0)

            if mic_writer:
                mic_writer.write_frame(proc_frame)

            # Prepare VAD inputs: shape [1, 512]. Feed the DC-filtered, 20x-boosted audio to VAD.
            audio_input = np.expand_dims(proc_frame, axis=0)

            # 3. Run Silero VAD v3 — 3 inputs: input, state, sr
            ort_inputs = {
                "input": audio_input,
                "state": vad_state,
                "sr": sr_scalar,
            }
            ort_outputs = vad_session.run(None, ort_inputs)
            out   = ort_outputs[0]   # shape [1, 1]
            vad_state = ort_outputs[1]   # updated hidden state
            speech_prob = out[0, 0]


            # 3b. Full-Duplex Barge-In Detection & Echo Guard
            # (rms already computed from raw vad_frame above)

            if state and state.is_agent_speaking.is_set():
                _echo_guard_until = time.monotonic() + 0.30  # Arm 300ms post-speech guard window
                if speech_prob > 0.65:
                    now = time.monotonic()
                    cooldown = getattr(state, 'interrupt_cooldown_sec', 0.3)
                    last_t = getattr(state, 'last_interrupt_time', 0.0)
                    if now - last_t > cooldown:
                        print("⚡ [Barge-In] Candidate interrupted Eva! Halting audio output.", flush=True)
                        state.interrupt_event.set()
                        state.last_interrupt_time = now
                        try:
                            from .speaker import force_stop_all
                        except ImportError:
                            try:
                                from model.voice_to_voice_model.model.speaker import (
                                    force_stop_all,
                                )
                            except ImportError:
                                from speaker import force_stop_all
                        force_stop_all()
                        state.is_agent_speaking.clear()
                        _echo_guard_until = 0.0  # Cancel guard when candidate barged in
                else:
                    silence_frames_counter = 0
                    continue

            # Post-TTS Echo Guard: suppress VAD triggers during post-speech room acoustic decay
            if time.monotonic() < _echo_guard_until:
                continue

            # 4. Speech Start/End Decision Logic
            _diag_frame_counter += 1


            # Periodic VAD diagnostic: print live VAD prob + RMS every ~2s (60 frames * 32ms)
            # This helps calibrate thresholds when speech is not being detected.
            if _diag_frame_counter % 60 == 0 and not has_spoken:
                print(
                    f"[VAD Diag] prob={speech_prob:.3f}  rms={rms:.4f}  "
                    f"(gates: prob>=0.30+rms>={_start_rms_gate:.4f} OR prob>=0.50)",
                    flush=True
                )

            if not has_spoken:

                # --- Adaptive Speech START Gate (hybrid VAD + RMS) ---
                # Primary path  : VAD prob >= 0.30 AND rms > _start_rms_gate  (debounce 2 frames ~64ms)
                # Strong path   : VAD prob >= 0.50 alone (confident speech, no RMS needed)
                # RMS fallback  : rms > _start_rms_gate for 4 consecutive frames (~128ms)
                vad_triggered = (
                    (speech_prob >= 0.30 and rms >= _start_rms_gate)
                    or speech_prob >= 0.50
                )
                rms_triggered = rms >= _start_rms_gate

                if vad_triggered:
                    speech_start_candidate_frames += 1
                    rms_start_candidate_frames = 0
                    if speech_start_candidate_frames >= 2:   # ~64ms debounce
                        print(
                            f"[Speech Detected! VAD] prob={speech_prob:.2f}, RMS={rms:.4f}, "
                            f"gate={_start_rms_gate:.4f}",
                            flush=True
                        )
                        has_spoken = True
                        audio_buffer.extend(pre_speech_buffer)
                        if state:
                            state.is_candidate_speaking.set()
                        silence_frames_counter = 0
                elif rms_triggered:
                    rms_start_candidate_frames += 1
                    speech_start_candidate_frames = 0
                    if rms_start_candidate_frames >= 4:   # ~128ms debounce
                        print(
                            f"[Speech Detected! RMS-only] prob={speech_prob:.2f}, RMS={rms:.4f}, "
                            f"gate={_start_rms_gate:.4f} (VAD unreliable — using RMS fallback)",
                            flush=True
                        )
                        has_spoken = True
                        audio_buffer.extend(pre_speech_buffer)
                        if state:
                            state.is_candidate_speaking.set()
                        silence_frames_counter = 0
                else:
                    speech_start_candidate_frames = 0
                    rms_start_candidate_frames = 0
            else:
                # --- Adaptive Speech CONTINUATION Gate (RMS primary) ---
                # Silence counter climbs when BOTH VAD and RMS confirm silence.
                # Either VAD prob > 0.20 OR rms above continue gate resets the counter.
                if speech_prob > 0.20 or rms > _continue_rms_gate:
                    silence_frames_counter = 0
                else:
                    silence_frames_counter += 1

            if ui_callback:
                ui_callback({
                    "type": "audio_level",
                    "rms": float(rms),
                    "vad_prob": float(speech_prob),
                    "state": (
                        "Hearing you..." if has_spoken
                        else f"Waiting for speech...  VAD: {speech_prob:.2f}  RMS: {rms:.4f}"
                    )
                })

            # Accumulate clean (noise-suppressed) audio for Whisper while speech is active
            if has_spoken:
                audio_buffer.append(vad_frame.copy())
                total_frames_counter += 1


                # Warning near post-speech hard timeout (around 50s)
                if total_frames_counter == 1562 and ui_callback:
                    ui_callback({
                        "type": "audio_level",
                        "rms": 0.0,
                        "vad_prob": 0.0,
                        "state": "⚠️ Approaching time limit (10s remaining)..."
                    })
            else:
                pre_speech_buffer.append(vad_frame.copy())

                # Pre-speech idle timeout: if no speech is detected for MAX_IDLE_WAIT_SEC,
                # break and return empty string — prevents infinite hang when user says nothing.
                idle_elapsed = time.monotonic() - _listen_start_time
                if idle_elapsed >= MAX_IDLE_WAIT_SEC:
                    print(
                        f"[Listener] No speech detected in {MAX_IDLE_WAIT_SEC:.0f}s idle window. "
                        f"Returning empty transcript.",
                        flush=True
                    )
                    if ui_callback:
                        ui_callback({
                            "type": "audio_level",
                            "rms": 0.0,
                            "vad_prob": 0.0,
                            "state": "⏱️ No response detected — moving on..."
                        })
                    break


            # Break loop when silence threshold is reached after speech (and minimum speech duration met), or hard timeout
            if has_spoken:
                can_endpoint = total_frames_counter >= MIN_SPEECH_FRAMES
                if (silence_frames_counter >= max_silence_frames and can_endpoint) or total_frames_counter > MAX_RECORDING_FRAMES:
                    # Tier 1 + Tier 2 Hybrid Thought Completion Check (enabled for desktop or explicit flag)
                    should_check_thought = (
                        ws_audio_queue is None or getattr(state, "enable_thought_classifier", False)
                    )
                    if should_check_thought and not has_extended_silence and total_frames_counter <= MAX_RECORDING_FRAMES:
                        _cached_interim_transcript = _transcribe_audio_buffer(audio_buffer)
                        status = check_thought_completion(_cached_interim_transcript)
                        if status == "INCOMPLETE":
                            has_extended_silence = True
                            if state:
                                state.pause_tolerance_ms = 2000
                            max_silence_frames = max(8, (state.pause_tolerance_ms if state else 2000) // 32)
                            print(
                                f"⏳ Candidate is thinking... extending wait time to {max_silence_frames * 32}ms "
                                f"(interim transcript: '{_cached_interim_transcript}')",
                                flush=True
                            )
                            continue

                    # ── Speaker Verification Gate ──
                    # Runs ONCE per completed utterance (NOT per VAD frame).
                    # Rejects foreign voices BEFORE sending audio to Whisper STT.
                    if speaker_verifier is not None and audio_buffer:
                        sv_audio = np.concatenate(audio_buffer)
                        sv_duration = len(sv_audio) / 16000

                        if speaker_verifier.is_enrolled:
                            is_candidate, sv_score = speaker_verifier.verify(sv_audio)
                            if not is_candidate and sv_score < 0.15:
                                print(
                                    f"[SV] ❌ Rejected foreign voice "
                                    f"(score={sv_score:.3f} < {speaker_verifier.ACCEPT_THRESHOLD}). "
                                    f"Ignoring {sv_duration:.1f}s audio.",
                                    flush=True,
                                )
                                if ui_callback:
                                    ui_callback({
                                        "type": "audio_level",
                                        "rms": 0.0,
                                        "vad_prob": 0.0,
                                        "state": f"⚠️ Voice didn't match profile (score: {sv_score:.2f}) - please speak clearly"
                                    })
                                # Reset state and continue listening — do NOT transcribe
                                audio_buffer.clear()
                                has_spoken = False
                                has_extended_silence = False
                                speech_start_candidate_frames = 0
                                silence_frames_counter = 0
                                total_frames_counter = 0
                                _cached_interim_transcript = None
                                continue  # Back to top of while loop
                            else:
                                print(f"[SV] ✅ Candidate voice confirmed (score={sv_score:.3f})", flush=True)
                        else:
                            # Auto-enroll from first utterance >= 1.5 seconds (ICEBREAKER turn)
                            if sv_duration >= 1.5:
                                speaker_verifier.enroll(sv_audio)
                                print(
                                    f"[SV] 🎤 Auto-enrolled candidate voice from "
                                    f"{sv_duration:.1f}s first utterance.",
                                    flush=True,
                                )

                    print(f"[Silence Detected ({silence_frames_counter * 32}ms). Processing speech...]")
                    if ui_callback:
                        ui_callback({
                            "type": "audio_level",
                            "rms": 0.0,
                            "vad_prob": 0.0,
                            "state": "Processing transcription..."
                        })
                    Benchmark.start("ttfa")
                    Benchmark.start("stt")
                    break


    finally:
        stop_producer.set()
        if state:
            state.is_candidate_speaking.clear()
            state.pause_tolerance_ms = 800  # Reset back to default baseline (800ms)
        if ui_callback:
            ui_callback({
                "type": "audio_level",
                "rms": 0.0,
                "vad_prob": 0.0,
                "state": "Mic: Standby"
            })
        # Clean up audio hardware streams immediately
        if stream:
            stream.stop()
            stream.close()

    if not audio_buffer:
        return ""

    # Combine accumulated (DC-filtered via streaming IIR) frames
    audio_array = np.concatenate(audio_buffer)

    # Apply noise reduction ONCE on the full contiguous buffer (avoids 31Hz
    # windowing artifacts caused by per-chunk Hann window tapering).
    # Uses the noise profile captured during calibration for Wiener spectral gating.
    if noise_reducer is not None:
        try:
            import noisereduce as nr
            audio_array = nr.reduce_noise(
                y=audio_array,
                sr=16000,
                y_noise=noise_reducer.noise_clip,
                stationary=True,
                prop_decrease=0.85,
            ).astype(np.float32)
        except Exception:
            pass

    # Safety IIR high-pass filter (redundant with streaming DC blocker, but harmless).
    # y[n] = alpha * (y[n-1] + x[n] - x[n-1]), alpha=0.995 -> ~5Hz cutoff at 16kHz
    alpha = 0.995
    filtered = np.empty_like(audio_array)
    filtered[0] = 0.0
    for i in range(1, len(audio_array)):
        filtered[i] = alpha * (filtered[i-1] + audio_array[i] - audio_array[i-1])
    audio_array = filtered

    final_gain = 1.0
    utterance_peak = float(np.max(np.abs(audio_array)))
    if utterance_peak > 0.0001:
        final_gain = min(0.9 / utterance_peak, 15.0)  # 15x cap for utterance-level normalisation
        audio_array = audio_array * final_gain
    print(f"[STT] Sending {len(audio_array)/16000:.1f}s audio to Whisper (peak={utterance_peak:.4f}, gain={final_gain:.1f}x)", flush=True)

    if _cached_interim_transcript is not None:
        transcript_text = _cached_interim_transcript
    else:
        # Generate transcription using Faster-Whisper.
        segments, _ = whisper_model.transcribe(
            audio_array,
            language="en",
            initial_prompt=whisper_prompt,
            beam_size=1,
            best_of=1,
            temperature=0.0,
            condition_on_previous_text=False,
            no_speech_threshold=0.6,
            hallucination_silence_threshold=2.0,
            vad_filter=False,
            compression_ratio_threshold=2.4,
        )
        transcript_text = "".join([segment.text for segment in segments]).strip()

    stt_ms = Benchmark.end("stt")
    Benchmark.last_stt_ms = stt_ms

    if not transcript_text:
        return ""

    if not is_valid_transcript(transcript_text):
        print(f"[STT] Rejected likely hallucination: '{transcript_text}'", flush=True)
        return ""

    return transcript_text


def run_timed_test(rounds: int = 3, record_seconds: int = 8):
    """
    Standalone timed test for the STT listener.
    Uses sounddevice for recording, then runs Silero VAD + Whisper for transcription.
    """
    
    # Force UTF-8 output so the terminal does not crash on Windows cp1252
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

    try:
        import sounddevice as sd
    except ImportError:
        print("  [ERROR] sounddevice not installed. Run: pip install sounddevice", flush=True)
        return

    RATE  = 16000
    CHUNK = 512   # VAD frame size (32ms at 16kHz)

    print("\n  [MIC CHECK] Stay silent for 1 second...", flush=True)
    warmup = sd.rec(RATE, samplerate=RATE, channels=1, dtype="float32")
    sd.wait()
    rms_silence = float(np.sqrt(np.mean(warmup ** 2)))
    print(f"  [SILENCE RMS] {rms_silence:.5f}  (expected < 0.01)", flush=True)
    if rms_silence > 0.05:
        print("  [WARNING] Background noise is high - quieter space recommended.", flush=True)
    else:
        print("  [OK] Mic check passed.\n", flush=True)

    print("=" * 52, flush=True)
    print("   NETRAN AI -- STT LISTENER STANDALONE TEST", flush=True)
    print("=" * 52, flush=True)

    for round_num in range(1, rounds + 1):
        print(f"\n-- Round {round_num}/{rounds} " + "-" * 32, flush=True)

        for t in range(3, 0, -1):
            print(f"  [MIC] Get ready... {t}", end="\r", flush=True)
            time.sleep(1)
        print(f"  [REC] SPEAK NOW! Recording for {record_seconds}s...          ", flush=True)

        raw_recording = sd.rec(
            int(record_seconds * RATE),
            samplerate=RATE,
            channels=1,
            dtype="float32"
        )
        for tick in range(record_seconds):
            remaining = record_seconds - tick
            print(f"  [>>>] {tick+1}s / {record_seconds}s  Recording... ({remaining}s left) ", end="\r", flush=True)
            time.sleep(1)
        sd.wait()
        print("  [DONE] Recording complete. Running VAD + Whisper...              ", flush=True)

        audio_flat = raw_recording.flatten()
        audio_flat = audio_flat - np.mean(audio_flat)

        peak = float(np.max(np.abs(audio_flat)))
        if peak > 0.0005:
            target_peak = 0.9
            dynamic_gain = target_peak / peak
            dynamic_gain = min(dynamic_gain, 20.0)
            audio_flat = audio_flat * dynamic_gain
            print(f"  [GAIN] Auto-boosted volume by {dynamic_gain:.1f}x (Peak was {peak:.4f})", flush=True)

        rms_speech = float(np.sqrt(np.mean(audio_flat ** 2)))
        print(f"  [RMS] Audio level after boost: {rms_speech:.5f}", flush=True)

        if rms_speech < 0.0005:
            print("  [ERROR] Audio is near-silence even after gain boost. Check mic permissions.", flush=True)
            continue

        vad_state_arr = np.zeros((2, 1, 128), dtype=np.float32)
        sr_scalar = np.array(RATE, dtype=np.int64)

        speech_start_idx = None
        speech_end_idx   = None
        n_frames         = len(audio_flat) // CHUNK
        max_prob         = 0.0

        for i in range(n_frames):
            frame    = audio_flat[i * CHUNK : (i + 1) * CHUNK]
            audio_in = np.expand_dims(frame, 0)
            ort_out  = vad_session.run(None, {"input": audio_in, "state": vad_state_arr, "sr": sr_scalar})
            vad_state_arr    = ort_out[1]
            prob     = float(ort_out[0][0, 0])
            max_prob = max(max_prob, prob)

            if prob > 0.3 and speech_start_idx is None:
                speech_start_idx = i * CHUNK
            if prob > 0.1 and speech_start_idx is not None:
                speech_end_idx = (i + 1) * CHUNK

        print(f"  [VAD] Highest probability score: {max_prob:.4f}", flush=True)

        if speech_start_idx is None:
            print("  [VAD] No speech region found. Transcribing full recording.", flush=True)
            audio_to_transcribe = audio_flat
        else:
            pad   = int(0.2 * RATE)
            start = max(0, speech_start_idx - pad)
            end   = min(len(audio_flat), speech_end_idx + pad)
            audio_to_transcribe = audio_flat[start:end]
            print(f"  [VAD] Speech found: {(end-start)/RATE:.1f}s trimmed and ready.", flush=True)

        Benchmark.start("stt")
        segments, _ = whisper_model.transcribe(
            audio_to_transcribe,
            language="en",
            initial_prompt="User is speaking in English in a clear conversational tone.",
            beam_size=1,
            best_of=1,
            temperature=0.0,
            condition_on_previous_text=False,
            no_speech_threshold=0.6,
            hallucination_silence_threshold=2.0,
            vad_filter=False,
            compression_ratio_threshold=2.4,
        )
        transcript = "".join(s.text for s in segments).strip()
        stt_ms     = Benchmark.end("stt")

        print(f"\n  [TRANSCRIPT] \"{transcript}\"", flush=True)
        print(f"  [STT LATENCY] {stt_ms:.0f} ms", flush=True)
        if not transcript or len(transcript.split()) < 3:
            print("  [WARNING] Very short result - try speaking closer to the mic.", flush=True)
        print(flush=True)


if __name__ == "__main__":
    run_timed_test(rounds=3, record_seconds=8)


class ContinuousMicWriter:
    """
    Background worker thread that continuously writes incoming 16kHz float32 PCM mic frames
    to a 16kHz 16-bit Mono WAV file asynchronously using a queue.
    """
    def __init__(self, filepath: str, sample_rate: int = 16000):
        self.filepath = filepath
        self.sample_rate = sample_rate
        self.queue = queue.Queue()
        self.is_running = False
        self.thread = None
        self._wav_file = None

    def start(self):
        """Starts the background recording writer thread."""
        if self.is_running:
            return
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
        self.is_running = True
        self.thread = threading.Thread(target=self._writer_loop, daemon=True)
        self.thread.start()
        atexit.register(self.stop)
        print(f"[ContinuousMicWriter] Recording started -> {self.filepath}", flush=True)

    def write_frame(self, frame: np.ndarray):
        """Enqueues raw float32 frame for non-blocking disk writing."""
        if self.is_running:
            self.queue.put(frame.copy())

    def _writer_loop(self):
        """Worker thread loop consuming frames from the queue."""
        try:
            self._wav_file = wave.open(self.filepath, 'wb')
            self._wav_file.setnchannels(1)
            self._wav_file.setsampwidth(2)  # 16-bit PCM = 2 bytes
            self._wav_file.setframerate(self.sample_rate)

            while self.is_running or not self.queue.empty():
                try:
                    frame = self.queue.get(timeout=0.1)
                except queue.Empty:
                    continue

                if frame is None:  # Sentinel object to terminate
                    break

                # Convert float32 [-1.0, 1.0] to int16 [-32768, 32767]
                pcm16 = (np.clip(frame, -1.0, 1.0) * 32767).astype(np.int16)
                self._wav_file.writeframes(pcm16.tobytes())
                self.queue.task_done()
        except Exception as e:
            print(f"[ContinuousMicWriter Error] {e}", flush=True)
        finally:
            if self._wav_file:
                try:
                    self._wav_file.close()
                except Exception:
                    pass
                self._wav_file = None

    def stop(self):
        """Stops the writer thread and cleanly closes the WAV file header."""
        if not self.is_running:
            return
        self.is_running = False
        self.queue.put(None)  # Send sentinel
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2.0)
        print(f"[ContinuousMicWriter] Recording saved and closed -> {self.filepath}", flush=True)


class BargeInWatcher:
    """
    Full-Duplex Barge-In Detection — Background Daemon Thread.

    ROOT CAUSE OF ORIGINAL FAILURE:
    listen_and_transcribe() was called AFTER speak_text() returned, so the
    microphone was NEVER open while Eva was playing audio. The barge-in code
    inside listen_and_transcribe() could never fire because the function
    wasn't running.

    THIS FIX:
    BargeInWatcher opens its OWN independent sounddevice InputStream in a
    background daemon thread and runs Silero VAD concurrently with TTS
    playback. front.py starts this watcher BEFORE Eva begins speaking and
    stops it after the audio queue drains (or after barge-in fires).

    When speech_prob > 0.65:
      1. Sets state.interrupt_event  (aborts LLM generation in brain.py)
      2. Calls on_barge_in callback  (calls force_stop_all → hardware flush)
      3. Clears is_agent_speaking    (signals pipeline that Eva is done)
      4. Exits the watcher loop      (mic stream closed immediately)

    listen_and_transcribe() then starts fresh and captures whatever the
    candidate continues to say after the barge-in.

    Usage in front.py:
        watcher = BargeInWatcher(state, on_barge_in=force_stop_all)
        watcher.start()
        try:
            # ... Eva speaks / LLM streams ...
            # ... audio queue drain poll ...
        finally:
            watcher.stop()
    """

    # VAD probability threshold for barge-in trigger.
    # 0.50 (was 0.65) — detects quiet/normal conversational voice without requiring shouting.
    VAD_THRESHOLD = 0.50

    def __init__(self, state: SessionState, on_barge_in=None):
        self.state = state
        self.on_barge_in = on_barge_in
        self._stop_event = threading.Event()
        self._thread = None
        self.triggered = False

    def start(self):
        """Starts the background VAD monitoring thread."""
        self._stop_event.clear()
        self.triggered = False
        self._thread = threading.Thread(
            target=self._watch_loop,
            name="BargeInWatcher",
            daemon=True
        )
        self._thread.start()
        print("[BargeInWatcher] Barge-in monitor started.", flush=True)

    def stop(self):
        """
        Signals the watcher to stop and waits briefly for mic stream cleanup.
        Safe to call even if watcher already exited due to barge-in.
        """
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=0.08)

    def _watch_loop(self):
        """
        Background thread: opens an independent mic stream and runs Silero VAD
        on every 32ms frame (512 samples at 16kHz) while the agent is speaking.

        Uses its own local VAD state so there is NO shared state with the
        listen_and_transcribe() VAD session — they are never concurrent.
        """
        import time as _time

        RATE = 16000
        CHUNK = 512  # 32ms frame — Silero VAD v3 requires exactly 512 samples

        # Local VAD state — isolated from listen_and_transcribe's VAD state
        vad_state_local = np.zeros((2, 1, 128), dtype=np.float32)
        sr_scalar_local = np.array(RATE, dtype=np.int64)

        # --- Robust BargeInWatcher stream init (native rate, Python-side resampling) ---
        device_info = sd.query_devices(MIC_DEVICE) if MIC_DEVICE is not None else sd.query_devices(sd.default.device[0])
        native_rate = int(device_info.get("default_samplerate", 16000))
        if native_rate <= 0:
            native_rate = 16000
        CHUNK_NATIVE = int(CHUNK * native_rate / RATE)

        # Open an independent sounddevice input stream for concurrent mic monitoring
        # Robust microphone initialization with retries (fixes race condition with main listener)
        stream = None
        for attempt in range(3):
            try:
                # Attempt Method B: native OS resampling (works beautifully on MME/DirectSound)
                stream = sd.InputStream(
                    samplerate=RATE,
                    channels=1,
                    dtype="float32",
                    blocksize=CHUNK,
                    device=MIC_DEVICE,
                )
                native_rate = RATE
                CHUNK_NATIVE = CHUNK
                break
            except sd.PortAudioError:
                try:
                    # Fallback Method A: WASAPI strictly requires native rate
                    stream = sd.InputStream(
                        samplerate=native_rate,
                        channels=1,
                        dtype="float32",
                        blocksize=CHUNK_NATIVE,
                        device=MIC_DEVICE,
                    )
                    break
                except Exception as exc:
                    if attempt < 2:
                        print(f"[BargeInWatcher] Mic locked, retrying... ({exc})", flush=True)
                        _time.sleep(0.3)
                    else:
                        print(f"[BargeInWatcher] Could not open mic stream after retries: {exc}", flush=True)
                        return
            except Exception as exc:
                if attempt < 2:
                    print(f"[BargeInWatcher] Mic locked, retrying... ({exc})", flush=True)
                    _time.sleep(0.3)
                else:
                    print(f"[BargeInWatcher] Could not open mic stream after retries: {exc}", flush=True)
                    return
        stream.start()

        try:
            while not self._stop_event.is_set() and not self.state.should_stop.is_set():
                # Read one 32ms frame from the microphone
                try:
                    raw_data, _ = stream.read(CHUNK_NATIVE)
                except Exception:
                    break

                frame = raw_data.flatten()

                if native_rate == 48000 and RATE == 16000:
                    frame = frame.reshape(-1, 3).mean(axis=1).astype(np.float32)
                elif native_rate != RATE:
                    pcm16 = (frame * 32767.0).astype(np.int16)
                    resampled_pcm, _ = audioop.ratecv(pcm16.tobytes(), 2, 1, native_rate, RATE, None)
                    frame = np.frombuffer(resampled_pcm, dtype=np.int16).astype(np.float32) / 32767.0

                if len(frame) < CHUNK:
                    frame = np.pad(frame, (0, CHUNK - len(frame)), mode='edge')

                # DC offset removal removed to comply with Rule 11 (preserve Silero temporal continuity)
                peak = float(np.max(np.abs(frame)))

                # Feed un-gained frame to Silero VAD to preserve RNN continuity
                audio_input = np.expand_dims(frame, axis=0)  # shape [1, 512]
                ort_inputs = {
                    "input": audio_input,
                    "state": vad_state_local,
                    "sr": sr_scalar_local,
                }
                try:
                    ort_outputs = vad_session.run(None, ort_inputs)
                except Exception:
                    continue
                vad_state_local = ort_outputs[1]
                speech_prob = float(ort_outputs[0][0, 0])

                # Barge-in detected: speech above threshold
                rms = np.sqrt(np.mean(frame ** 2))
                # Avoid false barge-in triggers on static/echo by requiring a minimum VAD speech probability
                if (speech_prob > 0.25 and rms > 0.005) or speech_prob > 0.40:
                    now = _time.monotonic()
                    cooldown = getattr(self.state, "interrupt_cooldown_sec", 0.3)
                    last_t = getattr(self.state, "last_interrupt_time", 0.0)

                    if now - last_t > cooldown:
                        print(
                            f"\n⚡ [BargeInWatcher] BARGE-IN detected (prob={speech_prob:.2f})! "
                            f"Interrupting Eva immediately.",
                            flush=True
                        )
                        # 1. Set global interrupt signal — brain.py token loop and
                        #    speaker._play_loop sub-chunk loop both check this
                        self.state.interrupt_event.set()
                        self.state.last_interrupt_time = now

                        # 2. Clear agent-speaking flag
                        self.state.is_agent_speaking.clear()

                        # 3. Fire hardware-flush callback (force_stop_all)
                        self.triggered = True
                        if self.on_barge_in:
                            try:
                                self.on_barge_in()
                            except Exception as cb_exc:
                                print(f"[BargeInWatcher] Callback error: {cb_exc}", flush=True)

                        # 4. Exit watcher — interrupt is handled
                        break

        finally:
            try:
                stream.stop()
                stream.close()
            except Exception:
                pass
            print(
                f"[BargeInWatcher] Monitor stopped. "
                f"{'Barge-in triggered.' if self.triggered else 'No barge-in.'}",
                flush=True
            )