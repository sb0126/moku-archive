# Database Patterns

## Async Engine & Session Factory

```python
# database.py
from collections.abc import AsyncGenerator
from urllib.parse import urlparse, urlunparse
from sqlalchemy.ext.asyncio import (
    AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine,
)
from app.config import settings

def _sanitise_database_url(raw_url: str) -> str:
    """Ensure the database URL has a valid port (default 5432) and log masked."""
    if raw_url.startswith("sqlite"):
        return raw_url
    parsed = urlparse(raw_url)
    # Fix missing port for postgres URLs
    if parsed.port is None and parsed.scheme.startswith("postgres"):
        hostname = parsed.hostname or "localhost"
        user_info = f"{parsed.username}:{parsed.password}@" if parsed.username else ""
        netloc = f"{user_info}{hostname}:5432"
        parsed = parsed._replace(netloc=netloc)
    return str(urlunparse(parsed))

engine: AsyncEngine = create_async_engine(
    _sanitise_database_url(settings.database_url),
    echo=settings.debug,
    pool_pre_ping=True,      # detect stale connections
    pool_size=5,              # base connection count
    max_overflow=10,          # burst capacity
)

async_session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,   # avoid lazy-load issues in async
)

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session
```

### Key: JSONB ↔ SQLite Compatibility

The project uses JSONB for article locale data. For test environments using SQLite:

```python
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.compiler import compiles

@compiles(JSONB, "sqlite")
def _compile_jsonb_sqlite(type_: JSONB, compiler: object, **kw: object) -> str:
    return "JSON"
```

This is defined in `database.py` and enables SQLite-based tests to work with JSONB models.

## Rules

### 1. The `_utcnow()` Pattern — Timezone-Naive for asyncpg 0.30+

asyncpg 0.30+ raises `DBAPIError` if you pass a timezone-aware datetime to a
`TIMESTAMP WITHOUT TIME ZONE` column. All models use this pattern:

```python
def _utcnow() -> datetime:
    """Timezone-aware UTC now, then strip tzinfo for DB compatibility."""
    return datetime.now(timezone.utc).replace(tzinfo=None)
```

**Critical Rules:**
- ✅ `datetime.now(timezone.utc).replace(tzinfo=None)` — safe for asyncpg 0.30+
- ❌ `datetime.utcnow()` — deprecated in Python 3.12
- ❌ `datetime.now(timezone.utc)` (raw) — causes DBAPIError with asyncpg 0.30+

### 2. Always Use `col()` for mypy-safe Column References

```python
from sqlmodel import col

# ❌ mypy error
.where(Post.id == post_id)

# ✅ mypy-safe
.where(col(Post.id) == post_id)
```

### 3. Explicit Type Annotations on Query Results

```python
# ❌ Implicit types
result = await session.execute(select(Post))
posts = result.scalars().all()

# ✅ Explicit types
result = await session.execute(select(Post))
posts: list[Post] = list(result.scalars().all())
```

### 4. Use `select()` Not `session.query()`

```python
# ❌ Legacy ORM-style (sync, deprecated for async)
posts = session.query(Post).filter_by(pinned=True).all()

# ✅ Core-style (async-compatible)
result = await session.execute(
    select(Post).where(col(Post.pinned) == True)
)
posts: list[Post] = list(result.scalars().all())
```

### 5. Transaction Management

```python
# Simple: auto-commit via session context
async with async_session_factory() as session:
    session.add(post)
    await session.commit()

# Complex: explicit transaction for multi-step operations
async with async_session_factory() as session:
    async with session.begin():
        session.add(comment)
        post.comment_count += 1
        session.add(post)
    # auto-commit on block exit, auto-rollback on exception
```

### 6. Avoid N+1 Queries

```python
# ❌ N+1 — one resolve per article
articles = await get_all_articles(session)
for article in articles:
    article.image_url = resolve_storage_url(article.image_url)  # N operations

# ✅ Batch — resolve all at once
articles = await get_all_articles(session)
for article in articles:
    if article.image_url:
        article.image_url = resolve_storage_url(article.image_url)  # sync, O(1)
```

### 7. Use Atomic Increment for Counters

```python
from sqlalchemy import update

# ❌ Race condition — read-modify-write
post = await get_post(session, post_id)
post.views += 1
session.add(post)
await session.commit()

# ✅ Atomic — SQL-level increment
await session.execute(
    update(Post)
    .where(col(Post.id) == post_id)
    .values(views=col(Post.views) + 1)
)
await session.commit()
```

### 8. Pagination Pattern

```python
async def list_paginated(
    session: AsyncSession,
    page: int,
    limit: int,
    conditions: list[Any],
) -> tuple[list[Post], int, int]:
    # Count query
    count_stmt = select(func.count()).select_from(Post)
    for cond in conditions:
        count_stmt = count_stmt.where(cond)
    total: int = (await session.execute(count_stmt)).scalar_one()
    total_pages = max(1, (total + limit - 1) // limit)

    # Data query
    query = select(Post)
    for cond in conditions:
        query = query.where(cond)
    query = query.offset((page - 1) * limit).limit(limit)

    result = await session.execute(query)
    posts: list[Post] = list(result.scalars().all())

    return posts, total, total_pages
```

### 9. Cascade Deletes

Handle cascades explicitly in application code (not DB-level) for auditability:

```python
async def delete_post(session: AsyncSession, post_id: str) -> None:
    # Delete children first
    await session.execute(delete(Comment).where(col(Comment.post_id) == post_id))
    await session.execute(delete(PostLike).where(col(PostLike.post_id) == post_id))
    
    # Delete parent
    post = await get_or_404(session, post_id)
    await session.delete(post)
    await session.commit()
```

### 10. DB URL Sanitization

Railway and other PaaS providers may provide DATABASE_URL with missing ports.
Always sanitize the URL before creating the engine:

```python
_database_url = _sanitise_database_url(settings.database_url)
engine = create_async_engine(_database_url, ...)
```

The `_sanitise_database_url` function:
- Adds default port `5432` if missing for PostgreSQL
- Logs a masked URL (password hidden) for debugging
- Passes through SQLite URLs unchanged
