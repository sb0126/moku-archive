"""Redis caching service — async, graceful fallback when Redis is unavailable.

Provides:
  - ``get_cached`` / ``set_cached`` / ``delete_cached`` for JSON-serialisable values
  - ``invalidate_pattern`` for glob-based cache busting
  - ``blacklist_token`` / ``is_token_blacklisted`` for JWT denylist
  - ``get_redis`` for direct access when needed

All operations are *fire-and-forget safe*: if Redis is down, caching is silently
skipped and the app continues to serve fresh data from the DB.
"""

from __future__ import annotations

import json
import logging
from typing import Any

import redis.asyncio as aioredis

from app.config import settings

logger: logging.Logger = logging.getLogger(__name__)

# ── Client singleton ──────────────────────────────────────────

_redis_client: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    """Return (and lazily create) the shared async Redis client."""
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(
            settings.redis_url,
            decode_responses=True,
            socket_connect_timeout=3,
            socket_timeout=3,
        )
    return _redis_client


async def close_redis() -> None:
    """Gracefully close the Redis connection (call on shutdown)."""
    global _redis_client
    if _redis_client is not None:
        await _redis_client.aclose()
        _redis_client = None
        logger.info("Redis connection closed")


async def ping_redis() -> bool:
    """Return True if Redis is reachable."""
    try:
        client = await get_redis()
        return bool(await client.ping())
    except Exception:
        return False


# ── Cache helpers ─────────────────────────────────────────────

_KEY_PREFIX = "moku:"


def _make_key(namespace: str, key: str) -> str:
    return f"{_KEY_PREFIX}{namespace}:{key}"


async def get_cached(namespace: str, key: str) -> Any | None:
    """Retrieve a cached JSON value. Returns ``None`` on miss or error."""
    try:
        client = await get_redis()
        raw: str | None = await client.get(_make_key(namespace, key))
        if raw is None:
            return None
        return json.loads(raw)
    except Exception as exc:
        logger.debug("Cache GET miss/error (%s:%s): %s", namespace, key, exc)
        return None


async def set_cached(
    namespace: str, key: str, value: Any, *, ttl_seconds: int = 300
) -> None:
    """Store a JSON-serialisable value with a TTL (default 5 min)."""
    try:
        client = await get_redis()
        await client.set(
            _make_key(namespace, key),
            json.dumps(value, default=str),
            ex=ttl_seconds,
        )
    except Exception as exc:
        logger.debug("Cache SET error (%s:%s): %s", namespace, key, exc)


async def delete_cached(namespace: str, key: str) -> None:
    """Delete a single cached key."""
    try:
        client = await get_redis()
        await client.delete(_make_key(namespace, key))
    except Exception as exc:
        logger.debug("Cache DELETE error (%s:%s): %s", namespace, key, exc)


async def invalidate_pattern(pattern: str) -> int:
    """Delete all keys matching a glob pattern. Returns count deleted.

    Example patterns:
        ``"moku:articles:*"``  — all article caches
        ``"moku:posts:*"``     — all post caches
    """
    deleted = 0
    try:
        client = await get_redis()
        async for k in client.scan_iter(match=pattern, count=200):
            await client.delete(k)
            deleted += 1
        if deleted:
            logger.info("Cache invalidated %d keys matching %s", deleted, pattern)
    except Exception as exc:
        logger.debug("Cache invalidate error (%s): %s", pattern, exc)
    return deleted


# ── Convenience: namespace invalidation ───────────────────────


async def invalidate_namespace(namespace: str) -> int:
    """Invalidate all keys under a namespace (e.g. ``"articles"``)."""
    return await invalidate_pattern(f"{_KEY_PREFIX}{namespace}:*")


# ── JWT Blacklist ─────────────────────────────────────────────

_BLACKLIST_PREFIX = "moku:jwt_blacklist:"


async def blacklist_token(jti: str, *, ttl_seconds: int) -> None:
    """Add a JWT ID to the denylist with TTL matching the token's remaining lifetime."""
    try:
        client = await get_redis()
        await client.set(f"{_BLACKLIST_PREFIX}{jti}", "1", ex=ttl_seconds)
        logger.info("JWT blacklisted: jti=%s, ttl=%ds", jti, ttl_seconds)
    except Exception as exc:
        logger.warning("Failed to blacklist JWT %s: %s", jti, exc)


async def is_token_blacklisted(jti: str) -> bool:
    """Check whether a JWT ID has been revoked."""
    try:
        client = await get_redis()
        result = await client.get(f"{_BLACKLIST_PREFIX}{jti}")
        return result is not None
    except Exception:
        # If Redis is down, fail-open (allow token) to prevent total lockout.
        # This is a security trade-off for availability.
        return False
