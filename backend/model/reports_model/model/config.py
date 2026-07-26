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

@dataclass
class Stage4Config:
    """Stage 4 configuration data class."""
    gemini_api_key: str = field(default_factory=lambda: os.getenv("GEMINI_API_KEY", ""))
    gemini_model: str = field(default_factory=lambda: os.getenv("GEMINI_MODEL", "gemini-3.6-flash"))

    @classmethod
    def from_env(cls) -> "Stage4Config":
        """Factory method creating config instance from environment variables."""
        return cls()

# Backward compatibility module-level exports
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
