"""Cache service — no-op stubs + DB-backed JWT blacklist.

After removing Redis, all cache helpers are intentional no-ops so that
callers (article_service, post_service, admin_service, etc.) continue to
work without modification.  The JWT blacklist is persisted in the
``token_blacklist`` PostgreSQL table instead.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.token_blacklist import TokenBlacklist

logger: logging.Logger = logging.getLogger(__name__)


# ── Cache no-op stubs ─────────────────────────────────────────
# These maintain the same interface so that service files importing them
# don't need any changes.


async def get_cached(namespace: str, key: str) -> Any | None:  # noqa: ARG001
    """Always returns ``None`` (cache miss)."""
    return None


async def set_cached(  # noqa: ARG001
    namespace: str, key: str, value: Any, *, ttl_seconds: int = 300
) -> None:
    """No-op — caching disabled."""


async def delete_cached(namespace: str, key: str) -> None:  # noqa: ARG001
    """No-op — caching disabled."""


async def invalidate_pattern(pattern: str) -> int:  # noqa: ARG001
    """No-op — returns 0 deleted keys."""
    return 0


async def invalidate_namespace(namespace: str) -> int:  # noqa: ARG001
    """No-op — returns 0 deleted keys."""
    return 0


# ── JWT Blacklist (PostgreSQL-backed) ─────────────────────────


async def _get_session() -> AsyncSession:
    """Create a one-shot session for blacklist operations.

    We use the session factory directly because the blacklist functions
    are called from contexts that don't have a request-scoped session
    (e.g. ``verify_admin_token_async`` in the dependency layer).
    """
    from app.database import async_session_factory

    return async_session_factory()


async def blacklist_token(jti: str, *, ttl_seconds: int) -> None:
    """Add a JWT ID to the denylist with an expiry matching token lifetime."""
    try:
        expires_at = datetime.now(timezone.utc)
        # ttl_seconds from the caller represents remaining token lifetime
        from datetime import timedelta

        expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)
        entry = TokenBlacklist(
            jti=jti,
            expires_at=expires_at,
            created_at=datetime.now(timezone.utc),
        )
        async with await _get_session() as session:
            session.add(entry)
            await session.commit()
        logger.info("JWT blacklisted: jti=%s, expires_at=%s", jti, expires_at)
    except Exception as exc:
        logger.warning("Failed to blacklist JWT %s: %s", jti, exc)


async def is_token_blacklisted(jti: str) -> bool:
    """Check whether a JWT ID has been revoked."""
    try:
        async with await _get_session() as session:
            result = await session.execute(
                select(TokenBlacklist.jti).where(
                    TokenBlacklist.jti == jti  # type: ignore[arg-type]
                )
            )
            return result.scalar_one_or_none() is not None
    except Exception:
        # Fail-open for availability (same trade-off as before).
        return False


async def cleanup_expired_tokens() -> int:
    """Delete blacklist entries whose tokens have already expired.

    Call periodically (e.g. on startup or via a scheduled task).
    """
    try:
        async with await _get_session() as session:
            result = await session.execute(
                delete(TokenBlacklist).where(
                    TokenBlacklist.expires_at < datetime.now(timezone.utc)  # type: ignore[operator]
                )
            )
            await session.commit()
            deleted: int = result.rowcount  # type: ignore[assignment]
            if deleted:
                logger.info("Cleaned up %d expired blacklist entries", deleted)
            return deleted
    except Exception as exc:
        logger.warning("Failed to cleanup expired tokens: %s", exc)
        return 0
