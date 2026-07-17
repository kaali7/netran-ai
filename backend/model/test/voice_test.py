import numpy as np
import pyaudio
from faster_whisper import WhisperModel

# --- Configuration Constants ---
SAMPLE_RATE = 16000
CHUNK_SIZE = 1024  # Size of raw byte buffers read from soundcard
SILENCE_THRESHOLD = 500  # Voice energy spike threshold (adjust if mic is quiet/loud)
SILENCE_DURATION_S = 1.5  # Time in seconds to wait before closing the sentence boundary


def run_standalone_listener():
    print("Loading Faster-Whisper Model...")
    # Using 'tiny' or 'base' for hyper-fast localized responsiveness
    model = WhisperModel("base", device="cpu", compute_type="int8")
    print("Model Loaded successfully!\n")

    p = pyaudio.PyAudio()
    stream = p.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=SAMPLE_RATE,
        input=True,
        frames_per_buffer=CHUNK_SIZE,
    )

    print("=== Listening Loop Active ===")
    print("Speak freely into your microphone. Pause naturally to send to Whisper.\n")

    audio_buffer = []
    silent_chunks_count = 0
    # Calculate how many silent chunks equal our target silence window
    max_silent_chunks = int((SAMPLE_RATE / CHUNK_SIZE) * SILENCE_DURATION_S)
    is_recording_speech = False

    try:
        while True:
            # Grab raw binary PCM chunks straight from your sound card
            raw_data = stream.read(CHUNK_SIZE, exception_on_overflow=False)
            audio_data = np.frombuffer(raw_data, dtype=np.int16)

            # Calculate Root-Mean-Square (RMS) amplitude to evaluate current energy level
            audio_energy = np.sqrt(np.mean(audio_data**2)) if len(audio_data) > 0 else 0

            if audio_energy > SILENCE_THRESHOLD:
                # User is speaking
                if not is_recording_speech:
                    print("[Voice Detected - Recording...]", end="", flush=True)
                    is_recording_speech = True
                audio_buffer.append(raw_data)
                silent_chunks_count = 0  # Reset silence timer
            else:
                # User is silent
                if is_recording_speech:
                    audio_buffer.append(raw_data)
                    silent_chunks_count += 1

                    # Trigger transcription when silence threshold duration is reached
                    if silent_chunks_count >= max_silent_chunks:
                        print("\n[Processing Segment via Whisper...]")

                        # Bind accumulated binary chunks natively into memory
                        flat_pcm = b"".join(audio_buffer)
                        pcm_array = np.frombuffer(flat_pcm, dtype=np.int16)

                        # Convert from Int16 representation to float32 normalized for standard execution
                        float32_audio = (
                            pcm_array.astype(np.float32) / 32768.0
                        )

                        # Run local inference tracking
                        segments, _ = model.transcribe(
                            float32_audio, beam_size=5, language="en"
                        )
                        text_output = "".join(
                            [segment.text for segment in segments]
                        ).strip()

                        if text_output:
                            print(f"-> Live Transcript: \"{text_output}\"\n")
                        else:
                            print("-> [Silence or ambient room sound ignored]\n")

                        # Flush buffers for the next sentence turn
                        audio_buffer = []
                        silent_chunks_count = 0
                        is_recording_speech = False
                        print("=== Listening Loop Active ===")

    except KeyboardInterrupt:
        print("\nTerminating Listener.")
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()


if __name__ == "__main__":
    run_standalone_listener()