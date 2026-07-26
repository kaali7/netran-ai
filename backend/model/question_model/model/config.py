"""
Netran AI — Stage 2: Contextual Question & Behavioral Prompt Engine
Module: config.py
Description: Configuration loader for Stage 2. Enforces Stage2Config object model.
"""

import os
import logging
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
class Stage2Config:
    """Stage 2 configuration data class."""
    gemini_api_key: str = field(default_factory=lambda: os.getenv("GEMINI_API_KEY", ""))
    gemini_model: str = field(default_factory=lambda: os.getenv("GEMINI_MODEL", "gemini-3.6-flash"))

    @classmethod
    def from_env(cls) -> "Stage2Config":
        """Factory method creating config instance from environment variables."""
        return cls()

# Backward compatibility module-level exports
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
if not GEMINI_API_KEY:
    logger.warning("GEMINI_API_KEY is not set. API calls will fail.")
