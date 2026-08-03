"""
Universal Image Analysis Pipeline — FastAPI Application Entry Point.

Configures CORS, mounts static file serving for temp uploads,
registers API routers, and provides health check endpoint.
"""

import os
import shutil
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.config import get_settings
from backend.api.upload import router as upload_router
from backend.api.chat import router as chat_router
from backend.models.schemas import HealthResponse
from backend.services.session_manager import session_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler: startup and shutdown logic."""
    settings = get_settings()

    # Startup: ensure temp directory exists
    settings.upload_path.mkdir(parents=True, exist_ok=True)
    print(f"✅ Upload directory ready: {settings.upload_path}")
    print(f"✅ Triage model: {settings.TRIAGE_MODEL}")
    print(f"✅ Master VLM model: {settings.MASTER_VLM_MODEL}")

    if not settings.GEMINI_API_KEY or settings.GEMINI_API_KEY == "your_gemini_api_key_here":
        print("⚠️  WARNING: GEMINI_API_KEY not set! Set it in .env file.")
    else:
        print("✅ Gemini API key configured")

    yield

    # Shutdown: cleanup expired sessions and optionally clear temp
    session_manager.cleanup_expired()
    print("🧹 Cleanup complete. Server shutting down.")


# ── App Instance ────────────────────────────────────────────────────

app = FastAPI(
    title="Universal Image Analysis Pipeline",
    description=(
        "Enterprise-grade Compound AI System for analysing medical scans, "
        "UI screenshots, documents, charts, and everyday photographs."
    ),
    version="1.0.0",
    lifespan=lifespan,
)


# ── CORS ────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Static Files (temp uploads & thumbnails) ────────────────────────

settings = get_settings()
settings.upload_path.mkdir(parents=True, exist_ok=True)
app.mount("/temp", StaticFiles(directory=str(settings.upload_path)), name="temp")


# ── Routers ─────────────────────────────────────────────────────────

app.include_router(upload_router, prefix="/api", tags=["Upload"])
app.include_router(chat_router, prefix="/api", tags=["Chat"])


# ── Health Check ────────────────────────────────────────────────────

@app.get("/api/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Check if the API is running and pipeline is ready."""
    settings = get_settings()
    api_key_set = bool(settings.GEMINI_API_KEY and settings.GEMINI_API_KEY != "your_gemini_api_key_here")
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        pipeline_ready=api_key_set,
    )
