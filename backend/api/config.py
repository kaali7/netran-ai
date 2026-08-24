"""
Netran AI — Application Configuration for FastAPI Gateway.
Loads environment variables from backend/.env.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Base backend directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from backend/.env
ENV_PATH = BASE_DIR / ".env"
load_dotenv(dotenv_path=ENV_PATH)


class Settings:
    """Central settings class for FastAPI application."""

    # Project Information
    PROJECT_NAME: str = "Netran AI Backend API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # AI Model Keys
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
    TAVILY_API_KEY: str = os.getenv("TAVILY_API_KEY", "")

    # Security & Auth
    JWT_SECRET_KEY: str = os.getenv(
        "JWT_SECRET_KEY", "netran_ai_jwt_secret_key_change_in_production_9f8e7d6c5b4a3a21"
    )
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR}/data/cache.db")

    # CORS
    CORS_ORIGINS: list[str] = [
        origin.strip()
        for origin in os.getenv(
            "API_CORS_ORIGINS",
            "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000,http://localhost:5174,http://127.0.0.1:5174,http://localhost:8000,http://127.0.0.1:8000",
        ).split(",")
        if origin.strip()
    ]
    CORS_ORIGIN_REGEX: str | None = os.getenv(
        "API_CORS_ORIGIN_REGEX",
        r"^https?://(localhost|127\.0\.0\.1|192\.168\.\d+\.\d+|10\.\d+\.\d+\.\d+|172\.(1[6-9]|2\d|3[0-1])\.\d+\.\d+)(:\d+)?$",
    )


settings = Settings()
