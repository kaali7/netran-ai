"""
Netran AI — Stage 3: Live Voice-to-Voice Loop
Module: download_vad.py
Description: Download and verification utility for Silero VAD v3 ONNX model weights (`silero_vad.onnx`).
"""

import urllib.request
import os

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
    print("VAD model already present. Nothing to do.")
