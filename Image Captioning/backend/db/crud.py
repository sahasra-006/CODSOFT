"""
db/crud.py
Caption persistence operations.
"""

import logging
from typing import Optional
from backend.db.database import get_connection

logger = logging.getLogger(__name__)


def save_caption(
    filename: str,
    style: str,
    caption: str,
    device: str,
) -> dict:
    """Persist a generated caption and return the full row."""
    conn = get_connection()
    with conn:
        cursor = conn.execute(
            """
            INSERT INTO captions (filename, style, caption, device)
            VALUES (?, ?, ?, ?)
            """,
            (filename, style, caption, device),
        )
        row_id = cursor.lastrowid

    row = conn.execute(
        "SELECT * FROM captions WHERE id = ?", (row_id,)
    ).fetchone()
    conn.close()
    return dict(row)


def fetch_history(limit: int = 50, offset: int = 0) -> list[dict]:
    """Return most-recent captions, newest first."""
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT * FROM captions
        ORDER BY created_at DESC
        LIMIT ? OFFSET ?
        """,
        (limit, offset),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def fetch_caption(caption_id: int) -> Optional[dict]:
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM captions WHERE id = ?", (caption_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def delete_caption(caption_id: int) -> bool:
    conn = get_connection()
    with conn:
        cursor = conn.execute(
            "DELETE FROM captions WHERE id = ?", (caption_id,)
        )
    conn.close()
    return cursor.rowcount > 0
