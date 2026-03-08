# Database Patterns

## Async Engine & Session Factory

```python
# database.py
from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine,
)
from app.config import settings

engine: AsyncEngine = create_async_engine(
    settings.database_url,
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

## Rules

### 1. Always Use `col()` for mypy-safe Column References

```python
from sqlmodel import col

# ❌ mypy error
.where(Post.id == post_id)

# ✅ mypy-safe
.where(col(Post.id) == post_id)
```

### 2. Explicit Type Annotations on Query Results

```python
# ❌ Implicit types
result = await session.execute(select(Post))
posts = result.scalars().all()

# ✅ Explicit types
result = await session.execute(select(Post))
posts: list[Post] = list(result.scalars().all())
```

### 3. Use `select()` Not `session.query()`

```python
# ❌ Legacy ORM-style (sync, deprecated for async)
posts = session.query(Post).filter_by(pinned=True).all()

# ✅ Core-style (async-compatible)
result = await session.execute(
    select(Post).where(col(Post.pinned) == True)
)
posts: list[Post] = list(result.scalars().all())
```

### 4. Transaction Management

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

### 5. Avoid N+1 Queries

```python
# ❌ N+1 — one query per article
articles = await get_all_articles(session)
for article in articles:
    article.image_url = await resolve_storage_url(article.image_url)  # N queries!

# ✅ Batch — one bulk operation
articles = await get_all_articles(session)
storage_articles = [a for a in articles if a.image_url.startswith("storage:")]
paths = [a.image_url.removeprefix("storage:") for a in storage_articles]
signed_urls = await batch_sign_urls(paths)  # 1 query!
```

### 6. Use Atomic Increment for Counters

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

### 7. Pagination Pattern

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

### 8. Cascade Deletes

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
