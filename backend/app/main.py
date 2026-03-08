"""
FastAPI application entry-point.

Run locally:
    uvicorn app.main:app --reload --port 8000
"""

import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text
from sqlmodel import SQLModel

from app.config import settings
from app.database import engine
from app.models import *  # noqa: F401,F403  — register all table models with SQLModel metadata
from app.routers import admin, articles, comments, config, inquiries, posts
from app.schemas.common import HealthResponse, ReadinessResponse
from app.services import limiter

logger: logging.Logger = logging.getLogger(__name__)

_DB_CONNECT_RETRIES = 5
_DB_CONNECT_BACKOFF_BASE = 2.0  # seconds


# ── Lifespan ──────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Startup / shutdown lifecycle hook.

    DB connectivity is verified but failure is **non-fatal** so that the
    liveness probe (/api/health) can still pass.  Use the readiness probe
    (/api/ready) to gate traffic until the DB is actually reachable.
    """
    # Best-effort DB connectivity check with retries
    db_connected = False
    for attempt in range(1, _DB_CONNECT_RETRIES + 1):
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            logger.info("✅ Database connection verified (attempt %d)", attempt)
            db_connected = True
            break
        except Exception as exc:
            wait = _DB_CONNECT_BACKOFF_BASE ** attempt
            logger.warning(
                "⏳ Database connection attempt %d/%d failed: %s — retrying in %.1fs",
                attempt,
                _DB_CONNECT_RETRIES,
                exc,
                wait,
            )
            if attempt < _DB_CONNECT_RETRIES:
                await asyncio.sleep(wait)

    if db_connected:
        # Auto-create tables if they don't exist (idempotent).
        # Wrapped in try/except because PostgreSQL may already have
        # types or tables that collide (e.g. UniqueViolationError on
        # pg_type_typname_nsp_index).  In production use Alembic instead.
        try:
            async with engine.begin() as conn:
                await conn.run_sync(SQLModel.metadata.create_all)
            logger.info("✅ Database tables ensured")
        except Exception as exc:
            logger.warning(
                "⚠️ create_all partial failure (tables/types may already exist): %s",
                exc,
            )
    else:
        # Log but do NOT raise — let the app start so the health-check passes.
        logger.error(
            "❌ Database connection failed after %d attempts. "
            "App will start but /api/ready will report unhealthy.",
            _DB_CONNECT_RETRIES,
        )

    yield  # ← app is running

    # Shutdown: dispose engine connection pool
    await engine.dispose()
    logger.info("Database engine disposed")


# ── App instance ──────────────────────────────────────────────
app: FastAPI = FastAPI(
    title="Moku API",
    version="0.1.0",
    lifespan=lifespan,
    # Disable docs in production for security
    docs_url="/api/docs" if settings.debug else None,
    redoc_url="/api/redoc" if settings.debug else None,
    openapi_url="/api/openapi.json" if settings.debug else None,
)

# ── SlowAPI (rate limiting) ───────────────────────────────────
app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """Return a JSON 429 with a Japanese message."""
    return JSONResponse(
        status_code=429,
        content={"error": "リクエストが多すぎます。しばらくしてからもう一度お試しください。"},
    )


# ── CORS middleware ───────────────────────────────────────────
# Restricted to allowed origins defined in settings (env var CORS_ORIGINS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "Origin", "X-Requested-With"],
)


# ── Routers ───────────────────────────────────────────────────
app.include_router(posts.router)
app.include_router(comments.router)
app.include_router(inquiries.router)
app.include_router(articles.router)
app.include_router(admin.router)
app.include_router(config.router)


# ── Health check (liveness probe) ────────────────────────────
@app.get("/api/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Simple liveness probe — returns 200 if server is running."""
    return HealthResponse(status="ok")


# ── Readiness check (readiness probe) ────────────────────────
@app.get("/api/ready", response_model=ReadinessResponse)
async def readiness_check() -> ReadinessResponse:
    """Readiness probe — verifies DB connectivity before accepting traffic."""
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return ReadinessResponse(status="ready", db="ok")
    except Exception as exc:
        logger.error("Readiness check failed: %s", exc)
        raise HTTPException(
            status_code=503,
            detail="Database is unreachable",
        ) from exc
