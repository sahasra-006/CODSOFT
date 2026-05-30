import os
import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from fastapi.responses import HTMLResponse
from dotenv import load_dotenv

load_dotenv()

from db.database import init_db
from routes import chat, pdf, history

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting StudyMate AI…")
    await init_db()
    logger.info("Database initialized.")

    # Pre-warm models in background
    async def warm_models():
        await asyncio.sleep(2)
        try:
            from services.retrieval_service import get_encoder
            await get_encoder()
        except Exception as e:
            logger.warning(f"Encoder warm-up skipped: {e}")
        try:
            from services.ai_service import get_pipeline
            await get_pipeline()
        except Exception as e:
            logger.warning(f"AI pipeline warm-up skipped: {e}")

    asyncio.create_task(warm_models())

    yield
    logger.info("StudyMate AI shutting down.")


app = FastAPI(
    title="StudyMate AI",
    description="AI-powered study assistant with rule-based responses and PDF Q&A",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files and templates
frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")
static_dir = os.path.join(frontend_dir, "static")
templates_dir = os.path.join(frontend_dir, "templates")

if os.path.isdir(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

templates = Jinja2Templates(directory=templates_dir)

# Routers
app.include_router(chat.router)
app.include_router(pdf.router)
app.include_router(history.router)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/health")
async def health():
    return {"status": "ok", "service": "StudyMate AI"}
