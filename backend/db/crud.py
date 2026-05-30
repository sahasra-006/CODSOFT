from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, desc
from sqlalchemy.orm import selectinload
from datetime import datetime
from typing import List, Optional
import uuid

from db.models import ChatSession, Message, Document, DocumentChunk


# ── Sessions ──────────────────────────────────────────────────────────────────

async def create_session(db: AsyncSession, title: str = "New Chat") -> ChatSession:
    session_id = str(uuid.uuid4())
    session = ChatSession(session_id=session_id, title=title)
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


async def get_session(db: AsyncSession, session_id: str) -> Optional[ChatSession]:
    result = await db.execute(
        select(ChatSession).where(ChatSession.session_id == session_id)
    )
    return result.scalar_one_or_none()


async def get_or_create_session(db: AsyncSession, session_id: str) -> ChatSession:
    session = await get_session(db, session_id)
    if not session:
        session = ChatSession(session_id=session_id, title="New Chat")
        db.add(session)
        await db.commit()
        await db.refresh(session)
    return session


async def list_sessions(db: AsyncSession, limit: int = 50) -> List[ChatSession]:
    result = await db.execute(
        select(ChatSession)
        .options(selectinload(ChatSession.documents))
        .order_by(desc(ChatSession.updated_at))
        .limit(limit)
    )
    return result.scalars().all()


async def update_session_title(db: AsyncSession, session_id: str, title: str):
    await db.execute(
        update(ChatSession)
        .where(ChatSession.session_id == session_id)
        .values(title=title, updated_at=datetime.utcnow())
    )
    await db.commit()


async def touch_session(db: AsyncSession, session_id: str):
    await db.execute(
        update(ChatSession)
        .where(ChatSession.session_id == session_id)
        .values(updated_at=datetime.utcnow())
    )
    await db.commit()


async def delete_session(db: AsyncSession, session_id: str):
    await db.execute(delete(ChatSession).where(ChatSession.session_id == session_id))
    await db.commit()


# ── Messages ──────────────────────────────────────────────────────────────────

async def add_message(
    db: AsyncSession,
    session_id: str,
    role: str,
    content: str,
    response_type: str = "ai",
) -> Message:
    msg = Message(
        session_id=session_id,
        role=role,
        content=content,
        response_type=response_type,
    )
    db.add(msg)
    await db.commit()
    await db.refresh(msg)
    return msg


async def get_messages(db: AsyncSession, session_id: str, limit: int = 100) -> List[Message]:
    result = await db.execute(
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.created_at)
        .limit(limit)
    )
    return result.scalars().all()


# ── Documents ─────────────────────────────────────────────────────────────────

async def create_document(
    db: AsyncSession,
    session_id: str,
    filename: str,
    file_path: str,
) -> Document:
    doc = Document(session_id=session_id, filename=filename, file_path=file_path)
    db.add(doc)
    await db.commit()
    await db.refresh(doc)
    return doc


async def update_document_chunks(db: AsyncSession, doc_id: int, chunk_count: int):
    await db.execute(
        update(Document).where(Document.id == doc_id).values(chunk_count=chunk_count)
    )
    await db.commit()


async def get_documents_for_session(db: AsyncSession, session_id: str) -> List[Document]:
    result = await db.execute(
        select(Document)
        .where(Document.session_id == session_id)
        .order_by(desc(Document.uploaded_at))
    )
    return result.scalars().all()


# ── Document Chunks ───────────────────────────────────────────────────────────

async def add_chunks(db: AsyncSession, chunks: List[DocumentChunk]):
    db.add_all(chunks)
    await db.commit()


async def get_chunks_for_session(db: AsyncSession, session_id: str) -> List[DocumentChunk]:
    result = await db.execute(
        select(DocumentChunk).where(DocumentChunk.session_id == session_id)
    )
    return result.scalars().all()
