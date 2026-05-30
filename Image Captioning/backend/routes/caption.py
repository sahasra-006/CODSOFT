"""
routes/caption.py
POST /api/caption — accepts an image file, returns a generated caption.
"""

from fastapi import APIRouter, File, Form, UploadFile, HTTPException
from fastapi.responses import JSONResponse

from backend.core.inference import generate_caption, get_device
from backend.core.preprocessing import preprocess_image
from backend.core.config import MAX_FILE_SIZE_BYTES, MAX_FILE_SIZE_MB, VALID_STYLES
from backend.db.crud import save_caption
from backend.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["caption"])


@router.post("/caption")
async def caption_image(
    file: UploadFile = File(..., description="Image to caption (JPEG, PNG, WebP, etc.)"),
    style: str = Form("descriptive", description="Caption style"),
):
    """
    Upload an image and receive an AI-generated caption.

    - **file**: image binary (≤ 10 MB)
    - **style**: one of descriptive | cinematic | poetic | social | documentary
    """
    # Validate style
    if style not in VALID_STYLES:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid style '{style}'. Choose from: {sorted(VALID_STYLES)}",
        )

    # Read & size-check
    file_bytes = await file.read()
    file_size_kb = len(file_bytes) / 1024

    if not file_bytes:
        logger.warning("Empty file received from upload")
        raise HTTPException(status_code=400, detail="Empty file received.")

    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        logger.warning(f"Upload rejected — file too large: {file_size_kb:.0f} KB")
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE_MB} MB.",
        )

    logger.info(f"Upload received — {file.filename!r}, {file_size_kb:.0f} KB, style={style!r}")

    # Preprocess — validates format, fixes orientation, normalises size
    try:
        image = preprocess_image(file_bytes)
    except ValueError as exc:
        logger.warning(f"Preprocessing failed for {file.filename!r}: {exc}")
        raise HTTPException(status_code=422, detail=str(exc))

    # Inference
    try:
        caption = generate_caption(image, style=style)
    except RuntimeError as exc:
        logger.error(f"Model not ready: {exc}")
        raise HTTPException(status_code=503, detail="Model not ready. Please retry in a moment.")
    except Exception as exc:
        logger.exception(f"Unexpected inference error for {file.filename!r}: {exc}")
        raise HTTPException(status_code=500, detail="Caption generation failed.")

    device = get_device()

    # Persist
    filename = file.filename or "upload.jpg"
    record = save_caption(filename=filename, style=style, caption=caption, device=device)

    return JSONResponse({
        "id": record["id"],
        "caption": caption,
        "style": style,
        "filename": filename,
        "device": device,
        "created_at": record["created_at"],
    })
