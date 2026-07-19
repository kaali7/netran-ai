import numpy as np
import pyaudio
from kokoro import KPipeline

# Global agent speaking state for echo gate
IS_AGENT_SPEAKING = False

# Lazy-init sentinel: the heavy Kokoro model is only loaded on the FIRST call
# to speak_text(). Importing this module does NOT trigger a model load.
_kokoro_pipeline = None

def _get_pipeline():
    """Returns the shared Kokoro pipeline, initializing it on first use."""
    global _kokoro_pipeline
    if _kokoro_pipeline is None:
        print("Loading Kokoro TTS model into memory...")
        _kokoro_pipeline = KPipeline(lang_code="a")  # 'a' = American English
    return _kokoro_pipeline

def preload_models():
    """Preloads the heavy TTS models into memory."""
    print("Pre-heating Kokoro TTS engine...", flush=True)
    _get_pipeline()

# Break 2: The Core Text-to-Speech Engine
def speak_text(text_to_say, voice_preset="af_bella"):
    """Converts a string of text into raw audio using Kokoro
    and plays it back through the speakers immediately.
    """
    global IS_AGENT_SPEAKING
    if not text_to_say.strip():
        return

    import sounddevice as sd

    try:
        IS_AGENT_SPEAKING = True

        print("[DEBUG] Calling pipeline to generate audio...", flush=True)
        generator = _get_pipeline()(text_to_say, voice=voice_preset, speed=1.0)
        
        for _, _, audio_array in generator:
            if audio_array is None:
                continue
                
            # Move tensor to CPU and convert to numpy float32
            if hasattr(audio_array, "cpu"):
                audio_array = audio_array.cpu().numpy()
            
            # sounddevice plays float32 arrays natively! No need to convert to int16 or bytes.
            # Kokoro native sample rate is 24000
            sd.play(audio_array, samplerate=24000)
            sd.wait() # Block until this chunk finishes playing
        
    except Exception as e:
        print(f"\n[Speaker Error: Check audio drivers. Details: {str(e)}]")
        
    finally:
        IS_AGENT_SPEAKING = False

# Break 4: Local Test Execution
if __name__ == "__main__":
    print("Testing Speaker Module out loud...")
    sample_text = "Testing complete. I am now able to translate text back into audio using the local pipeline."
    print(f"Speaking: '{sample_text}'")
    speak_text(sample_text)