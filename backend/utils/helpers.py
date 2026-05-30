import uuid
import re
from datetime import datetime
from typing import Any, Dict


def new_session_id() -> str:
    return str(uuid.uuid4())


def sanitize_filename(filename: str) -> str:
    return re.sub(r"[^\w\-_\. ]", "_", filename)


def format_timestamp(dt: datetime) -> str:
    return dt.strftime("%b %d, %Y %H:%M")


def truncate(text: str, max_len: int = 100) -> str:
    if len(text) <= max_len:
        return text
    return text[:max_len].rsplit(" ", 1)[0] + "…"


def success_response(data: Any = None, message: str = "Success") -> Dict:
    return {"status": "success", "message": message, "data": data}


def error_response(message: str, code: int = 400) -> Dict:
    return {"status": "error", "message": message, "code": code}
