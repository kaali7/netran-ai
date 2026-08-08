"""
Netran AI — Workflow Orchestrator Engine
Module: cache.py
Description: Master class-based WorkflowCache subsystem (`cache.db`) providing end-to-end caching 
             and cross-stage cache invalidation across Stage 1, Stage 2, and Stage 4.
"""

import hashlib
import json
import logging
import sqlite3
from pathlib import Path
from typing import Any

try:
    from model.question_model.model.cache import Stage2Cache
    from model.research_model.model.cache import Stage1Cache
except ImportError:
    from cache import Stage2Cache  # type: ignore
    from cache import Stage1Cache  # type: ignore

logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).resolve().parent / "cache.db"


class WorkflowCache:
    """Master SQLite cache manager for full workflow pipeline executions."""

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.stage1_cache = Stage1Cache()
        self.stage2_cache = Stage2Cache()
        self._init_db()

    def _init_db(self):
        """Initializes the Workflow SQLite cache schema if not existing."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS workflow_cache (
                        workflow_hash TEXT PRIMARY KEY,
                        session_id TEXT NOT NULL,
                        stage1_output_json TEXT,
                        stage2_output_json TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to initialize Workflow SQLite cache: {e}")

    @staticmethod
    def hash_key(jd_text: str, resume_path: str, target_seniority: str) -> str:
        """Computes SHA-256 hash for workflow inputs."""
        combined = f"{jd_text.strip()}||{resume_path.strip()}||{target_seniority.strip()}"
        return hashlib.sha256(combined.encode("utf-8")).hexdigest()

    def get(
        self,
        jd_text: str,
        resume_path: str,
        target_seniority: str
    ) -> dict[str, Any] | None:
        """Retrieves cached workflow metadata if existing."""
        key = self.hash_key(jd_text, resume_path, target_seniority)
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT stage1_output_json, stage2_output_json FROM workflow_cache WHERE workflow_hash = ?",
                    (key,)
                )
                row = cursor.fetchone()
                if row and row[0] and row[1]:
                    logger.info("Retrieved valid Workflow cache entry.")
                    return {
                        "stage1": json.loads(row[0]),
                        "stage2": json.loads(row[1])
                    }
        except Exception as e:
            logger.warning(f"Workflow cache lookup failed ({e}). Proceeding to pipeline execution.")
        return None

    def set(
        self,
        jd_text: str,
        resume_path: str,
        target_seniority: str,
        session_id: str,
        stage1_output: Any,
        stage2_output: Any
    ):
        """Stores workflow execution outputs into cache."""
        key = self.hash_key(jd_text, resume_path, target_seniority)
        try:
            s1_json = stage1_output.model_dump_json() if hasattr(stage1_output, "model_dump_json") else json.dumps(stage1_output)
            s2_json = stage2_output.model_dump_json() if hasattr(stage2_output, "model_dump_json") else json.dumps(stage2_output)

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT OR REPLACE INTO workflow_cache (workflow_hash, session_id, stage1_output_json, stage2_output_json) VALUES (?, ?, ?, ?)",
                    (key, session_id, s1_json, s2_json)
                )
                conn.commit()
                logger.info(f"Saved workflow execution cache entry for session {session_id}.")
        except Exception as e:
            logger.error(f"Failed to write to WorkflowCache: {e}")

    def clear_all(self):
        """Clears all caches across Stage 1, Stage 2, and Workflow."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM workflow_cache")
                conn.commit()
            
            self.stage1_cache.clear()
            self.stage2_cache.clear()
            logger.info("All workflow & stage cache databases cleared successfully.")
        except Exception as e:
            logger.error(f"Error clearing workflow caches: {e}")


# Global default instance
default_workflow_cache = WorkflowCache()
