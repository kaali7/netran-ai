"""
Netran AI — Stage 1: JD Research & Market Intelligence Engine
Module: config.py
Description: Configuration loader for Stage 1. Reads GEMINI_API_KEY, TAVILY_API_KEY, and TRUSTED_DOMAINS.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Search for .env file up to backend/model level
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")

TRUSTED_DOMAINS = [
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
