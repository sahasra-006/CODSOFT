"""
db/database.py
SQLite setup using the stdlib sqlite3 module — no ORM overhead.
"""

import sqlite3
from backend.core.config import DB_PATH
from backend.utils.logger import get_logger

logger = get_logger(__name__)


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row          # rows as dicts
    conn.execute("PRAGMA journal_mode=WAL") # better concurrent reads
    return conn


def init_db():
    """Create tables if they don't exist."""
    conn = get_connection()
    with conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS captions (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                filename    TEXT NOT NULL,
                style       TEXT NOT NULL DEFAULT 'descriptive',
                caption     TEXT NOT NULL,
                device      TEXT NOT NULL DEFAULT 'cpu',
                created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_captions_created
                ON captions(created_at DESC);
        """)
    conn.close()
    logger.info("Database initialised.")
