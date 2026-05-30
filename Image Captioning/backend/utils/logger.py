"""
utils/logger.py
Centralised logging setup for Image Captioning.

Usage:
    from backend.utils.logger import get_logger
    logger = get_logger(__name__)
    logger.info("Model loaded")
    logger.inference("caption generated", duration=1.23, style="cinematic")
"""

import logging
import time
from functools import wraps
from typing import Callable

# ── Custom level: INFERENCE (between INFO and DEBUG) ─────────────────────────
INFERENCE_LEVEL = 25
logging.addLevelName(INFERENCE_LEVEL, "INFERENCE")


class ImageCaptioningLogger(logging.Logger):
    """Logger subclass with an inference() convenience method."""

    def inference(self, msg: str, *args, duration: float | None = None, **kwargs):
        """Log an inference event with optional duration."""
        if duration is not None:
            msg = f"{msg} [{duration:.2f}s]"
        self.log(INFERENCE_LEVEL, msg, *args, **kwargs)


logging.setLoggerClass(ImageCaptioningLogger)


def _build_formatter() -> logging.Formatter:
    return logging.Formatter(
        fmt="%(asctime)s  %(levelname)-9s  %(name)s — %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def configure_logging(level: int = logging.INFO) -> None:
    """
    Call once at application startup (from main.py lifespan).
    Sets up a stream handler on the root logger.
    """
    root = logging.getLogger()
    if root.handlers:
        return  # already configured

    handler = logging.StreamHandler()
    handler.setFormatter(_build_formatter())
    root.addHandler(handler)
    root.setLevel(level)


def get_logger(name: str) -> ImageCaptioningLogger:
    """Return a ImageCaptioningLogger for the given module name."""
    return logging.getLogger(name)  # type: ignore[return-value]


# ── Timing decorator ─────────────────────────────────────────────────────────

def log_duration(logger: ImageCaptioningLogger, label: str):
    """
    Decorator that logs execution time of the wrapped function.

    Example:
        @log_duration(logger, "BLIP inference")
        def generate_caption(...): ...
    """
    def decorator(fn: Callable):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            start = time.perf_counter()
            try:
                result = fn(*args, **kwargs)
                elapsed = time.perf_counter() - start
                logger.inference(label, duration=elapsed)
                return result
            except Exception as exc:
                elapsed = time.perf_counter() - start
                logger.error(f"{label} FAILED after {elapsed:.2f}s — {exc}")
                raise
        return wrapper
    return decorator
