"""
Netran AI — Stage 3: Live Voice-to-Voice Loop
Module: download_vad.py
Description: Download and verification utility for Silero VAD v3 ONNX model weights and Hugging Face local AI models.
"""

import os
import urllib.request
import subprocess
import sys

def download_silero_vad():
    VAD_URL = "https://github.com/snakers4/silero-vad/raw/master/src/silero_vad/data/silero_vad.onnx"
    OUT_PATH = os.path.join(os.path.dirname(__file__), "silero_vad.onnx")

    if not os.path.exists(OUT_PATH):
        print("Downloading Silero VAD model (~2 MB)...")
        try:
            urllib.request.urlretrieve(VAD_URL, OUT_PATH)
            print(f"Saved to: {OUT_PATH}")
        except Exception as e:
            print(f"Error downloading VAD model: {e}")
    else:
        print("Silero VAD model already present. Nothing to do.")

def download_hf_models():
    print("\nDownloading Hugging Face models...")
    models = [
        "Systran/faster-whisper-small",
        "hexgrad/Kokoro-82M",
        "speechbrain/spkrec-ecapa-voxceleb"
    ]
    
    # Path to hf inside the same .venv/Scripts folder as the running python.exe
    hf_cli = os.path.join(os.path.dirname(sys.executable), "hf.exe")
    
    # Fallback to general hf if running on non-windows or outside this specific venv layout
    if not os.path.exists(hf_cli):
        hf_cli = "hf"
        
    for model in models:
        print(f"\n--- Fetching {model} ---")
        try:
            subprocess.run([hf_cli, "download", model], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error downloading {model}: {e}")
        except Exception as e:
            print(f"An unexpected error occurred while downloading {model}: {e}")

if __name__ == "__main__":
    print("========================================")
    print("  Netran AI Local Model Pre-Downloader  ")
    print("========================================")
    download_silero_vad()
    download_hf_models()
    print("\n========================================")
    print("All downloads finished!")
