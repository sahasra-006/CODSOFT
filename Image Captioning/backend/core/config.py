"""
core/config.py
Central configuration for Image Captioning.
All tuneable values live here — nothing scattered across modules.
"""

# ── Model ────────────────────────────────────────────────────────────────────
# BLIP Base is the deliberate choice: faster inference, lower VRAM,
# stable deployment. Large adds marginal quality at significant cost.
MODEL_ID = "Salesforce/blip-image-captioning-base"

# Beam search: 3 balances quality and latency.
# 5-beam noticeably increases CPU wait; 1 (greedy) drops coherence.
NUM_BEAMS = 3
MAX_NEW_TOKENS = 100
REPETITION_PENALTY = 1.3

# ── Image preprocessing ──────────────────────────────────────────────────────
MAX_IMAGE_DIMENSION = 960        # px; resize longest edge if exceeded
SUPPORTED_FORMATS = {"JPEG", "PNG", "WEBP", "BMP", "GIF", "TIFF"}

# ── Upload limits ────────────────────────────────────────────────────────────
MAX_FILE_SIZE_MB = 10
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

# ── Caption styles ───────────────────────────────────────────────────────────
# Maps style key → BLIP conditional prompt prefix
STYLE_PROMPTS: dict[str, str] = {
    "descriptive": "a photo of",
    "cinematic":   "a cinematic still of",
    "poetic":      "a poetic vision of",
    "social":      "an instagram photo of",
    "documentary": "a documentary photograph of",
}

# Light post-processing appended after generation
STYLE_SUFFIXES: dict[str, str] = {
    "descriptive": "",
    "cinematic":   " — shot on 35mm film.",
    "poetic":      "",
    "social":      " ✨",
    "documentary": "",
}

VALID_STYLES = set(STYLE_PROMPTS.keys())

# ── Database ─────────────────────────────────────────────────────────────────
import os
DB_PATH = os.environ.get("DB_PATH", "image-captioning.db")
