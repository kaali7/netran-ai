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
    from .prompts import WHISPER_INITIAL_PROMPT
    from .session_state import SessionState
except ImportError:
    try:
        from model.voice_to_voice_model.model.benchmark import Benchmark
        from model.voice_to_voice_model.model.config import (
            WHISPER_MODEL,
            MIC_DEVICE_INDEX,
            auto_select_mic_device,
        )
        from model.voice_to_voice_model.model.prompts import WHISPER_INITIAL_PROMPT
        from model.voice_to_voice_model.model.session_state import SessionState
    except ImportError:
        from benchmark import Benchmark
        from config import WHISPER_MODEL, MIC_DEVICE_INDEX, auto_select_mic_device
        from prompts import WHISPER_INITIAL_PROMPT
        from session_state import SessionState

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


def listen_and_transcribe(ui_callback=None, mic_writer=None, state: SessionState = None):
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
    except sd.PortAudioError:
        # Fallback Method A: WASAPI strictly requires native rate, so we do manual decimation
        stream = sd.InputStream(
            samplerate=native_rate,
            channels=CHANNELS,
            dtype='float32',
            blocksize=CHUNK_NATIVE,
            device=MIC_DEVICE,
        )
    stream.start()

    is_ptt = bool(state and getattr(state, "input_mode", "VAD") == "PTT")
    if is_ptt:
        print("\n[Push-To-Talk Active] Hold PTT button or Spacebar to speak...", flush=True)
    else:
        print("\n[Listening...] Speak into your microphone now.", flush=True)

    audio_buffer = []
    pre_speech_buffer = collections.deque(maxlen=15)  # 480ms ring buffer
    has_spoken = False
    speech_start_candidate_frames = 0
    silence_frames_counter = 0
    _diag_frame_counter = 0   # Periodic VAD diagnostic counter
    
    # Defaults if state isn't provided (for standalone tests) — 800ms default pause tolerance (25 frames * 32ms)
    max_silence_frames = 25 if state is None else max(8, state.pause_tolerance_ms // 32)
    MIN_SPEECH_FRAMES = 15   # Must accumulate at least 15 frames (~480ms) before endpointing is allowed
    total_frames_counter = 0 
    MAX_RECORDING_FRAMES = 1875  # 60s hard timeout (1875 * 32ms = 60,000ms)

    if state:
        state.is_candidate_speaking.clear()
        state.force_speech_done.clear()

    # Initialize VAD state tensors (Silero VAD v3 ONNX: only state is required, no context)
    vad_state = np.zeros((2, 1, 128), dtype=np.float32)
    sr_scalar = np.array(RATE, dtype=np.int64)

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

            # 1. Read raw PCM data from the microphone
            try:
                raw_data, overflowed = stream.read(CHUNK_NATIVE)
                original_frame = raw_data.flatten()
            except Exception:
                continue

            # Anti-aliased integer decimation for 48kHz -> 16kHz
            if native_rate == 48000 and RATE == 16000:
                original_frame = original_frame.reshape(-1, 3).mean(axis=1).astype(np.float32)
            elif native_rate != RATE:
                # Basic fallback
                pcm16 = (original_frame * 32767.0).astype(np.int16)
                resampled_pcm, _ = audioop.ratecv(pcm16.tobytes(), 2, 1, native_rate, RATE, None)
                original_frame = np.frombuffer(resampled_pcm, dtype=np.int16).astype(np.float32) / 32767.0

            # 2. Process the raw frame for VAD
            vad_frame = original_frame.copy()
            if len(vad_frame) < CHUNK:
                vad_frame = np.pad(vad_frame, (0, CHUNK - len(vad_frame)), mode='edge')

            frame_peak = float(np.max(np.abs(vad_frame)))

            # Apply a constant volume boost for the output recording (Whisper + WAV)
            # DO NOT apply dynamic per-chunk auto-gain before Silero VAD, as it destroys RNN temporal continuity!
            proc_frame = vad_frame * 3.0
            proc_frame = np.clip(proc_frame, -1.0, 1.0)

            if mic_writer:
                mic_writer.write_frame(proc_frame)

            # Prepare VAD inputs: input shape must be [1, 512]. Feed clean, un-gained audio to VAD.
            audio_input = np.expand_dims(vad_frame, axis=0)

            # 3. Run Silero VAD v3 — 3 inputs: input, state, sr
            ort_inputs = {
                "input": audio_input,
                "state": vad_state,
                "sr": sr_scalar,
            }
            # Outputs: [output_prob [batch,1], stateN [2,batch,128]]
            ort_outputs = vad_session.run(None, ort_inputs)
            out   = ort_outputs[0]   # shape [1, 1]
            vad_state = ort_outputs[1]   # updated hidden state
            speech_prob = out[0, 0]

            # 3b. Full-Duplex Barge-In Detection
            # Calculate RMS early to use it as a fallback for broken VAD microphones.
            rms = np.sqrt(np.mean(proc_frame ** 2))
            
            # VAD runs continuously even during agent speech. When speech_prob > 0.65 OR rms >= 0.015,
            # we fire the interrupt (with cooldown) and FALL THROUGH to accumulate the
            # barge-in audio so the candidate's interrupted speech is captured for STT.
            if state and state.is_agent_speaking.is_set():
                if speech_prob > 0.65 or rms >= 0.015:
                    now = time.monotonic()
                    cooldown = getattr(state, 'interrupt_cooldown_sec', 0.3)
                    last_t = getattr(state, 'last_interrupt_time', 0.0)
                    if now - last_t > cooldown:
                        print("⚡ [Barge-In] Candidate interrupted Eva! Halting audio output.", flush=True)
                        # 1. Set global interrupt signal (checked by brain.py & speaker.py)
                        state.interrupt_event.set()
                        state.last_interrupt_time = now
                        # 2. Hard-flush hardware audio buffer + drain Python queue
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
                        # 3. Fall through — do NOT continue; let audio_buffer accumulate
                        #    the barge-in speech so STT captures what the candidate said.
                else:
                    # Low-probability frame during agent speech: suppress mic accumulation
                    silence_frames_counter = 0
                    continue

            # 4. Speech Start/End Decision Logic
            _diag_frame_counter += 1

            # Periodic VAD diagnostic: print live VAD prob + RMS every ~2s (60 frames * 32ms)
            # This helps calibrate thresholds when speech is not being detected.
            if _diag_frame_counter % 60 == 0 and not has_spoken:
                print(
                    f"[VAD Diag] prob={speech_prob:.3f}  rms={rms:.4f}  "
                    f"(need: prob>=0.20+rms>=0.008 OR prob>=0.35 OR rms>=0.015 to trigger)",
                    flush=True
                )

            if not has_spoken:
                # Lowered thresholds for laptop/built-in mic compatibility:
                # Combined gate: VAD prob >= 0.20 AND RMS >= 0.008  (was 0.35 + 0.015)
                # Strong gate:   VAD prob >= 0.35                   (was 0.50)
                # Rationale: the BargeInWatcher threshold is already at 0.50 for barge-in;
                # for initial speech start we use softer criteria since there's no
                # concurrent agent audio to filter out. The RMS floor of 0.008 is still
                # sufficient to reject pure background static near the 0.0005 noise gate.
                # FALLBACK: If VAD fails due to corrupted audio but RMS is consistently high (>= 0.015).
                if (speech_prob >= 0.20 and rms >= 0.008) or speech_prob >= 0.35 or rms >= 0.015:
                    speech_start_candidate_frames += 1
                    if speech_start_candidate_frames >= 2:   # 2 frames = ~64ms debounce
                        print(f"[Speech Detected!] (VAD prob={speech_prob:.2f}, RMS={rms:.4f})", flush=True)
                        has_spoken = True
                        audio_buffer.extend(pre_speech_buffer)
                        if state:
                            state.is_candidate_speaking.set()
                        silence_frames_counter = 0
                else:
                    speech_start_candidate_frames = 0
            else:
                # Forgiving speech continuation threshold
                if speech_prob > 0.15 or rms > 0.008:
                    silence_frames_counter = 0
                else:
                    silence_frames_counter += 1

            if ui_callback:
                display_rms = np.sqrt(np.mean(proc_frame ** 2))
                ui_callback({
                    "type": "audio_level",
                    "rms": float(display_rms),
                    "vad_prob": float(speech_prob),
                    "state": (
                        "Hearing you..." if has_spoken
                        else f"Waiting for speech...  VAD: {speech_prob:.2f}  RMS: {rms:.4f}"
                    )
                })

            # Accumulate clean, un-clipped audio while speech is active for Whisper
            if has_spoken:
                audio_buffer.append(vad_frame.copy())
                total_frames_counter += 1
            else:
                pre_speech_buffer.append(vad_frame.copy())
                
                # Warning near timeout (around 50s)
                if total_frames_counter == 1562 and ui_callback:
                    ui_callback({
                        "type": "audio_level", 
                        "rms": 0.0, 
                        "vad_prob": 0.0,
                        "state": "⚠️ Approaching time limit (10s remaining)..."
                    })

            # Break loop when silence threshold is reached after speech (and minimum speech duration met), or hard timeout
            if has_spoken:
                can_endpoint = total_frames_counter >= MIN_SPEECH_FRAMES
                if (silence_frames_counter >= max_silence_frames and can_endpoint) or total_frames_counter > MAX_RECORDING_FRAMES:
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
        if state:
            state.is_candidate_speaking.clear()
        # Clean up audio hardware streams immediately
        stream.stop()
        stream.close()

    if not audio_buffer:
        return ""

    # Combine accumulated (already DC-offset + auto-gain processed) frames
    audio_array = np.concatenate(audio_buffer)

    # IIR high-pass filter to remove per-chunk DC drift without creating
    # step discontinuities at chunk boundaries.
    # y[n] = alpha * (y[n-1] + x[n] - x[n-1]), alpha=0.995 -> ~5Hz cutoff at 16kHz
    alpha = 0.995
    filtered = np.empty_like(audio_array)
    filtered[0] = 0.0
    for i in range(1, len(audio_array)):
        filtered[i] = alpha * (filtered[i-1] + audio_array[i] - audio_array[i-1])
    audio_array = filtered

    utterance_peak = float(np.max(np.abs(audio_array)))
    if utterance_peak > 0.0001:
        final_gain = min(0.9 / utterance_peak, 15.0)  # 15x cap for utterance-level normalisation
        audio_array = audio_array * final_gain
    print(f"[STT] Sending {len(audio_array)/16000:.1f}s audio to Whisper (peak={utterance_peak:.4f}, gain={final_gain:.1f}x)", flush=True)

    # Generate transcription using Faster-Whisper.
    # vad_filter=False: Whisper's built-in VAD is deliberately disabled because it
    # re-applies a silence gate that strips out quiet/distant speech that our Silero
    # VAD already approved and our auto-gain already amplified. Letting Whisper
    # re-filter the audio causes quiet voices to produce empty transcripts.
    segments, _ = whisper_model.transcribe(
        audio_array,
        language="en",
        initial_prompt=WHISPER_INITIAL_PROMPT,
        beam_size=1,
        best_of=1,
        temperature=0.0,
        condition_on_previous_text=False,      # Prevents infinite phrase loops & repeated hallucinations
        no_speech_threshold=0.6,               # Drops non-speech static segments
        hallucination_silence_threshold=2.0,   # Drops long hallucinated silent segments
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
    import time
    
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
            initial_prompt=WHISPER_INITIAL_PROMPT,
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
            self._thread.join(timeout=0.8)

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

        device_info = sd.query_devices(MIC_DEVICE) if MIC_DEVICE is not None else sd.query_devices(sd.default.device[0])
        native_rate = int(device_info.get("default_samplerate", 16000))
        if native_rate <= 0:
            native_rate = 16000
        CHUNK_NATIVE = int(CHUNK * native_rate / RATE)

        # Open an independent sounddevice input stream for concurrent mic monitoring
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
            stream.start()
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
                stream.start()
            except Exception as exc:
                print(f"[BargeInWatcher] Could not open mic stream: {exc}", flush=True)
                return
        except Exception as exc:
            print(f"[BargeInWatcher] Could not open mic stream: {exc}", flush=True)
            return

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

                # DC offset removal
                frame = frame - np.mean(frame)
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
                if speech_prob > self.VAD_THRESHOLD:
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