"""
routes/history.py
GET  /api/history          — paginated caption history
GET  /api/history/{id}     — single caption record
DELETE /api/history/{id}   — delete a record
GET  /api/history/{id}/download — download caption as .txt
"""

import logging
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import PlainTextResponse, JSONResponse

from backend.db.crud import fetch_history, fetch_caption, delete_caption

logger = logging.getLogger(__name__)
router = APIRouter(tags=["history"])


@router.get("/history")
async def get_history(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    records = fetch_history(limit=limit, offset=offset)
    return JSONResponse({"items": records, "count": len(records)})


@router.get("/history/{caption_id}")
async def get_caption(caption_id: int):
    record = fetch_caption(caption_id)
    if not record:
        raise HTTPException(status_code=404, detail="Caption not found.")
    return JSONResponse(record)


@router.delete("/history/{caption_id}")
async def remove_caption(caption_id: int):
    deleted = delete_caption(caption_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Caption not found.")
    return JSONResponse({"deleted": True, "id": caption_id})


@router.get("/history/{caption_id}/download")
async def download_caption(caption_id: int):
    """Return the caption as a plain-text file download."""
    record = fetch_caption(caption_id)
    if not record:
        raise HTTPException(status_code=404, detail="Caption not found.")

    content = (
        f"Image Captioning\n"
        f"{'='*40}\n"
        f"File     : {record['filename']}\n"
        f"Style    : {record['style'].capitalize()}\n"
        f"Created  : {record['created_at']}\n"
        f"Device   : {record['device'].upper()}\n"
        f"{'='*40}\n\n"
        f"{record['caption']}\n"
    )

    safe_name = record["filename"].rsplit(".", 1)[0].replace(" ", "_")
    headers = {
        "Content-Disposition": f'attachment; filename="{safe_name}_caption.txt"'
    }
    return PlainTextResponse(content, headers=headers)
