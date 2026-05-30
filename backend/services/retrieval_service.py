import os
import json
import asyncio
import logging
import numpy as np
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
TOP_K = int(os.getenv("TOP_K_CHUNKS", "3"))

_encoder = None
_encoder_lock = asyncio.Lock()


async def get_encoder():
    global _encoder
    if _encoder is not None:
        return _encoder
    async with _encoder_lock:
        if _encoder is not None:
            return _encoder
        try:
            from sentence_transformers import SentenceTransformer
            loop = asyncio.get_event_loop()
            _encoder = await loop.run_in_executor(
                None,
                lambda: SentenceTransformer(EMBEDDING_MODEL)
            )
            logger.info(f"Loaded embedding model: {EMBEDDING_MODEL}")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            _encoder = None
    return _encoder


async def embed_texts(texts: List[str]) -> Optional[List[List[float]]]:
    """Embed a list of texts and return their embeddings."""
    if not texts:
        return []
    try:
        encoder = await get_encoder()
        if encoder is None:
            return None
        loop = asyncio.get_event_loop()
        embeddings = await loop.run_in_executor(
            None,
            lambda: encoder.encode(texts, show_progress_bar=False).tolist()
        )
        return embeddings
    except Exception as e:
        logger.error(f"Embedding error: {e}")
        return None


def cosine_similarity(a: List[float], b: List[float]) -> float:
    """Compute cosine similarity between two vectors."""
    a_arr = np.array(a, dtype=np.float32)
    b_arr = np.array(b, dtype=np.float32)
    dot = np.dot(a_arr, b_arr)
    norm_a = np.linalg.norm(a_arr)
    norm_b = np.linalg.norm(b_arr)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(dot / (norm_a * norm_b))


async def retrieve_relevant_chunks(
    query: str,
    chunks_with_embeddings: List[Tuple[str, str]],  # (content, embedding_json)
    top_k: int = TOP_K,
) -> List[str]:
    """Retrieve the most relevant chunks for a query."""
    if not chunks_with_embeddings:
        return []

    try:
        # Embed the query
        query_embeddings = await embed_texts([query])
        if not query_embeddings:
            # Fallback: keyword matching
            return _keyword_fallback(query, [c for c, _ in chunks_with_embeddings], top_k)

        query_vec = query_embeddings[0]

        # Score each chunk
        scored = []
        for content, emb_json in chunks_with_embeddings:
            if emb_json:
                chunk_vec = json.loads(emb_json)
                score = cosine_similarity(query_vec, chunk_vec)
            else:
                score = 0.0
            scored.append((score, content))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [content for _, content in scored[:top_k] if _ > 0.1]

    except Exception as e:
        logger.error(f"Retrieval error: {e}")
        return _keyword_fallback(query, [c for c, _ in chunks_with_embeddings], top_k)


def _keyword_fallback(query: str, chunks: List[str], top_k: int) -> List[str]:
    """Simple keyword-based fallback retrieval."""
    query_words = set(query.lower().split())
    scored = []
    for chunk in chunks:
        chunk_words = set(chunk.lower().split())
        overlap = len(query_words & chunk_words)
        scored.append((overlap, chunk))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [c for _, c in scored[:top_k] if _ > 0]
