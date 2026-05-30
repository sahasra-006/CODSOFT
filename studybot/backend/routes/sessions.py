from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from backend.database import get_db
from backend.models import ChatSession
from backend.schemas import SessionCreate, SessionUpdate, SessionOut

router = APIRouter()


@router.get("/sessions", response_model=List[SessionOut])
def get_sessions(db: Session = Depends(get_db)):
    sessions = db.query(ChatSession).order_by(ChatSession.created_at.desc()).all()
    return sessions


@router.post("/sessions", response_model=SessionOut)
def create_session(data: SessionCreate, db: Session = Depends(get_db)):
    session = ChatSession(title=data.title)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.put("/sessions/{session_id}", response_model=SessionOut)
def update_session(session_id: int, data: SessionUpdate, db: Session = Depends(get_db)):
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    session.title = data.title
    db.commit()
    db.refresh(session)
    return session


@router.delete("/sessions/{session_id}")
def delete_session(session_id: int, db: Session = Depends(get_db)):
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    db.delete(session)
    db.commit()
    return {"detail": "Session deleted"}
