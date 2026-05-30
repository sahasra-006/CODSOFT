"""
core/preprocessing.py
Image validation and normalisation before BLIP inference.
All limits are read from config.py — nothing hardcoded here.
"""

import io
from PIL import Image, ImageOps

from backend.core.config import MAX_IMAGE_DIMENSION, SUPPORTED_FORMATS
from backend.utils.logger import get_logger

logger = get_logger(__name__)


def preprocess_image(file_bytes: bytes) -> Image.Image:
    """
    Decode, validate, and normalise an image from raw bytes.

    Returns a PIL Image in RGB mode, resized to fit within MAX_DIMENSION.
    Raises ValueError for unsupported or corrupt images.
    """
    try:
        image = Image.open(io.BytesIO(file_bytes))
    except Exception as exc:
        raise ValueError(f"Cannot decode image: {exc}") from exc

    fmt = image.format or ""
    if fmt.upper() not in SUPPORTED_FORMATS:
        raise ValueError(f"Unsupported image format: {fmt}. Accepted: {SUPPORTED_FORMATS}")

    # Normalise orientation (EXIF)
    image = ImageOps.exif_transpose(image)

    # Convert to RGB (handles RGBA, palette, grayscale, etc.)
    if image.mode != "RGB":
        image = image.convert("RGB")

    # Resize if too large (keeps aspect ratio)
    image = _resize_if_needed(image)

    return image


def _resize_if_needed(image: Image.Image) -> Image.Image:
    w, h = image.size
    if max(w, h) > MAX_IMAGE_DIMENSION:
        scale = MAX_IMAGE_DIMENSION / max(w, h)
        new_size = (int(w * scale), int(h * scale))
        image = image.resize(new_size, Image.LANCZOS)
        logger.debug(f"Resized {w}×{h} → {new_size[0]}×{new_size[1]}")
    return image


def image_to_bytes(image: Image.Image, fmt: str = "JPEG", quality: int = 90) -> bytes:
    """Encode a PIL Image back to bytes (for storage or response)."""
    buf = io.BytesIO()
    image.save(buf, format=fmt, quality=quality)
    return buf.getvalue()
