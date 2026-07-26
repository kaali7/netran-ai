"""
Netran AI — Stage 2: Contextual Question & Behavioral Prompt Engine
Module: cache.py
Description: SQLite-based hashing subsystem (`cache.db`) for caching generated Stage 2 question trees
             and system prompts by SHA-256 hash of (JD + Resume + Seniority), eliminating redundant LLM API calls.
"""

import sqlite3
import hashlib
import json
import logging
from pathlib import Path
from typing import Optional

try:
    from .schemas import Stage2Output
except ImportError:
    try:
        from model.question_model.model.schemas import Stage2Output
    except ImportError:
        from schemas import Stage2Output

logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).resolve().parent / "cache.db"

def init_db():
    """Initializes the SQLite cache table if not existing."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
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

def _hash_key(jd_text: str, resume_text: str, target_seniority: str) -> str:
    combined = f"{jd_text.strip()}||{resume_text.strip()}||{target_seniority.strip()}"
    return hashlib.sha256(combined.encode("utf-8")).hexdigest()

def get_cached_stage2_output(
    jd_text: str,
    resume_text: str,
    target_seniority: str,
    session_id: str
) -> Optional[Stage2Output]:
    """Retrieves cached Stage2Output if available for the given input parameters."""
    init_db()
    cache_key = _hash_key(jd_text, resume_text, target_seniority)
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT stage2_output_json FROM question_cache WHERE cache_key = ?", (cache_key,))
            row = cursor.fetchone()
            if row:
                logger.info("Retrieved Stage 2 question tree & system prompt from SQLite cache.")
                output_dict = json.loads(row[0])
                output_dict["session_id"] = session_id  # Update session_id to current run
                return Stage2Output.model_validate(output_dict)
    except Exception as e:
        logger.error(f"Stage 2 cache read error: {e}")
    return None

def set_cached_stage2_output(
    jd_text: str,
    resume_text: str,
    target_seniority: str,
    stage2_output: Stage2Output
):
    """Saves generated Stage2Output into SQLite cache."""
    init_db()
    cache_key = _hash_key(jd_text, resume_text, target_seniority)
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO question_cache (cache_key, stage2_output_json) VALUES (?, ?)",
                (cache_key, stage2_output.model_dump_json())
            )
            conn.commit()
            logger.info("Saved Stage 2 output to SQLite cache.")
    except Exception as e:
        logger.error(f"Stage 2 cache write error: {e}")
