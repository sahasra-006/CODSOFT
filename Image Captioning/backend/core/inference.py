"""
core/inference.py
BLIP inference pipeline: model loading and caption generation.

Design decisions:
  - BLIP Base over Large: faster CPU inference, lower VRAM, stable deployment.
  - 3-beam search: meaningful quality improvement over greedy without
    the latency penalty of 5-beam, which becomes noticeable on CPU.
  - GPU auto-detected; falls back to CPU transparently.
"""

from typing import Optional
from PIL import Image

import torch
from transformers import BlipProcessor, BlipForConditionalGeneration

from backend.core.config import (
    MODEL_ID,
    NUM_BEAMS,
    MAX_NEW_TOKENS,
    REPETITION_PENALTY,
    STYLE_PROMPTS,
    STYLE_SUFFIXES,
)
from backend.utils.logger import get_logger, log_duration

logger = get_logger(__name__)

# ── Module-level singletons ───────────────────────────────────────────────────
_processor: Optional[BlipProcessor] = None
_model: Optional[BlipForConditionalGeneration] = None
_device: str = "cpu"


def load_model() -> None:
    """
    Load BLIP processor and model at application startup.
    GPU is used when available; CPU otherwise.
    Float16 on GPU reduces VRAM usage; float32 required on CPU.
    """
    global _processor, _model, _device

    _device = "cuda" if torch.cuda.is_available() else "cpu"
    dtype = torch.float16 if _device == "cuda" else torch.float32

    logger.info(f"Loading {MODEL_ID} on {_device.upper()} (dtype={dtype}) ...")

    _processor = BlipProcessor.from_pretrained(MODEL_ID)
    _model = BlipForConditionalGeneration.from_pretrained(
        MODEL_ID, torch_dtype=dtype
    ).to(_device)
    _model.eval()

    logger.info(f"Model ready — {_device.upper()}, beams={NUM_BEAMS}")


def get_device() -> str:
    return _device


@log_duration(logger, "BLIP caption generation")
def generate_caption(image: Image.Image, style: str = "descriptive") -> str:
    """
    Generate a caption for a PIL Image.

    Args:
        image: RGB PIL Image (pre-processed by preprocessing.py)
        style: Key from STYLE_PROMPTS; controls conditional generation prefix

    Returns:
        Post-processed caption string

    Raises:
        RuntimeError: if model has not been loaded
    """
    if _processor is None or _model is None:
        raise RuntimeError("Model not loaded. Call load_model() first.")

    prompt = STYLE_PROMPTS.get(style, STYLE_PROMPTS["descriptive"])

    inputs = _processor(
        images=image,
        text=prompt,
        return_tensors="pt",
    ).to(_device)

    with torch.no_grad():
        output_ids = _model.generate(
            **inputs,
            max_new_tokens=MAX_NEW_TOKENS,
            num_beams=NUM_BEAMS,
            early_stopping=True,
            repetition_penalty=REPETITION_PENALTY,
        )

    raw = _processor.decode(output_ids[0], skip_special_tokens=True)

    # BLIP sometimes echoes the prompt prefix; strip it if present
    if prompt and raw.lower().startswith(prompt.lower()):
        raw = raw[len(prompt):].strip()

    return _postprocess(raw, style)


# ── Post-processing ───────────────────────────────────────────────────────────

def _postprocess(caption: str, style: str) -> str:
    """Capitalise and apply style-specific suffix."""
    if not caption:
        return caption

    caption = caption[0].upper() + caption[1:]

    suffix = STYLE_SUFFIXES.get(style, "")
    if suffix and not caption.endswith(suffix.strip()):
        caption = caption.rstrip(".") + suffix

    return caption
