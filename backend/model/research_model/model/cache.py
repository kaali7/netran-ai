"""
Netran AI — Stage 1: JD Research & Market Intelligence Engine
Module: cache.py
Description: Class-based SQLite caching subsystem (`cache.db`) for interview rubrics.
"""

import hashlib
import logging
import sqlite3
from pathlib import Path

try:
    from .schemas import InterviewRubric
except ImportError:
    try:
        from model.research_model.model.schemas import InterviewRubric
    except ImportError:
        from schemas import InterviewRubric

logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).resolve().parent / "cache.db"


class Stage1Cache:
    """SQLite-based cache manager for Stage 1 interview rubrics."""

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initializes the SQLite cache table if not existing."""
        try:
            with sqlite3.connect(self.db_path) as conn:
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

    @staticmethod
    def hash_text(text: str) -> str:
        """Computes SHA-256 hash of input text."""
        return hashlib.sha256(text.strip().encode("utf-8")).hexdigest()

    def get(self, jd_text: str) -> InterviewRubric | None:
        """Retrieves cached InterviewRubric if available."""
        jd_hash = self.hash_text(jd_text)
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT rubric_json FROM rubric_cache WHERE jd_hash = ?", (jd_hash,))
                row = cursor.fetchone()
                if row:
                    logger.info("Retrieved rubric from Stage1Cache.")
                    return InterviewRubric.model_validate_json(row[0])
        except Exception as e:
            logger.error(f"Cache read error: {e}")
        return None

    def set(self, jd_text: str, rubric: InterviewRubric):
        """Saves generated InterviewRubric into cache."""
        jd_hash = self.hash_text(jd_text)
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT OR REPLACE INTO rubric_cache (jd_hash, rubric_json) VALUES (?, ?)",
                    (jd_hash, rubric.model_dump_json())
                )
                conn.commit()
                logger.info("Saved rubric to Stage1Cache.")
        except Exception as e:
            logger.error(f"Cache write error: {e}")


# Global default cache instance for module-level functions
default_cache = Stage1Cache()

def get_cached_rubric(jd_text: str) -> InterviewRubric | None:
    return default_cache.get(jd_text)

def set_cached_rubric(jd_text: str, rubric: InterviewRubric):
    default_cache.set(jd_text, rubric)
