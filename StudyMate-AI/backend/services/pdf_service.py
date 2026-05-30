import os
import re
import asyncio
import logging
from typing import List, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
MAX_CHUNK_SIZE = int(os.getenv("MAX_CHUNK_SIZE", "500"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "50"))

Path(UPLOAD_DIR).mkdir(parents=True, exist_ok=True)


async def extract_text_from_pdf(file_path: str) -> str:
    """Extract all text from a PDF file using pdfplumber."""
    def _extract():
        try:
            import pdfplumber
            pages_text = []
            with pdfplumber.open(file_path) as pdf:
                for i, page in enumerate(pdf.pages):
                    text = page.extract_text()
                    if text:
                        pages_text.append(f"[Page {i+1}]\n{text}")
            return "\n\n".join(pages_text)
        except Exception as e:
            logger.error(f"PDF extraction error: {e}")
            return ""

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _extract)


def chunk_text(text: str, chunk_size: int = MAX_CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    """Split text into overlapping chunks."""
    if not text.strip():
        return []

    # Clean text
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r" {2,}", " ", text)

    # Split by paragraphs first
    paragraphs = [p.strip() for p in re.split(r"\n\n+", text) if p.strip()]

    chunks = []
    current_chunk = []
    current_size = 0

    for para in paragraphs:
        words = para.split()
        para_size = len(words)

        if current_size + para_size <= chunk_size:
            current_chunk.append(para)
            current_size += para_size
        else:
            if current_chunk:
                chunks.append(" ".join(current_chunk))

            # Handle paragraphs larger than chunk_size
            if para_size > chunk_size:
                words_list = para.split()
                for i in range(0, len(words_list), chunk_size - overlap):
                    chunk_words = words_list[i: i + chunk_size]
                    chunks.append(" ".join(chunk_words))
                current_chunk = []
                current_size = 0
            else:
                # Start new chunk with overlap
                if chunks:
                    prev_words = chunks[-1].split()[-overlap:]
                    current_chunk = [" ".join(prev_words), para]
                    current_size = overlap + para_size
                else:
                    current_chunk = [para]
                    current_size = para_size

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return [c for c in chunks if c.strip()]


async def save_uploaded_file(filename: str, content: bytes) -> str:
    """Save uploaded file to disk and return the path."""
    safe_name = re.sub(r"[^\w\-_\. ]", "_", filename)
    file_path = os.path.join(UPLOAD_DIR, safe_name)

    # Handle duplicate filenames
    base, ext = os.path.splitext(file_path)
    counter = 1
    while os.path.exists(file_path):
        file_path = f"{base}_{counter}{ext}"
        counter += 1

    def _write():
        with open(file_path, "wb") as f:
            f.write(content)

    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _write)
    return file_path
