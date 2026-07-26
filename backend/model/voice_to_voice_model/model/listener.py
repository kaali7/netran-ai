"""
Netran AI — Stage 3: Live Voice-to-Voice Loop
Module: listener.py
Description: Audio capture engine utilizing sounddevice, Silero VAD ONNX inference,
             dynamic peak auto-gain normalization, Faster-Whisper int8 STT,
             and asynchronous continuous PCM mic WAV streaming.
"""

import wave
import queue
import threading
import atexit
import numpy as np
import sounddevice as sd
import onnxruntime as ort
import os
import importlib
from faster_whisper import WhisperModel
try:
    from .benchmark import Benchmark
    from .prompts import WHISPER_INITIAL_PROMPT
except ImportError:
    try:
        from model.voice_to_voice_model.model.benchmark import Benchmark
        from model.voice_to_voice_model.model.prompts import WHISPER_INITIAL_PROMPT
    except ImportError:
        from benchmark import Benchmark
        from prompts import WHISPER_INITIAL_PROMPT

# Global setup
VAD_MODEL_PATH = os.path.join(os.path.dirname(__file__), "silero_vad.onnx")

import sys

print("Loading Silero VAD model...", flush=True)
# Disable logging/profiling in onnxruntime to keep output clean
ort_opts = ort.SessionOptions()
ort_opts.log_severity_level = 3
vad_session = ort.InferenceSession(VAD_MODEL_PATH, ort_opts)

# 'small' model is now fully cached locally — loads fast from disk, no download needed.
print("Loading Faster-Whisper model (small)...", flush=True)
whisper_model = WhisperModel("small", device="cpu", compute_type="int8", cpu_threads=4)
print("Models loaded successfully!", flush=True)

# Global manual speech endpointing flag
FORCE_SPEECH_DONE = False

def trigger_speech_done():
    """Triggers immediate speech endpointing to skip waiting for silence."""
    global FORCE_SPEECH_DONE
    FORCE_SPEECH_DONE = True

