from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
import json

from db.database import get_db
from db import crud
from services.rule_engine import match_rule
from services.ai_service import generate_ai_response
from services.retrieval_service import retrieve_relevant_chunks
from services.memory_service import (
    build_conversation_history,
    generate_session_title,
    format_context_from_chunks,
)

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatRequest(BaseModel):
    session_id: str
    message: str


class ChatResponse(BaseModel):
    session_id: str
    response: str
    response_type: str  # rule | ai | pdf
    sources: list[str] = []


@router.post("/message", response_model=ChatResponse)
async def send_message(req: ChatRequest, db: AsyncSession = Depends(get_db)):
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    # Ensure session exists
    session = await crud.get_or_create_session(db, req.session_id)

    # Save user message
    await crud.add_message(db, req.session_id, "user", req.message, "user")

    # Auto-title the session from the first message
    messages = await crud.get_messages(db, req.session_id)
    if len(messages) == 1:
        title = generate_session_title(req.message)
        await crud.update_session_title(db, req.session_id, title)

    # ── Step 1: Rule Engine ────────────────────────────────────────────────────
    rule = match_rule(req.message)
    if rule:
        response_text = rule["response"]
        response_type = "rule"
        sources = []

    else:
        # ── Step 2: Check for PDF context ─────────────────────────────────────
        db_chunks = await crud.get_chunks_for_session(db, req.session_id)
        context = None
        sources = []

        if db_chunks:
            chunks_with_embeddings = [
                (chunk.content, chunk.embedding) for chunk in db_chunks
            ]
            relevant_chunks = await retrieve_relevant_chunks(
                req.message, chunks_with_embeddings
            )
            if relevant_chunks:
                context = format_context_from_chunks(relevant_chunks)
                sources = [chunk[:120] + "…" if len(chunk) > 120 else chunk for chunk in relevant_chunks]
                response_type = "pdf"
            else:
                response_type = "ai"
        else:
            response_type = "ai"

        # ── Step 3: AI Response ────────────────────────────────────────────────
        history = build_conversation_history(messages)
        response_text = await generate_ai_response(
            req.message,
            context=context,
            conversation_history=history,
        )

    # Save assistant response
    await crud.add_message(db, req.session_id, "assistant", response_text, response_type)
    await crud.touch_session(db, req.session_id)

    return ChatResponse(
        session_id=req.session_id,
        response=response_text,
        response_type=response_type,
        sources=sources,
    )


@router.get("/history/{session_id}")
async def get_chat_history(session_id: str, db: AsyncSession = Depends(get_db)):
    messages = await crud.get_messages(db, session_id)
    return {
        "session_id": session_id,
        "messages": [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "response_type": m.response_type,
                "created_at": m.created_at.isoformat(),
            }
            for m in messages
        ],
    }
