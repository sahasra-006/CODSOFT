"""
utils/helpers.py
Shared formatting and validation helpers.
"""

import re
from datetime import datetime


def friendly_time(iso_string: str) -> str:
    """Convert ISO datetime string to human-friendly relative time."""
    try:
        dt = datetime.fromisoformat(iso_string)
        delta = datetime.utcnow() - dt
        seconds = int(delta.total_seconds())

        if seconds < 60:
            return "just now"
        if seconds < 3600:
            m = seconds // 60
            return f"{m}m ago"
        if seconds < 86400:
            h = seconds // 3600
            return f"{h}h ago"
        d = seconds // 86400
        return f"{d}d ago"
    except Exception:
        return iso_string


def sanitise_filename(name: str) -> str:
    """Strip unsafe characters from a filename."""
    name = re.sub(r"[^\w\-_. ]", "", name)
    return name.strip() or "upload"
