from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from backend.database import get_db
from backend.models import Message, ChatSession, UploadedPDF
from backend.schemas import ChatRequest, ChatResponse, MessageOut
from backend.rules import get_rule_response
from backend.ai_engine import generate_response
from backend.pdf_engine import get_pdf_context

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest, db: Session = Depends(get_db)):
    # Validate session
    session = db.query(ChatSession).filter(ChatSession.id == request.session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    message = request.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    
    # Save user message
    user_msg = Message(
        session_id=request.session_id,
        role="user",
        content=message,
        response_type=None
    )
    db.add(user_msg)
    db.commit()
    
    # 1. Check rule-based responses first
    rule_response = get_rule_response(message)
    if rule_response:
        assistant_msg = Message(
            session_id=request.session_id,
            role="assistant",
            content=rule_response,
            response_type="rule"
        )
        db.add(assistant_msg)
        db.commit()
        return ChatResponse(response=rule_response, type="rule")
    
    # 2. Check for active PDF and get context
    active_pdf = db.query(UploadedPDF).filter(UploadedPDF.is_active == True).first()
    pdf_context = None
    response_type = "ai"
    
    if active_pdf:
        try:
            pdf_context = get_pdf_context(active_pdf.id, active_pdf.filepath, message)
            if pdf_context:
                response_type = "pdf"
        except Exception as e:
            pass  # Fall through to normal AI response
    
    # 3. Build conversation history for context
    history_messages = (
        db.query(Message)
        .filter(Message.session_id == request.session_id)
        .order_by(Message.timestamp)
        .limit(20)
        .all()
    )
    
    history = [
        {"role": msg.role, "content": msg.content}
        for msg in history_messages
        if msg.role in ("user", "assistant")
    ]
    
    # 4. Generate AI response
    ai_response = generate_response(
        user_message=message,
        history=history,
        pdf_context=pdf_context
    )
    
    # Save assistant message
    assistant_msg = Message(
        session_id=request.session_id,
        role="assistant",
        content=ai_response,
        response_type=response_type
    )
    db.add(assistant_msg)
    db.commit()
    
    return ChatResponse(response=ai_response, type=response_type)


@router.get("/messages/{session_id}", response_model=List[MessageOut])
def get_messages(session_id: int, db: Session = Depends(get_db)):
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    messages = (
        db.query(Message)
        .filter(Message.session_id == session_id)
        .order_by(Message.timestamp)
        .all()
    )
    return messages
