"""
Netran AI — Stage 1: JD Research & Market Intelligence Engine
Module: cache.py
Description: SQLite-based hashing subsystem (`cache.db`) for caching generated interview rubrics
             by SHA-256 hash of JD text, eliminating redundant LLM API calls and search queries.
"""

import sqlite3
import hashlib
import json
import logging
from pathlib import Path
from typing import Optional
try:
    from .schemas import InterviewRubric
except ImportError:
    try:
        from model.research_model.model.schemas import InterviewRubric
    except ImportError:
        from schemas import InterviewRubric

logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).resolve().parent / "cache.db"

def init_db():
    """Initializes the SQLite cache table if not existing."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS rubric_cache (
                    jd_hash TEXT PRIMARY KEY,
                    rubric_json TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
    except Exception as e:
        logger.error(f"Failed to initialize SQLite cache: {e}")

def _hash_text(text: str) -> str:
    return hashlib.sha256(text.strip().encode("utf-8")).hexdigest()

def get_cached_rubric(jd_text: str) -> Optional[InterviewRubric]:
    """Retrieves cached InterviewRubric if available."""
    init_db()
    jd_hash = _hash_text(jd_text)
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT rubric_json FROM rubric_cache WHERE jd_hash = ?", (jd_hash,))
            row = cursor.fetchone()
            if row:
                logger.info("Retrieved rubric from SQLite cache.")
                return InterviewRubric.model_validate_json(row[0])
    except Exception as e:
        logger.error(f"Cache read error: {e}")
    return None

def set_cached_rubric(jd_text: str, rubric: InterviewRubric):
    """Saves generated InterviewRubric into cache."""
    init_db()
    jd_hash = _hash_text(jd_text)
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO rubric_cache (jd_hash, rubric_json) VALUES (?, ?)",
                (jd_hash, rubric.model_dump_json())
            )
            conn.commit()
            logger.info("Saved rubric to SQLite cache.")
    except Exception as e:
        logger.error(f"Cache write error: {e}")
