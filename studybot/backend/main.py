import logging
import os
from contextlib import asynccontextmanager
 
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
 
from backend.database import engine
from backend.models import Base
from backend.ai_engine import load_model
from backend.routes import chat, sessions, pdf
 
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)
 
 
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Loading AI model... (this may take a minute on first run)")
    success = load_model()
    if success:
        logger.info("✅ AI model ready.")
    else:
        logger.warning("⚠️ AI model failed to load. AI responses will be unavailable.")
    yield
    # Shutdown
    logger.info("Shutting down StudyBot.")
 
 
app = FastAPI(
    title="StudyBot API",
    description="AI-powered study assistant",
    version="1.0.0",
    lifespan=lifespan
)
 
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
 
# API routes
app.include_router(chat.router, prefix="/api", tags=["chat"])
app.include_router(sessions.router, prefix="/api", tags=["sessions"])
app.include_router(pdf.router, prefix="/api", tags=["pdf"])
 
# Serve frontend (main.py is inside backend/, so go up one level to project root)
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend")
FRONTEND_DIR = os.path.normpath(FRONTEND_DIR)
if os.path.exists(FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
 