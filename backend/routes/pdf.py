from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
import json

from db.database import get_db
from db import crud
from db.models import DocumentChunk
from services.pdf_service import extract_text_from_pdf, chunk_text, save_uploaded_file
from services.retrieval_service import embed_texts

router = APIRouter(prefix="/api/pdf", tags=["pdf"])

MAX_PDF_SIZE = 20 * 1024 * 1024  # 20 MB


@router.post("/upload")
async def upload_pdf(
    session_id: str = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    content = await file.read()
    if len(content) > MAX_PDF_SIZE:
        raise HTTPException(status_code=413, detail="File too large. Maximum size is 20 MB.")

    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    # Ensure session exists
    await crud.get_or_create_session(db, session_id)

    # Save to disk
    file_path = await save_uploaded_file(file.filename, content)

    # Create document record
    doc = await crud.create_document(db, session_id, file.filename, file_path)

    # Extract text
    raw_text = await extract_text_from_pdf(file_path)
    if not raw_text.strip():
        raise HTTPException(
            status_code=422,
            detail="Could not extract text from this PDF. It may be scanned or image-based."
        )

    # Chunk the text
    chunks = chunk_text(raw_text)
    if not chunks:
        raise HTTPException(status_code=422, detail="Could not create text chunks from the PDF.")

    # Generate embeddings
    embeddings = await embed_texts(chunks)

    # Store chunks
    db_chunks = []
    for i, (chunk_text_val, emb) in enumerate(zip(chunks, embeddings or [None] * len(chunks))):
        db_chunks.append(
            DocumentChunk(
                document_id=doc.id,
                session_id=session_id,
                chunk_index=i,
                content=chunk_text_val,
                embedding=json.dumps(emb) if emb else None,
            )
        )

    await crud.add_chunks(db, db_chunks)
    await crud.update_document_chunks(db, doc.id, len(db_chunks))

    return {
        "document_id": doc.id,
        "filename": file.filename,
        "chunk_count": len(db_chunks),
        "message": f"✅ PDF processed successfully! {len(db_chunks)} sections indexed. You can now ask questions about this document.",
    }


@router.get("/documents/{session_id}")
async def list_documents(session_id: str, db: AsyncSession = Depends(get_db)):
    docs = await crud.get_documents_for_session(db, session_id)
    return {
        "documents": [
            {
                "id": d.id,
                "filename": d.filename,
                "chunk_count": d.chunk_count,
                "uploaded_at": d.uploaded_at.isoformat(),
            }
            for d in docs
        ]
    }
