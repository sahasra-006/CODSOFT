"""
app.py — Hugging Face Spaces entry point.
HF Spaces looks for app.py at root and expects the ASGI app called `app`.
"""
from backend.main import app  # noqa: F401 — re-exported for HF

# HF Spaces auto-detects and serves the `app` object via uvicorn.