def listen_and_transcribe(ui_callback=None, mic_writer=None):
    """
    Opens the microphone, uses Silero VAD to detect speech start and end,
    respects the echo gate, transcribes the speech using Faster-Whisper,
    and optionally streams raw frames to continuous mic writer.
    """
    global FORCE_SPEECH_DONE
    FORCE_SPEECH_DONE = False

    # Audio hardware recording constraints
    CHANNELS = 1
    RATE = 16000     # 16kHz for VAD and Whisper
    CHUNK = 512      # Silero VAD v4 requires EXACTLY 512 samples at 16kHz
    assert CHUNK == 512, f"[VAD Guard] Silero VAD requires exactly 512 samples at 16kHz, got {CHUNK}"  # Fix Bug #4

    stream = sd.InputStream(
        samplerate=RATE,
        channels=CHANNELS,
        dtype='float32',
        blocksize=CHUNK
    )
    stream.start()

    print("\n[Listening...] Speak into your microphone now.", flush=True)

    audio_buffer = []
    has_spoken = False
    speech_start_candidate_frames = 0
    silence_frames_counter = 0
    max_silence_frames = 28  # 28 * 32ms = ~900ms (natural interview pause window)
    MIN_SPEECH_FRAMES = 15   # Must accumulate at least 15 frames (~480ms) before endpointing is allowed
    total_frames_counter = 0 # 12-second hard timeout for the recording

    # Initialize VAD state tensors (Silero VAD v3 ONNX: only state is required, no context)
    state = np.zeros((2, 1, 128), dtype=np.float32)
    sr_scalar = np.array(RATE, dtype=np.int64)

    try:
        while True:
            # Check manual force submit flag
            if FORCE_SPEECH_DONE:
                print("[Manual Done Speaking Triggered! Processing speech...]", flush=True)
                FORCE_SPEECH_DONE = False
                break

            # 1. Read raw PCM data from the microphone
            try:
                raw_data, overflowed = stream.read(CHUNK)
                original_frame = raw_data.flatten()
            except Exception:
                continue

            # 2. Check Echo Gate: If agent is speaking, drop input to prevent feedback
            try:
                _speaker_mod = importlib.import_module("speaker")
                _agent_speaking = getattr(_speaker_mod, "IS_AGENT_SPEAKING", False)
            except ImportError:
                _agent_speaking = False

            if _agent_speaking:
                # Discard frame and reset talking state to avoid triggering mid-speech
                silence_frames_counter = 0
                continue

            # 2b. Apply DC offset + auto-gain to the raw frame so both the
            #     mic_writer WAV file and the VAD/Whisper audio are boosted.
            #     (Confirmed fix: demo_raw.wav sounds clear because of this pipeline.)
            proc_frame = original_frame.copy()
            if len(proc_frame) < CHUNK:
                proc_frame = np.pad(proc_frame, (0, CHUNK - len(proc_frame)), 'constant')
            proc_frame = proc_frame - np.mean(proc_frame)  # DC offset removal
            frame_peak = float(np.max(np.abs(proc_frame)))
            if frame_peak > 0.0005:
                frame_gain = min(0.9 / frame_peak, 50.0)   # up to 50x, target 90% peak
                proc_frame = proc_frame * frame_gain

            if mic_writer:
                # Write the gain-boosted frame so recording.wav sounds clear
                mic_writer.write_frame(proc_frame)

            # Use the processed (DC + gain) frame for both VAD and accumulation
            audio_frame = proc_frame.copy()

            # Prepare VAD inputs: input shape must be [1, 512]
            audio_input = np.expand_dims(audio_frame, axis=0)

            # 3. Run Silero VAD v3 — 3 inputs: input, state, sr
            ort_inputs = {
                "input": audio_input,
                "state": state,
                "sr": sr_scalar,
            }
            # Outputs: [output_prob [batch,1], stateN [2,batch,128]]
            ort_outputs = vad_session.run(None, ort_inputs)
            out   = ort_outputs[0]   # shape [1, 1]
            state = ort_outputs[1]   # updated hidden state
            speech_prob = out[0, 0]

            # 4. Speech Start/End Decision Logic
            rms = np.sqrt(np.mean(audio_frame ** 2))
            
            if not has_spoken:
                # Debounce speech start: require 2 consecutive frames to avoid false triggers
                if (speech_prob > 0.10 and rms > 0.005) or (rms > 0.025):
                    speech_start_candidate_frames += 1
                    if speech_start_candidate_frames >= 2:
                        print(f"[Speech Detected!] (VAD prob={speech_prob:.2f}, RMS={rms:.4f})", flush=True)
                        has_spoken = True
                        silence_frames_counter = 0
                else:
                    speech_start_candidate_frames = 0
            else:
                # Forgiving speech continuation: reset silence counter if speech_prob > 0.05 OR rms > 0.008.
                # This ensures natural pauses (breathing, hesitation) don't cut off speech prematurely.
                if speech_prob > 0.05 or rms > 0.008:
                    silence_frames_counter = 0
                else:
                    silence_frames_counter += 1

            if ui_callback:
                rms = np.sqrt(np.mean(audio_frame ** 2))
                ui_callback({
                    "type": "audio_level",
                    "rms": float(rms),
                    "vad_prob": float(speech_prob),
                    "state": "Hearing you..." if has_spoken else "Waiting for speech..."
                })

            # Accumulate gain-boosted audio while speech is active
            if has_spoken:
                audio_buffer.append(proc_frame.copy())
                total_frames_counter += 1

            # Break loop when silence threshold (~900ms) is reached after speech (and minimum speech duration met), or hard timeout
            if has_spoken:
                can_endpoint = total_frames_counter >= MIN_SPEECH_FRAMES
                if (silence_frames_counter >= max_silence_frames and can_endpoint) or total_frames_counter > 375:
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
        # Clean up audio hardware streams immediately
        stream.stop()
        stream.close()

    if not audio_buffer:
        return ""

    # Combine accumulated (already DC-offset + auto-gain processed) frames
    audio_array = np.concatenate(audio_buffer)
    # Final whole-utterance gain pass: ensures consistent level for Whisper
    # (per-frame gain can vary; this normalizes the full utterance)
    audio_array = audio_array - np.mean(audio_array)  # re-center
    utterance_peak = float(np.max(np.abs(audio_array)))
    if utterance_peak > 0.0005:
        final_gain = min(0.9 / utterance_peak, 10.0)  # gentle 10x cap for utterance-level
        audio_array = audio_array * final_gain
    print(f"[STT] Sending {len(audio_array)/16000:.1f}s audio to Whisper (peak={utterance_peak:.4f})", flush=True)

    # Generate transcription using Faster-Whisper
    segments, _ = whisper_model.transcribe(
        audio_array,
        language="en",
        initial_prompt=WHISPER_INITIAL_PROMPT,
        beam_size=5,
        temperature=0.0,
        vad_filter=True,
        vad_parameters=dict(min_silence_duration_ms=300)
    )
    transcript_text = "".join([segment.text for segment in segments]).strip()

    stt_ms = Benchmark.end("stt")
    Benchmark.last_stt_ms = stt_ms

    # Filter out empty responses
    if not transcript_text:
        return ""

    return transcript_text

