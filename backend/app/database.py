"""
Async SQLAlchemy engine & session factory.

Usage:
    from app.database import get_session

    @router.get("/items")
    async def list_items(session: AsyncSession = Depends(get_session)) -> ...:
        ...
"""

from __future__ import annotations

import logging
import re
from collections.abc import AsyncGenerator
from urllib.parse import urlparse, urlunparse

from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.compiler import compiles

@compiles(JSONB, "sqlite")
def _compile_jsonb_sqlite(type_: JSONB, compiler: object, **kw: object) -> str:
    return "JSON"

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import settings

logger = logging.getLogger(__name__)

_DEFAULT_PG_PORT = 5432


def _sanitise_database_url(raw_url: str) -> str:
    """Ensure the database URL has a valid port (default 5432) and log it masked."""
    if raw_url.startswith("sqlite"):
        return raw_url

    parsed = urlparse(raw_url)

    # Fix missing or empty port for postgres URLs
    port = parsed.port
    if port is None and parsed.scheme.startswith("postgres"):
        # urlparse returns None when port is absent or empty-string.
        # Reconstruct netloc with default port.
        # Also handle the edge-case where the raw URL contains ":<empty>/"
        # e.g. "postgresql+asyncpg://user:pw@host:/db"
        hostname = parsed.hostname or "localhost"
        user_info = ""
        if parsed.username:
            pwd_part = f":{parsed.password}" if parsed.password else ""
            user_info = f"{parsed.username}{pwd_part}@"
        netloc = f"{user_info}{hostname}:{_DEFAULT_PG_PORT}"
        parsed = parsed._replace(netloc=netloc)
        logger.warning(
            "DATABASE_URL had no port — defaulting to %d", _DEFAULT_PG_PORT
        )

    # Build a masked version for logging (hide password)
    final_url: str = str(urlunparse(parsed))
    safe_url = re.sub(
        r"://([^:]+):([^@]+)@",
        r"://\1:****@",
        final_url,
    )
    logger.info("Database URL (masked): %s", safe_url)

    return final_url


_database_url = _sanitise_database_url(settings.database_url)

engine: AsyncEngine = create_async_engine(
    _database_url,
    echo=settings.debug,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)

async_session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an ``AsyncSession`` and closes it after use."""
    async with async_session_factory() as session:
        yield session
