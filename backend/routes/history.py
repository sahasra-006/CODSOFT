from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from db.database import get_db
from db import crud

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


class CreateSessionRequest(BaseModel):
    title: str = "New Chat"


@router.post("/")
async def create_session(req: CreateSessionRequest, db: AsyncSession = Depends(get_db)):
    session = await crud.create_session(db, req.title)
    return {
        "session_id": session.session_id,
        "title": session.title,
        "created_at": session.created_at.isoformat(),
    }


@router.get("/")
async def list_sessions(db: AsyncSession = Depends(get_db)):
    sessions = await crud.list_sessions(db)
    return {
        "sessions": [
            {
                "session_id": s.session_id,
                "title": s.title,
                "created_at": s.created_at.isoformat(),
                "updated_at": s.updated_at.isoformat(),
                "document_count": len(s.documents),
            }
            for s in sessions
        ]
    }


@router.delete("/{session_id}")
async def delete_session(session_id: str, db: AsyncSession = Depends(get_db)):
    session = await crud.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")
    await crud.delete_session(db, session_id)
    return {"message": "Session deleted successfully."}


@router.put("/{session_id}/title")
async def rename_session(
    session_id: str,
    body: dict,
    db: AsyncSession = Depends(get_db),
):
    title = body.get("title", "").strip()
    if not title:
        raise HTTPException(status_code=400, detail="Title cannot be empty.")
    await crud.update_session_title(db, session_id, title)
    return {"message": "Session renamed.", "title": title}
