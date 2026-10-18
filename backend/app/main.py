"""Enterprise Knowledge Assistant — FastAPI application entry point.

Run with:
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.api.routes import router as api_router
from app.config import settings


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("eka")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup + shutdown hooks."""
    # Startup
    logger.info("Starting %s v%s", settings.app_name, settings.app_version)
    logger.info("Environment: %s", settings.environment)
    logger.info("Vector DB path: %s", settings.vector_db_path)
    logger.info("Embedding model: %s", settings.embedding_model)

    from app.rag.llm import llm_provider_name
    logger.info("LLM provider: %s", llm_provider_name())

    # Auto-seed sample docs on first run
    from app.ingestion.ingest import seed_sample_docs
    from app.rag.vectorstore import count_chunks

    total_chunks = sum(count_chunks(a) for a in ["hr", "it", "policy"])
    if total_chunks == 0:
        logger.info("Vector DB is empty — seeding sample documents...")
        try:
            results = seed_sample_docs()
            seeded = len([r for r in results if "error" not in r])
            logger.info("Seeded %d sample documents", seeded)
        except Exception as e:
            logger.warning("Auto-seed failed: %s. Run /api/seed manually.", e)
    else:
        logger.info("Vector DB already has %d chunks (skipping seed)", total_chunks)

    yield

    # Shutdown
    logger.info("Shutting down %s", settings.app_name)


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "Enterprise Knowledge Assistant backend — RAG + multi-agent. "
        "Phase 2: Python + FastAPI + LangChain + Chroma."
    ),
    lifespan=lifespan,
)


# CORS — allow the GitHub Pages frontend and local dev
origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Mount API routes under /api
app.include_router(api_router)


# Serve the frontend (Phase 1 static files) at root
# This lets you run the whole stack from one origin during local dev.
FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent
if FRONTEND_DIR.exists():
    app.mount("/app", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")


@app.get("/")
async def root():
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
        "frontend": "/app/",
        "api": "/api/health",
    }
