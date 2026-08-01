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

# Force offline HuggingFace mode to prevent network overhead
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

USER_HOME = os.environ.get("USERPROFILE", os.path.expanduser("~"))

# Local model snapshot paths
DEFAULT_WHISPER_SNAPSHOT = os.path.join(
    USER_HOME,
    r".cache\huggingface\hub\models--Systran--faster-whisper-small\snapshots\536b0662742c02347bc0e980a01041f333bce120"
)

DEFAULT_KOKORO_SNAPSHOT = os.path.join(
    USER_HOME,
    r".cache\huggingface\hub\models--hexgrad--Kokoro-82M\snapshots\f3ff3571791e39611d31c381e3a41a3af07b4987"
)


def resolve_whisper_model_path() -> str:
    """Returns local snapshot path if present on disk, else fallback model string."""
    env_override = os.getenv("WHISPER_MODEL_PATH")
    if env_override and os.path.exists(env_override):
        return env_override
    if os.path.exists(DEFAULT_WHISPER_SNAPSHOT):
        return DEFAULT_WHISPER_SNAPSHOT
    return os.getenv("WHISPER_MODEL", "small")


def resolve_kokoro_model_path() -> str:
    """Returns HF repo ID string (Kokoro pipeline requires valid repo_id format)."""
    return os.getenv("KOKORO_MODEL", "hexgrad/Kokoro-82M")


@dataclass
class Stage3Config:
    """Stage 3 configuration data class."""
    ollama_model: str = field(default_factory=lambda: os.getenv("OLLAMA_MODEL", "qwen2.5:3b"))
    whisper_model: str = field(default_factory=resolve_whisper_model_path)
    kokoro_model: str = field(default_factory=resolve_kokoro_model_path)
    max_questions: int = field(default=15)

    @classmethod
    def from_env(cls) -> "Stage3Config":
        """Factory method creating config instance from environment variables."""
        return cls()

# Backward compatibility module-level exports
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")
WHISPER_MODEL = resolve_whisper_model_path()
KOKORO_MODEL = resolve_kokoro_model_path()
MAX_QUESTIONS = 15
