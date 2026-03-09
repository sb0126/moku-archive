"""Cache service — in-memory LRU with TTL + DB-backed JWT blacklist.

Replaces the previous no-op stubs with a lightweight in-process LRU cache.
The public API (get_cached, set_cached, delete_cached, invalidate_namespace,
invalidate_pattern) is unchanged so that callers (article_service,
post_service, admin_service, etc.) continue to work without modification.

The JWT blacklist remains backed by the ``token_blacklist`` PostgreSQL table.
"""

from __future__ import annotations

import logging
import threading
import time
from collections import OrderedDict
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.token_blacklist import TokenBlacklist

logger: logging.Logger = logging.getLogger(__name__)


# ── In-Memory LRU Cache ──────────────────────────────────────

class _LRUCache:
    """Thread-safe in-memory LRU cache with per-entry TTL.

    Each entry is stored as ``(value, expires_at_monotonic)``.
    When the cache exceeds ``max_size``, the least-recently-used
    entry is evicted regardless of its TTL.
    """

    __slots__ = ("_store", "_max_size", "_lock", "_hits", "_misses")

    def __init__(self, max_size: int = 256) -> None:
        self._store: OrderedDict[str, tuple[Any, float]] = OrderedDict()
        self._max_size = max_size
        self._lock = threading.Lock()
        self._hits: int = 0
        self._misses: int = 0

    def get(self, key: str) -> Any | None:
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                self._misses += 1
                return None
            value, expires_at = entry
            if time.monotonic() > expires_at:
                # Expired → evict
                del self._store[key]
                self._misses += 1
                return None
            # Move to end (most recently used)
            self._store.move_to_end(key)
            self._hits += 1
            return value

    def set(self, key: str, value: Any, *, ttl_seconds: int = 300) -> None:
        with self._lock:
            expires_at = time.monotonic() + ttl_seconds
            if key in self._store:
                del self._store[key]
            self._store[key] = (value, expires_at)
            # Evict oldest if over capacity
            while len(self._store) > self._max_size:
                evicted_key, _ = self._store.popitem(last=False)
                logger.debug("LRU evicted: %s", evicted_key)

    def delete(self, key: str) -> bool:
        with self._lock:
            if key in self._store:
                del self._store[key]
                return True
            return False

    def invalidate_prefix(self, prefix: str) -> int:
        with self._lock:
            keys_to_delete = [k for k in self._store if k.startswith(prefix)]
            for k in keys_to_delete:
                del self._store[k]
            return len(keys_to_delete)

    def clear(self) -> None:
        with self._lock:
            self._store.clear()
            self._hits = 0
            self._misses = 0

    def stats(self) -> dict[str, int]:
        with self._lock:
            now = time.monotonic()
            alive = sum(1 for _, (_, exp) in self._store.items() if exp > now)
            return {
                "total_entries": len(self._store),
                "alive_entries": alive,
                "hits": self._hits,
                "misses": self._misses,
            }


# Global singleton — shared across all async tasks in the process
_cache = _LRUCache(max_size=256)


# ── Public cache API (same interface as before) ──────────────


async def get_cached(namespace: str, key: str) -> Any | None:
    """Retrieve a value from the in-memory LRU cache."""
    return _cache.get(f"{namespace}:{key}")


async def set_cached(
    namespace: str, key: str, value: Any, *, ttl_seconds: int = 300
) -> None:
    """Store a value in the in-memory LRU cache with TTL."""
    _cache.set(f"{namespace}:{key}", value, ttl_seconds=ttl_seconds)


async def delete_cached(namespace: str, key: str) -> None:
    """Remove a specific entry from the cache."""
    _cache.delete(f"{namespace}:{key}")


async def invalidate_pattern(pattern: str) -> int:
    """Invalidate all entries whose key starts with ``pattern``."""
    deleted = _cache.invalidate_prefix(pattern)
    if deleted:
        logger.debug("Cache invalidated %d entries matching '%s'", deleted, pattern)
    return deleted


async def invalidate_namespace(namespace: str) -> int:
    """Invalidate all entries in a namespace (prefix ``namespace:``)."""
    deleted = _cache.invalidate_prefix(f"{namespace}:")
    if deleted:
        logger.debug("Cache namespace '%s' invalidated (%d entries)", namespace, deleted)
    return deleted


def get_cache_stats() -> dict[str, int]:
    """Return cache hit/miss statistics (for admin/debug endpoints)."""
    return _cache.stats()


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
