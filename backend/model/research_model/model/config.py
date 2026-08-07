"""
Netran AI — Stage 1: JD Research & Market Intelligence Engine
Module: config.py
Description: Configuration loader for Stage 1. Enforces Stage1Config object model with categorized domain search vectors.
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

# Categorized domain vectors for targeted Tavily search filtering
TRUSTED_DOMAINS_BY_VECTOR: dict[str, list[str]] = {
    # Vector 1: Technical Questions & System Design Deep Dives
    "technical": [
        "leetcode.com",
        "github.com",
        "geeksforgeeks.org",
        "stackoverflow.com",
        "teamblind.com",
        "careercup.com",
        "tryexponent.com",
        "bytebytego.com",
        "educative.io",
        "dev.to",
        "medium.com"
    ],
    
    # Vector 2: Salary, Compensation & Market Intelligence (USD & INR CTC)
    "market_salary": [
        "levels.fyi",
        "ambitionbox.com",
        "wellfound.com",
        "glassdoor.com",
        "linkedin.com",
        "reddit.com"
    ],
    
    # Vector 3: HR Recruiter Lens, Screening Standards & Behavioral
    "hr_recruiter": [
        "resources.workable.com",
        "linkedin.com",
        "glassdoor.com",
        "teamblind.com",
        "reddit.com"
    ]
}

# Complete fallback list combining all domain vectors
TRUSTED_DOMAINS_DEFAULT: list[str] = sorted(list(set(
    domain 
    for domains in TRUSTED_DOMAINS_BY_VECTOR.values() 
    for domain in domains
)))


@dataclass
class Stage1Config:
    """Stage 1 configuration data class."""
    gemini_api_key: str = field(default_factory=lambda: os.getenv("GEMINI_API_KEY", ""))
    gemini_model: str = field(default_factory=lambda: os.getenv("GEMINI_MODEL", "gemini-3.6-flash"))
    tavily_api_key: str = field(default_factory=lambda: os.getenv("TAVILY_API_KEY", ""))
    trusted_domains: list[str] = field(default_factory=lambda: TRUSTED_DOMAINS_DEFAULT)
    trusted_domains_by_vector: dict[str, list[str]] = field(default_factory=lambda: TRUSTED_DOMAINS_BY_VECTOR)

    @classmethod
    def from_env(cls) -> "Stage1Config":
        """Factory method creating config instance from environment variables."""
        return cls()


# Backward compatibility module-level exports
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
TRUSTED_DOMAINS = TRUSTED_DOMAINS_DEFAULT

