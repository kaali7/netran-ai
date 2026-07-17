import numpy as np
import pyaudio
from kokoro import KPipeline

# Break 1: Global Model Setup (Loads only once inside the folder)
print("Loading Kokoro TTS model into memory...")
kokoro_pipeline = KPipeline(lang_code="a")  # 'a' stands for American English


# Break 2: The Core Text-to-Speech Engine
def speak_text(text_to_say, voice_preset="af_bella"):
    """Converts a string of text into raw audio using Kokoro

    and plays it back through the speakers immediately.
    
    :param text_to_say: String of text for Eva to say.
    :param voice_preset: Default voice token (e.g., af_bella, af_sarah, am_adam).
    """
    if not text_to_say.strip():
        return

    # PyAudio structural playback settings
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 24000  # Kokoro models output natively at 24kHz

    p = pyaudio.PyAudio()
    
    try:
        # Open hardware speaker output channel
        output_stream = p.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            output=True
        )

        # Generate structural audio arrays using Kokoro pipeline
        generator = kokoro_pipeline(text_to_say, voice=voice_preset, speed=1.0)
        
        # Change this part inside your generator loop in speaker.py:
        for _, _, audio_array in generator:
            if audio_array is None:
                continue
                
            # Move tensor to CPU and convert to a native NumPy array safely
            if hasattr(audio_array, "cpu"):
                audio_array = audio_array.cpu().numpy()
        
            # Now astype() will work perfectly without throwing errors!
            pcm_integers = (audio_array * 32767).astype(np.int16)
            binary_audio_payload = pcm_integers.tobytes()
    
            output_stream.write(binary_audio_payload)
        
    except Exception as e:
        print(f"\n[Speaker Error: Check audio drivers. Details: {str(e)}]")
        
    finally:
        p.terminate()

# Break 4: Local Test Execution
if __name__ == "__main__":
    print("Testing Speaker Module out loud...")
    sample_text = "Testing complete. I am now able to translate text back into audio using the local pipeline."
    print(f"Speaking: '{sample_text}'")
    speak_text(sample_text)