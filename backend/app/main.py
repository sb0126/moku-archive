"""
FastAPI application entry-point.

Run locally:
    uvicorn app.main:app --reload --port 8000
"""

import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from alembic import command as alembic_command
from alembic.config import Config as AlembicConfig
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text
from sqlmodel import SQLModel

from app.config import settings
from app.database import engine
from app.middleware import CacheHeaderMiddleware
from app.models import *  # noqa: F401,F403  — register all table models with SQLModel metadata
from app.routers import admin, articles, comments, config, inquiries, posts
from app.schemas.common import HealthResponse, ReadinessResponse
from app.sentry import init_sentry
from app.services import limiter

logger: logging.Logger = logging.getLogger(__name__)

# ── Sentry (must run before FastAPI app is created) ───────────
init_sentry()

_DB_CONNECT_RETRIES = 5
_DB_CONNECT_BACKOFF_BASE = 2.0  # seconds


def _run_alembic_upgrade() -> None:
    """Run Alembic migrations to 'head' (synchronous, called once at startup).

    Auto-detects pre-existing databases:
      - If tables exist but alembic_version does NOT → stamp head (baseline)
      - Otherwise → upgrade head (apply pending migrations)
    """
    import os

    from sqlalchemy import create_engine, inspect, text as sa_text

    ini_path = os.path.join(os.path.dirname(__file__), "..", "alembic.ini")
    alembic_cfg = AlembicConfig(ini_path)
    alembic_cfg.set_main_option(
        "script_location",
        os.path.join(os.path.dirname(__file__), "..", "alembic"),
    )

    # Build a sync URL for the inspection check
    # .strip() removes trailing newlines that some PaaS providers inject
    sync_url = settings.database_url.replace(
        "postgresql+asyncpg://", "postgresql://"
    ).replace(
        "sqlite+aiosqlite://", "sqlite://"
    ).strip()
    sync_engine = create_engine(sync_url)

    try:
        inspector = inspect(sync_engine)
        existing_tables = set(inspector.get_table_names())
        has_alembic = "alembic_version" in existing_tables
        has_app_tables = bool(existing_tables & {"posts", "articles", "comments", "inquiries"})

        if has_app_tables and not has_alembic:
            # Pre-existing DB without Alembic tracking → stamp as baseline
            logger.info("🔖 Existing DB detected without alembic_version — stamping head")
            alembic_command.stamp(alembic_cfg, "head")
        else:
            # Normal path: apply any pending migrations
            alembic_command.upgrade(alembic_cfg, "head")
    finally:
        sync_engine.dispose()


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
        # Run Alembic migrations (replaces old create_all approach)
        try:
            _run_alembic_upgrade()
            logger.info("✅ Alembic migrations applied (head)")
        except Exception as exc:
            logger.warning(
                "⚠️ Alembic migration failed: %s — tables may already be up-to-date",
                exc,
            )

        # Cleanup expired JWT blacklist entries on startup
        try:
            from app.services.cache import cleanup_expired_tokens

            cleaned = await cleanup_expired_tokens()
            if cleaned:
                logger.info("🧹 Cleaned up %d expired blacklist entries", cleaned)
        except Exception as exc:
            logger.debug("Blacklist cleanup skipped: %s", exc)
    else:
        # Log but do NOT raise — let the app start so the health-check passes.
        logger.warning(
            "⚠️ Database connection failed after %d attempts. "
            "App will start but /api/ready will report unhealthy.",
            _DB_CONNECT_RETRIES,
        )

    yield  # ← app is running

    # Shutdown: dispose engine
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


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all for unhandled errors — log + forward to Sentry."""
    import sentry_sdk  # type: ignore[import-untyped]

    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    sentry_sdk.capture_exception(exc)
    return JSONResponse(
        status_code=500,
        content={"error": "内部サーバーエラーが発生しました。"},
    )


# ── CORS middleware ───────────────────────────────────────────
# Restricted to allowed origins defined in settings (env var CORS_ORIGINS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "Origin", "X-Requested-With", "X-Admin-Token"],
)

# ── Cache-Control headers ─────────────────────────────────────
app.add_middleware(CacheHeaderMiddleware)


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


# ── Sentry debug (test endpoint) ─────────────────────────────
if settings.debug:

    @app.get("/sentry-debug")
    async def trigger_error() -> None:
        """Intentional error to verify Sentry integration."""
        division_by_zero = 1 / 0

