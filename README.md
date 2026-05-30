# StudyMate AI
An AI-powered study assistant with rule-based responses, PDF Q&A, and conversation history.

# Setup
bashcd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# What it does
Rule engine — instant answers for: hello, study tips, exam tips, productivity tips, help, about
AI chat — Flan-T5 answers any other question
PDF Q&A — upload a PDF, then ask questions about it
Chat history — all sessions saved in SQLite

# Stack
FastAPI · SQLite · HuggingFace Transformers · Sentence Transformers · pdfplumber