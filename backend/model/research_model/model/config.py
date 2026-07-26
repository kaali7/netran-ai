"""
Netran AI — Stage 1: JD Research & Market Intelligence Engine
Module: config.py
Description: Configuration loader for Stage 1. Enforces Stage1Config object model.
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

TRUSTED_DOMAINS_DEFAULT = [
    "linkedin.com",
    "leetcode.com",
    "glassdoor.com",
    "github.com",
    "stackoverflow.com",
    "geeksforgeeks.org",
    "reddit.com",
    "medium.com",
    "dev.to",
]

@dataclass
class Stage1Config:
    """Stage 1 configuration data class."""
    gemini_api_key: str = field(default_factory=lambda: os.getenv("GEMINI_API_KEY", ""))
    gemini_model: str = field(default_factory=lambda: os.getenv("GEMINI_MODEL", "gemini-3.6-flash"))
    tavily_api_key: str = field(default_factory=lambda: os.getenv("TAVILY_API_KEY", ""))
    trusted_domains: list[str] = field(default_factory=lambda: TRUSTED_DOMAINS_DEFAULT)

    @classmethod
    def from_env(cls) -> "Stage1Config":
        """Factory method creating config instance from environment variables."""
        return cls()

# Backward compatibility module-level exports
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
TRUSTED_DOMAINS = TRUSTED_DOMAINS_DEFAULT
