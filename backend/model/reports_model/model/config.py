"""
Netran AI — Stage 4: Post-Session Multimodal Evaluation & Report Generation Engine
Module: config.py
Description: Configuration loader for Stage 4. Enforces Stage4Config object model.
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

def get_gemini_api_keys() -> list[str]:
    """
    Extracts all configured Gemini API keys from environment variables.
    Checks:
    1. GEMINI_API_KEYS (comma-separated list)
    2. GEMINI_API_KEY1, GEMINI_API_KEY2, ... GEMINI_API_KEY10
    3. GEMINI_API_KEY (single default)
    Returns a deduplicated list of non-empty API keys.
    """
    keys: list[str] = []
    
    # 1. Comma-separated list
    raw_keys = os.getenv("GEMINI_API_KEYS", "")
    if raw_keys:
        for k in raw_keys.split(","):
            cleaned = k.strip().strip('"\'')
            if cleaned and cleaned not in keys:
                keys.append(cleaned)

    # 2. Numbered keys GEMINI_API_KEY1 .. GEMINI_API_KEY10
    for i in range(1, 11):
        k = os.getenv(f"GEMINI_API_KEY{i}", "").strip().strip('"\'')
        if k and k not in keys:
            keys.append(k)

    # 3. Default single key GEMINI_API_KEY
    default_k = os.getenv("GEMINI_API_KEY", "").strip().strip('"\'')
    if default_k and default_k not in keys:
        keys.append(default_k)

    return keys


@dataclass
class Stage4Config:
    """Stage 4 configuration data class supporting multi-key parallel processing."""
    gemini_api_key: str = field(default_factory=lambda: (get_gemini_api_keys() or [""])[0])
    gemini_api_keys: list[str] = field(default_factory=get_gemini_api_keys)
    gemini_model: str = field(default_factory=lambda: os.getenv("GEMINI_MODEL", "gemini-3.6-flash"))
    groq_api_key: str = field(default_factory=lambda: os.getenv("GROQ_API_KEY", ""))
    groq_model: str = field(default_factory=lambda: os.getenv("GROQ_EVALUATION_MODEL", "openai/gpt-oss-120b"))
    ollama_model: str = field(default_factory=lambda: os.getenv("OLLAMA_MODEL", "qwen2.5:3b"))
    emotion_model: str = field(default_factory=lambda: os.getenv("STAGE4_EMOTION_MODEL", "superb/wav2vec2-base-superb-er"))
    max_parallel_workers: int = field(default_factory=lambda: int(os.getenv("STAGE4_MAX_WORKERS", "5")))

    @classmethod
    def from_env(cls) -> "Stage4Config":
        """Factory method creating config instance from environment variables."""
        return cls()

    def get_api_keys(self) -> list[str]:
        """Returns the active list of non-empty API keys."""
        if self.gemini_api_keys:
            return [k for k in self.gemini_api_keys if k]
        if self.gemini_api_key:
            return [self.gemini_api_key]
        return get_gemini_api_keys()


# Backward compatibility module-level exports
GEMINI_API_KEYS = get_gemini_api_keys()
GEMINI_API_KEY = (GEMINI_API_KEYS or [""])[0]
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
MAX_PARALLEL_WORKERS = int(os.getenv("STAGE4_MAX_WORKERS", "5"))
