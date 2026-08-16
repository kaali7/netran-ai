"""
Netran AI — Database Connection & Session Management.
Uses SQLAlchemy with SQLite (zero-code migration path to PostgreSQL).
"""

from typing import Generator
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from api.config import settings

# Ensure data directory exists
db_path_str = settings.DATABASE_URL.replace("sqlite:///", "")
if not db_path_str.startswith(":memory:"):
    db_file = Path(db_path_str)
    db_file.parent.mkdir(parents=True, exist_ok=True)

# Connect args for SQLite to handle multi-threaded requests
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def init_db() -> None:
    """Initialize database tables and run lightweight column migrations."""
    Base.metadata.create_all(bind=engine)

    # Lightweight column migration check for SQLite
    if settings.DATABASE_URL.startswith("sqlite"):
        from sqlalchemy import text
        with engine.connect() as conn:
            # Check if progress_message column exists on sessions table
            res = conn.execute(text("PRAGMA table_info(sessions);")).fetchall()
            columns = [row[1] for row in res]
            if "progress_message" not in columns:
                conn.execute(text("ALTER TABLE sessions ADD COLUMN progress_message VARCHAR;"))
                conn.commit()



def get_db() -> Generator:
    """FastAPI dependency to yield a database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
