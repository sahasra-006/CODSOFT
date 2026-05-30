import os
import re
from typing import List, Optional, Tuple
import pdfplumber
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# In-memory cache: pdf_id -> (chunks, vectorizer, tfidf_matrix)
_pdf_cache: dict = {}


def extract_text_from_pdf(filepath: str) -> str:
    """Extract all text from a PDF file using pdfplumber."""
    text = ""
    try:
        with pdfplumber.open(filepath) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        # Fallback to PyPDF2
        try:
            import PyPDF2
            with open(filepath, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e2:
            raise RuntimeError(f"Failed to extract PDF text: {e2}")
    return text.strip()


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """Split text into overlapping chunks for better retrieval."""
    # Clean text
    text = re.sub(r'\s+', ' ', text).strip()
    
    words = text.split()
    chunks = []
    
    if len(words) <= chunk_size:
        return [text]
    
    start = 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk = ' '.join(words[start:end])
        chunks.append(chunk)
        if end == len(words):
            break
        start += chunk_size - overlap
    
    return chunks


def build_index(pdf_id: int, chunks: List[str]):
    """Build TF-IDF index for a set of text chunks."""
    vectorizer = TfidfVectorizer(
        stop_words='english',
        max_features=10000,
        ngram_range=(1, 2)
    )
    tfidf_matrix = vectorizer.fit_transform(chunks)
    _pdf_cache[pdf_id] = (chunks, vectorizer, tfidf_matrix)


def retrieve_relevant_chunks(pdf_id: int, query: str, top_k: int = 3) -> List[str]:
    """Retrieve the most relevant chunks for a query using TF-IDF cosine similarity."""
    if pdf_id not in _pdf_cache:
        return []
    
    chunks, vectorizer, tfidf_matrix = _pdf_cache[pdf_id]
    
    try:
        query_vec = vectorizer.transform([query])
        similarities = cosine_similarity(query_vec, tfidf_matrix).flatten()
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        relevant = []
        for idx in top_indices:
            if similarities[idx] > 0.01:  # Minimum relevance threshold
                relevant.append(chunks[idx])
        
        return relevant if relevant else chunks[:top_k]
    except Exception:
        return chunks[:top_k]


def load_pdf_into_cache(pdf_id: int, filepath: str) -> int:
    """Extract text from PDF, chunk it, and build TF-IDF index. Returns chunk count."""
    if pdf_id in _pdf_cache:
        return len(_pdf_cache[pdf_id][0])
    
    text = extract_text_from_pdf(filepath)
    if not text:
        raise ValueError("Could not extract text from PDF. The file may be scanned or image-based.")
    
    chunks = chunk_text(text)
    build_index(pdf_id, chunks)
    return len(chunks)


def get_pdf_context(pdf_id: int, filepath: str, query: str) -> Optional[str]:
    """Get relevant context from a PDF for a query."""
    # Load into cache if not already loaded
    if pdf_id not in _pdf_cache:
        load_pdf_into_cache(pdf_id, filepath)
    
    chunks = retrieve_relevant_chunks(pdf_id, query, top_k=3)
    if not chunks:
        return None
    
    context = "\n\n---\n\n".join(chunks)
    return context


def clear_pdf_cache(pdf_id: int):
    """Remove a PDF from the cache."""
    if pdf_id in _pdf_cache:
        del _pdf_cache[pdf_id]
