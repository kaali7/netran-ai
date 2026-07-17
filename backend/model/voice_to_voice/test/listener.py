import numpy as np
import pyaudio
from faster_whisper import WhisperModel

# Break 1: Global Model Setup (Loads only once inside the folder)
# Using "base" and compute_type="int8" so it runs cleanly on any CPU/GPU
print("Loading Faster-Whisper model into memory...")
whisper_model = WhisperModel("base", device="cpu", compute_type="int8")


# Break 2: Check if the user has gone silent (Simple VAD)
def check_silence(audio_frame, threshold=500):
    """Calculates the root-mean-square amplitude to detect if someone is speaking."""
    # Convert to float32 first to completely prevent integer overflow during squaring
    audio_data = np.frombuffer(audio_frame, dtype=np.int16).astype(np.float32)
    if len(audio_data) == 0:
        return True
        
    # Safe calculation with no overflows
    rms = np.sqrt(np.mean(audio_data**2))
    return rms < threshold


# Break 3: The Main Listening Engine Function
def listen_and_transcribe():
    """Opens the microphone, records until a sustained pause is detected,

    and returns the live string transcript.
    """
    # Audio hardware recording constraints
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000  # 16kHz is native for Whisper models
    CHUNK = 1024  # Size of raw byte frames read from the sound card

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
    silence_counter = 0
    has_spoken = False

    while True:
        # Read raw PCM data from the microphone
        raw_data = stream.read(CHUNK, exception_on_overflow=False)
        audio_buffer.append(raw_data)

        # Check for silence state
        is_silent = check_silence(raw_data)

        if not is_silent:
            has_spoken = True
            silence_counter = 0  # Reset counter while active speaking is happening
        else:
            if has_spoken:
                silence_counter += 1

        # If the user has spoken, and then remains silent for ~1.5 seconds (about 25 continuous chunks)
        if has_spoken and silence_counter > 25:
            print("[Processing Speech...]")
            break

    # Clean up audio hardware streams immediately
    stream.stop_stream()
    stream.close()
    p.terminate()

    # Break 4: Convert binary buffer to Whisper-compatible format
    raw_pcm_bytes = b"".join(audio_buffer)
    # Convert standard 16-bit integer PCM data to a float32 array normalized to [-1.0, 1.0]
    audio_array = np.frombuffer(raw_pcm_bytes, dtype=np.int16)
    audio_array = audio_array.astype(np.float32) / 32768.0

    # Break 5: Generate the final text string via Faster-Whisper
    segments, _ = whisper_model.transcribe(audio_array, beam_size=5)
    transcript_text = "".join([segment.text for segment in segments]).strip()

    return transcript_text


# Break 6: local test execution inside the script
if __name__ == "__main__":
    # Test our isolated module loop
    user_speech = listen_and_transcribe()
    print(f"Final Transcription: '{user_speech}'")