from typing import List, Dict
from db.models import Message


def build_conversation_history(messages: List[Message], limit: int = 10) -> List[Dict[str, str]]:
    """Convert DB messages to conversation history list."""
    recent = messages[-limit:] if len(messages) > limit else messages
    return [{"role": m.role, "content": m.content} for m in recent]


def generate_session_title(first_message: str, max_length: int = 40) -> str:
    """Generate a session title from the first user message."""
    title = first_message.strip()
    if len(title) > max_length:
        title = title[:max_length].rsplit(" ", 1)[0] + "…"
    return title or "New Chat"


def format_context_from_chunks(chunks: List[str]) -> str:
    """Format retrieved chunks into a context string for the AI."""
    if not chunks:
        return ""
    parts = []
    for i, chunk in enumerate(chunks, 1):
        parts.append(f"[Excerpt {i}]\n{chunk}")
    return "\n\n".join(parts)
