"""NeuroNote AI - FastAPI Application Entry Point"""

import logging
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.config import settings
from app.database import async_session, init_db
from app.routes import notes, transcribe, export

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize services on startup."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    logger.info("Starting NeuroNote AI")
    await init_db()
    # Preload whisper model to avoid blocking the event loop on first request
    try:
        from app.services.whisper_service import get_whisper_model
        get_whisper_model()
        logger.info("Whisper model preloaded")
    except Exception as e:
        logger.warning(f"Could not preload whisper model: {e}")
    yield


app = FastAPI(
    title="NeuroNote AI",
    description="AI-powered voice-to-structured-notes system",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(transcribe.router, prefix="/api", tags=["Transcription"])
app.include_router(notes.router, prefix="/api", tags=["Notes"])
app.include_router(export.router, prefix="/api", tags=["Export"])


@app.get("/api/health")
async def health_check():
    """Lightweight health check that verifies DB and Ollama connectivity."""
    status = {"service": "NeuroNote AI", "status": "ok", "components": {}}

    # DB check
    try:
        async with async_session() as session:
            await session.execute(text("SELECT 1"))
        status["components"]["database"] = "ok"
    except Exception as exc:
        logger.error(f"Database health check failed: {exc}")
        status["components"]["database"] = "error"
        status["status"] = "degraded"

    # Ollama check (fast, non-streaming)
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(f"{settings.ollama_base_url}/api/version")
            resp.raise_for_status()
        status["components"]["ollama"] = "ok"
    except Exception as exc:
        logger.error(f"Ollama health check failed: {exc}")
        status["components"]["ollama"] = "error"
        status["status"] = "degraded"

    return status
