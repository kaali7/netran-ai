"""
Netran AI — Workflow Orchestrator
Module: config.py
Description: Master configuration loader for unified workflow. Loads environment variables
             from backend root `.env` and sets up non-colliding sys.path entries across all 4 stages.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Path references
WORKFLOW_MODEL_DIR = Path(__file__).resolve().parent
WORKFLOW_DIR = WORKFLOW_MODEL_DIR.parent
MODEL_DIR = WORKFLOW_DIR.parent
BACKEND_DIR = MODEL_DIR.parent

DOTENV_PATH = BACKEND_DIR / ".env"
if DOTENV_PATH.exists():
    load_dotenv(dotenv_path=DOTENV_PATH)
else:
    load_dotenv()

# Inject stage paths into sys.path
RESEARCH_MODEL_DIR = MODEL_DIR / "research_model"
VOICE_MODEL_DIR = MODEL_DIR / "voice_to_voice_model" / "model"

for stage_path in [str(MODEL_DIR), str(RESEARCH_MODEL_DIR), str(VOICE_MODEL_DIR)]:
    if stage_path not in sys.path:
        sys.path.insert(0, stage_path)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:1.5b")

PROCESS_BASE_DIR = WORKFLOW_DIR / "test" / "process"
OUTPUT_BASE_DIR = WORKFLOW_DIR / "test" / "output"

os.makedirs(PROCESS_BASE_DIR, exist_ok=True)
os.makedirs(OUTPUT_BASE_DIR, exist_ok=True)
