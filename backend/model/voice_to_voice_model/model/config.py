"""
Netran AI — Stage 3: Live Voice-to-Voice Loop
Module: config.py
Description: Configuration loader for Stage 3. Enforces Stage3Config object model.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

# Search for .env file up to backend root
env_path = Path(__file__).resolve().parent.parent.parent.parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv()

@dataclass
class Stage3Config:
    """Stage 3 configuration data class."""
    ollama_model: str = field(default_factory=lambda: os.getenv("OLLAMA_MODEL", "qwen2.5:1.5b"))
    whisper_model: str = field(default_factory=lambda: os.getenv("WHISPER_MODEL", "small"))
    max_questions: int = field(default=15)

    @classmethod
    def from_env(cls) -> "Stage3Config":
        """Factory method creating config instance from environment variables."""
        return cls()

# Backward compatibility module-level exports
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:1.5b")
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "small")
MAX_QUESTIONS = 15
