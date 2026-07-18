import numpy as np
import pyaudio
import onnxruntime as ort
import os
from faster_whisper import WhisperModel
import speaker  # for echo gate checking

# Global setup
VAD_MODEL_PATH = os.path.join(os.path.dirname(__file__), "silero_vad.onnx")

print("Loading Silero VAD model...")
# Disable logging/profiling in onnxruntime to keep output clean
ort_opts = ort.SessionOptions()
ort_opts.log_severity_level = 3
vad_session = ort.InferenceSession(VAD_MODEL_PATH, ort_opts)

print("Loading Faster-Whisper model (small)...")
whisper_model = WhisperModel("small", device="cpu", compute_type="int8", cpu_threads=4)

def listen_and_transcribe():
    """
    Opens the microphone, uses Silero VAD to detect speech start and end,
    respects the echo gate, and transcribes the speech using Faster-Whisper.
    """
    # Audio hardware recording constraints
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000     # 16kHz for VAD and Whisper
    CHUNK = 512      # 32ms frame size for Silero VAD at 16kHz

    p = pyaudio.PyAudio()
    stream = p.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=RATE,
        input=True,
        frames_per_buffer=CHUNK,
    )

    print("\n[Listening...] Speak into your microphone now.")

    audio_buffer = []
    has_spoken = False
    silence_frames_counter = 0
    max_silence_frames = 22  # 22 * 32ms = 704ms (approx 700ms silence threshold)

    # Initialize VAD state
    state = np.zeros((2, 1, 128), dtype=np.float32)
    sr_scalar = np.array(RATE, dtype=np.int64)

    try:
        while True:
            # 1. Read raw PCM data from the microphone
            try:
                raw_data = stream.read(CHUNK, exception_on_overflow=False)
            except IOError:
                continue

            # 2. Check Echo Gate: If agent is speaking, drop input to prevent feedback
            if getattr(speaker, "IS_AGENT_SPEAKING", False):
                # Discard frame and reset talking state to avoid triggering mid-speech
                silence_frames_counter = 0
                continue

            # Convert to float32 normalized to [-1.0, 1.0] for VAD
            audio_frame = np.frombuffer(raw_data, dtype=np.int16).astype(np.float32) / 32768.0
            if len(audio_frame) < CHUNK:
                # Pad to 512 if read was incomplete
                audio_frame = np.pad(audio_frame, (0, CHUNK - len(audio_frame)), 'constant')

            # Prepare VAD inputs: input shape must be [1, 512]
            audio_input = np.expand_dims(audio_frame, axis=0)

            # 3. Run Silero VAD
            ort_inputs = {
                "input": audio_input,
                "state": state,
                "sr": sr_scalar
            }
            out, state = vad_session.run(None, ort_inputs)
            speech_prob = out[0, 0]

            # 4. Speech Start/End Decision Logic
            if speech_prob > 0.5:
                if not has_spoken:
                    print("[Speech Detected...]")
                has_spoken = True
                silence_frames_counter = 0
            else:
                if has_spoken:
                    silence_frames_counter += 1

            # Accumulate audio while speech is active
            if has_spoken:
                audio_buffer.append(raw_data)

            # Break loop when silence threshold is reached after speech
            if has_spoken and silence_frames_counter >= max_silence_frames:
                print("[Silence Detected. Processing speech...]")
                from benchmark import Benchmark
                Benchmark.start("ttfa")
                Benchmark.start("stt")
                break

    finally:
        # Clean up audio hardware streams immediately
        stream.stop_stream()
        stream.close()
        p.terminate()

    if not audio_buffer:
        return ""

    # Convert binary buffer to Whisper-compatible float32 array normalized to [-1.0, 1.0]
    raw_pcm_bytes = b"".join(audio_buffer)
    audio_array = np.frombuffer(raw_pcm_bytes, dtype=np.int16).astype(np.float32) / 32768.0

    # Generate transcription using Faster-Whisper
    # We specify language='en' and guide it with initial_prompt.
    # Set beam_size=1 for maximum decoding speed on CPU.
    # Set vad_filter=False since we already cropped silence using Silero VAD.
    segments, _ = whisper_model.transcribe(
        audio_array,
        beam_size=1,
        language="en",
        initial_prompt="This is a technical job interview. The candidate is answering questions.",
        vad_filter=False
    )
    transcript_text = "".join([segment.text for segment in segments]).strip()

    stt_ms = Benchmark.end("stt")
    Benchmark.last_stt_ms = stt_ms

    # Filter out junk/very short responses (e.g. noise artifact words)
    words = transcript_text.split()
    if len(words) < 3:
        # If the transcript is extremely short (e.g., noise words like "grapefruit", "bub"), discard it
        print(f"Filtered out low-confidence transcript: '{transcript_text}'")
        return ""

    return transcript_text

if __name__ == "__main__":
    user_speech = listen_and_transcribe()
    print(f"Final Transcription: '{user_speech}'")