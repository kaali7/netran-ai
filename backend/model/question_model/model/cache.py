"""
Netran AI — Stage 2: Contextual Question & Behavioral Prompt Engine
Module: cache.py
Description: Class-based SQLite caching subsystem (`cache.db`) for generated Stage 2 question trees.
"""

import hashlib
import json
import logging
import sqlite3
from pathlib import Path

try:
    from .schemas import Stage2Output
except ImportError:
    try:
        from model.question_model.model.schemas import Stage2Output
    except ImportError:
        from schemas import Stage2Output

logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).resolve().parent / "cache.db"


class Stage2Cache:
    """Class-based SQLite cache manager for Stage 2 outputs."""

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initializes the SQLite cache table if not existing."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS question_cache (
                        cache_key TEXT PRIMARY KEY,
                        stage2_output_json TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to initialize Stage 2 SQLite cache: {e}")

    @staticmethod
    def hash_key(jd_text: str, resume_text: str, target_seniority: str) -> str:
        combined = f"{jd_text.strip()}||{resume_text.strip()}||{target_seniority.strip()}"
        return hashlib.sha256(combined.encode("utf-8")).hexdigest()

    def get(
        self,
        jd_text: str,
        resume_text: str,
        target_seniority: str,
        session_id: str
    ) -> Stage2Output | None:
        """Retrieves cached Stage2Output if available for the given input parameters."""
        cache_key = self.hash_key(jd_text, resume_text, target_seniority)
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT stage2_output_json FROM question_cache WHERE cache_key = ?", (cache_key,))
                row = cursor.fetchone()
                if row:
                    logger.info("Retrieved Stage 2 question tree & system prompt from SQLite cache.")
                    output_dict = json.loads(row[0])
                    output_dict["session_id"] = session_id
                    return Stage2Output.model_validate(output_dict)
        except Exception as e:
            logger.error(f"Stage 2 cache read error: {e}")
        return None

    def set(
        self,
        jd_text: str,
        resume_text: str,
        target_seniority: str,
        stage2_output: Stage2Output
    ):
        """Saves generated Stage2Output into SQLite cache."""
        cache_key = self.hash_key(jd_text, resume_text, target_seniority)
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT OR REPLACE INTO question_cache (cache_key, stage2_output_json) VALUES (?, ?)",
                    (cache_key, stage2_output.model_dump_json())
                )
                conn.commit()
                logger.info("Saved Stage 2 output to SQLite cache.")
        except Exception as e:
            logger.error(f"Stage 2 cache write error: {e}")


# Backward compatibility default instance and wrappers
default_cache = Stage2Cache()

def get_cached_stage2_output(jd_text: str, resume_text: str, target_seniority: str, session_id: str) -> Stage2Output | None:
    return default_cache.get(jd_text, resume_text, target_seniority, session_id)

def set_cached_stage2_output(jd_text: str, resume_text: str, target_seniority: str, stage2_output: Stage2Output):
    default_cache.set(jd_text, resume_text, target_seniority, stage2_output)
