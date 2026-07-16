"""
PatentPilot FastAPI Application.

Entry point for the backend server.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.models.database import init_db, close_db
from app.routes.api import router as api_router

# ---------------------------------------------------------------------------
# Logging configuration
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Lifespan (startup / shutdown)
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown events."""
    logger.info("PatentPilot API starting up …")
    logger.info(
        "Gemini configuration: key_present=%s, model=%s",
        bool(settings.GEMINI_API_KEY and settings.GEMINI_API_KEY.strip()),
        settings.GEMINI_MODEL,
    )
    await init_db()
    yield
    logger.info("PatentPilot API shutting down …")
    await close_db()


# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------
app = FastAPI(
    title="PatentPilot API",
    description=(
        "AI-powered patent landscape analysis for pharmaceutical compounds. "
        "Submit a SMILES string and receive a comprehensive risk assessment "
        "with supporting evidence and AI-generated explanations."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow Next.js dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(api_router)


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@app.get("/health", tags=["health"])
async def health_check():
    """Basic health / readiness probe."""
    return {"status": "healthy", "service": "PatentPilot API", "version": "1.0.0"}
