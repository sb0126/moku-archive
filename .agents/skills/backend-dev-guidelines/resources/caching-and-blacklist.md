# Caching & JWT Blacklist

## Architecture Overview

```
┌──────────────────────────────────────────┐
│  In-Memory LRU Cache (256 entries, TTL)  │  ← articles, posts, admin stats
├──────────────────────────────────────────┤
│  PostgreSQL `token_blacklist` table      │  ← revoked JWT jti values
└──────────────────────────────────────────┘
```

**Design Decision:** Redis was removed in favour of a single-PostgreSQL architecture.
The in-memory LRU cache handles hot-path caching, and the `token_blacklist` table
handles JWT revocation. This simplifies infrastructure (one less service to manage).

---

## In-Memory LRU Cache

### Implementation (`services/cache.py`)

Thread-safe, in-process LRU cache with per-entry TTL:

```python
class _LRUCache:
    """Thread-safe in-memory LRU cache with per-entry TTL."""

    def __init__(self, max_size: int = 256) -> None:
        self._store: OrderedDict[str, tuple[Any, float]] = OrderedDict()
        self._max_size = max_size
        self._lock = threading.Lock()

    def get(self, key: str) -> Any | None:
        # Returns None if expired or missing
        # Moves to end (most recently used) on hit

    def set(self, key: str, value: Any, *, ttl_seconds: int = 300) -> None:
        # Evicts oldest when over capacity

    def delete(self, key: str) -> bool: ...
    def invalidate_prefix(self, prefix: str) -> int: ...
    def clear(self) -> None: ...
    def stats(self) -> dict[str, int]: ...

# Global singleton
_cache = _LRUCache(max_size=256)
```

### Public API

All functions are `async` for interface consistency (even though the LRU is synchronous):

```python
# Read
await get_cached("articles", "list")

# Write (default TTL: 5 minutes)
await set_cached("articles", "list", articles_data, ttl_seconds=300)

# Delete specific entry
await delete_cached("articles", "list")

# Invalidate all entries in a namespace
await invalidate_namespace("articles")  # deletes "articles:*"

# Invalidate by prefix pattern
await invalidate_pattern("posts:")  # deletes "posts:*"

# Cache stats (sync, for admin dashboard)
stats = get_cache_stats()
# {"total_entries": 42, "alive_entries": 38, "hits": 1234, "misses": 56}
```

### Cache Key Convention

```
{namespace}:{key}
```

Examples:
- `articles:list` — cached article list
- `articles:visa-guide-2026` — cached single article
- `posts:list:page=1&limit=20` — cached paginated post list
- `admin:stats` — cached dashboard statistics

### When to Invalidate

| Operation | Invalidation |
|-----------|-------------|
| Create article | `invalidate_namespace("articles")` |
| Update article | `invalidate_namespace("articles")` |
| Delete article | `invalidate_namespace("articles")` |
| Create post | `invalidate_namespace("posts")` |
| Update/delete post | `invalidate_namespace("posts")` |
| Create comment | `invalidate_namespace("posts")` (comment_count changes) |

---

## PostgreSQL JWT Blacklist

### Model (`models/token_blacklist.py`)

```python
class TokenBlacklist(SQLModel, table=True):
    __tablename__ = "token_blacklist"

    jti: str = Field(sa_column=Column(String(64), primary_key=True))
    expires_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False, index=True),
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
```

**Note:** Unlike other models, `TokenBlacklist` uses `DateTime(timezone=True)`
because it needs timezone-aware expiry comparison.

### Blacklist Operations

```python
# Revoke a token
await blacklist_token(jti="abc123", ttl_seconds=86400)

# Check if revoked
is_revoked = await is_token_blacklisted(jti="abc123")

# Cleanup expired entries (called on startup)
cleaned = await cleanup_expired_tokens()
```

### Session Management for Blacklist

Blacklist functions create their own sessions (not request-scoped) because
they're called from the dependency layer which doesn't have a request session:

```python
async def _get_session() -> AsyncSession:
    """One-shot session for blacklist operations."""
    from app.database import async_session_factory
    return async_session_factory()

async def is_token_blacklisted(jti: str) -> bool:
    try:
        async with await _get_session() as session:
            result = await session.execute(
                select(TokenBlacklist.jti).where(TokenBlacklist.jti == jti)
            )
            return result.scalar_one_or_none() is not None
    except Exception:
        return False  # Fail-open for availability
```

**Trade-off:** Fail-open means a revoked token might briefly work if the DB is down.
This is acceptable for admin-only auth with short token lifetimes (24h).

### Startup Cleanup

Expired blacklist entries are cleaned on every server start:

```python
# In lifespan()
cleaned = await cleanup_expired_tokens()
if cleaned:
    logger.info("🧹 Cleaned up %d expired blacklist entries", cleaned)
```

---

## Rules

1. **Always invalidate cache after mutations** — stale data is worse than cache miss
2. **Use namespaces** — never use raw keys without a namespace prefix
3. **Keep TTL short** — 5 minutes default, adjust per use case
4. **Blacklist fail-open** — acceptable trade-off for availability
5. **No Redis dependency** — everything runs on PostgreSQL + in-memory
