"""
Image Captioning API
Entry point: mounts routes, serves frontend, initializes DB and model.
"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.routes.caption import router as caption_router
from backend.routes.history import router as history_router
from backend.core.inference import load_model
from backend.db.database import init_db
from backend.utils.logger import configure_logging, get_logger

configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: init DB and warm-up BLIP model."""
    logger.info("Image Captioning starting up …")
    init_db()
    load_model()
    logger.info("Startup complete — ready to serve requests.")
    yield
    logger.info("Image Captioning shutting down.")


app = FastAPI(
    title="Image Captioning",
    description="AI-powered image captioning with BLIP",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes
app.include_router(caption_router, prefix="/api")
app.include_router(history_router, prefix="/api")

# Static assets
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")
app.mount("/static", StaticFiles(directory=os.path.join(FRONTEND_DIR, "static")), name="static")


@app.get("/", include_in_schema=False)
async def serve_frontend():
    return FileResponse(os.path.join(FRONTEND_DIR, "templates", "index.html"))


@app.get("/health")
async def health():
    return {"status": "ok"}
