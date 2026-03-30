"""NeuroNote AI - FastAPI Application Entry Point"""

from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.config import settings
from app.database import async_session, init_db
from app.routes import notes, transcribe, export


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize services on startup."""
    await init_db()
    yield


app = FastAPI(
    title="NeuroNote AI",
    description="AI-powered voice-to-structured-notes system",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS
# Allow local frontend dev servers on localhost/127.0.0.1 with any port.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
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
        status["components"]["database"] = "error"
        status["status"] = "degraded"
        status["db_error"] = str(exc)

    # Ollama check (fast, non-streaming)
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(f"{settings.ollama_base_url}/api/version")
            resp.raise_for_status()
        status["components"]["ollama"] = "ok"
    except Exception as exc:
        status["components"]["ollama"] = "error"
        status["status"] = "degraded"
        status["ollama_error"] = str(exc)

    return status