def run_timed_test(rounds: int = 3, record_seconds: int = 8):
    """
    Standalone timed test for the STT listener.
    Uses sounddevice (same as notebook - proven to work on Windows) for
    recording, then runs Silero VAD + Whisper for transcription.
    """
    import time

    # Force UTF-8 output so the terminal does not crash on Windows cp1252
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass  # Python < 3.7 fallback — safe to ignore

    try:
        import sounddevice as sd
    except ImportError:
        print("  [ERROR] sounddevice not installed. Run: pip install sounddevice", flush=True)
        return

    RATE  = 16000
    CHUNK = 512   # VAD frame size (32ms at 16kHz)

    # -- Mic warmup: confirm audio is being captured ----------------------
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
    print(f"  Rounds        : {rounds}", flush=True)
    print(f"  Record time   : {record_seconds}s per round (VAD trims silence)", flush=True)
    print(f"  Whisper model : small  |  VAD: Silero v3", flush=True)
    print("=" * 52, flush=True)

    for round_num in range(1, rounds + 1):
        print(f"\n-- Round {round_num}/{rounds} " + "-" * 32, flush=True)

        # 3-second countdown
        for t in range(3, 0, -1):
            print(f"  [MIC] Get ready... {t}", end="\r", flush=True)
            time.sleep(1)
        print(f"  [REC] SPEAK NOW! Recording for {record_seconds}s...          ", flush=True)

        # -- Record with sounddevice --------------------------------------
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
        print(f"  [DONE] Recording complete. Running VAD + Whisper...              ", flush=True)

        # Flatten to 1D float32
        audio_flat = raw_recording.flatten()

        # ── Auto-Gain / Peak Normalization ────────────────────────────────
        # 1. Remove DC offset (centers audio at 0 so VAD neural net doesn't get confused)
        audio_flat = audio_flat - np.mean(audio_flat)

        # 2. Dynamically boost volume to 90% max so VAD always hears it
        peak = float(np.max(np.abs(audio_flat)))
        if peak > 0.0005:
            target_peak = 0.9
            dynamic_gain = target_peak / peak
            # Cap gain at 50x so we don't blow up silent static
            dynamic_gain = min(dynamic_gain, 50.0)
            audio_flat = audio_flat * dynamic_gain
            print(f"  [GAIN] Auto-boosted volume by {dynamic_gain:.1f}x (Peak was {peak:.4f})", flush=True)

        rms_speech = float(np.sqrt(np.mean(audio_flat ** 2)))
        print(f"  [RMS] Audio level after boost: {rms_speech:.5f}", flush=True)

        if rms_speech < 0.0005:
            print("  [ERROR] Audio is near-silence even after gain boost. Check mic permissions.", flush=True)
            continue

        # -- Run VAD over frames to find speech region --------------------
        state     = np.zeros((2, 1, 128), dtype=np.float32)
        sr_scalar = np.array(RATE, dtype=np.int64)

        speech_start_idx = None
        speech_end_idx   = None
        n_frames         = len(audio_flat) // CHUNK
        max_prob         = 0.0

        for i in range(n_frames):
            frame    = audio_flat[i * CHUNK : (i + 1) * CHUNK]
            audio_in = np.expand_dims(frame, 0)
            ort_out  = vad_session.run(None, {"input": audio_in, "state": state, "sr": sr_scalar})
            state    = ort_out[1]
            prob     = float(ort_out[0][0, 0])
            max_prob = max(max_prob, prob)

            # VAD thresholds: 0.3 for speech start, 0.1 for speech end
            if prob > 0.3 and speech_start_idx is None:
                speech_start_idx = i * CHUNK
            if prob > 0.1 and speech_start_idx is not None:
                speech_end_idx = (i + 1) * CHUNK

        print(f"  [VAD] Highest probability score: {max_prob:.4f}", flush=True)

        if speech_start_idx is None:
            print("  [VAD] No speech region found. Transcribing full recording.", flush=True)
            print("        Tip: Try speaking louder or closer to the microphone.", flush=True)
            audio_to_transcribe = audio_flat
        else:
            pad   = int(0.2 * RATE)
            start = max(0, speech_start_idx - pad)
            end   = min(len(audio_flat), speech_end_idx + pad)
            audio_to_transcribe = audio_flat[start:end]
            print(f"  [VAD] Speech found: {(end-start)/RATE:.1f}s trimmed and ready.", flush=True)

        # -- Transcribe with Whisper -------------------------------------
        FRONTEND_PROMPT = "React.js, Next.js, TypeScript, JavaScript, Vite, Tailwind CSS, HTML, CSS, frontend developer, UI layout, coding framework, tech mock interview."
        Benchmark.start("stt")
        segments, _ = whisper_model.transcribe(
            audio_to_transcribe,
            language="en",
            initial_prompt=WHISPER_INITIAL_PROMPT,
            beam_size=5,
            temperature=0.0,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500)
        )
        transcript = "".join(s.text for s in segments).strip()
        stt_ms     = Benchmark.end("stt")

        print(f"\n  [TRANSCRIPT] \"{transcript}\"", flush=True)
        print(f"  [STT LATENCY] {stt_ms:.0f} ms", flush=True)
        if not transcript or len(transcript.split()) < 3:
            print("  [WARNING] Very short result - try speaking closer to the mic.", flush=True)
        print(flush=True)

    print("=" * 52, flush=True)
    print("  Test complete.", flush=True)
    print("=" * 52 + "\n", flush=True)


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