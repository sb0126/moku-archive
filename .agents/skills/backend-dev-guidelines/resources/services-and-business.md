# Services & Business Logic

## Purpose

The service layer encapsulates **all business logic**, keeping routers thin and services testable.

## Rules

1. **Services are framework-agnostic** — No FastAPI imports (`Request`, `HTTPException`, `Depends`)
2. **Services receive `AsyncSession` as parameter** — Not via Depends()
3. **Services raise `DomainError`** — Centralized exception hierarchy in `exceptions.py`
4. **Services are stateless** — No mutable module-level state
5. **One service per domain** — `post_service.py`, `comment_service.py`, etc.

## Exception Hierarchy (Centralized)

All domain errors derive from `DomainError` — defined once in `services/exceptions.py`:

```python
from app.services.exceptions import (
    DomainError,       # base (400)
    NotFoundError,     # 404
    ForbiddenError,    # 403
    ConflictError,     # 409
    ValidationError,   # 400
    SpamDetectedError, # 400
)
```

**Key Difference from Previous:** No per-service exception classes. Use the centralized hierarchy.

## Pattern: Functional Services (Recommended for this project)

```python
# services/post_service.py

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col

from app.models import Post, PostLike
from app.schemas import PostCreate, PostCreateResponse, PostResponse
from app.services.auth import hash_password
from app.services.exceptions import NotFoundError, SpamDetectedError, ValidationError
from app.services.sanitize import sanitize_text
from app.services.spam import check_spam


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _generate_id() -> str:
    import time
    return f"post_{int(time.time() * 1000)}"


def _to_response(post: Post, *, like_count: int = 0) -> PostResponse:
    return PostResponse(
        id=post.id,
        numeric_id=post.numeric_id,
        title=post.title,
        author=post.author,
        content=post.content,
        views=post.views,
        comments=post.comment_count,
        pinned=post.pinned,
        pinned_at=post.pinned_at,
        experience=post.experience,
        category=post.category,
        like_count=like_count,
        created_at=post.created_at,
        updated_at=post.updated_at,
    )


async def create(session: AsyncSession, body: PostCreate) -> PostCreateResponse:
    """Create a new post with sanitization and spam checking."""
    # Sanitize
    author = sanitize_text(body.author)
    title = sanitize_text(body.title)
    content = sanitize_text(body.content)

    if not author or not title or not content:
        raise ValidationError("入力内容が無効です")

    # Spam check
    spam_result = check_spam(f"{title} {content}")
    if spam_result.is_spam:
        raise SpamDetectedError(spam_result.reason or "スパムが検出されました")

    # Generate numeric ID
    max_result = await session.execute(select(func.max(col(Post.numeric_id))))
    max_numeric: int | None = max_result.scalar_one_or_none()
    numeric_id = (max_numeric or 0) + 1

    now = _utcnow()
    post = Post(
        id=_generate_id(),
        numeric_id=numeric_id,
        title=title,
        author=author,
        content=content,
        password=hash_password(body.password),
        experience=body.experience,
        category=body.category,
        views=0,
        comment_count=0,
        pinned=False,
        pinned_at=None,
        created_at=now,
        updated_at=now,
    )
    session.add(post)
    await session.commit()
    await session.refresh(post)

    return PostCreateResponse(
        message="投稿が作成されました",
        post=_to_response(post),
    )


async def get_or_404(session: AsyncSession, post_id: str) -> Post:
    """Fetch a post by ID, raise NotFoundError if missing."""
    result = await session.execute(select(Post).where(col(Post.id) == post_id))
    post: Post | None = result.scalar_one_or_none()
    if post is None:
        raise NotFoundError("投稿が見つかりません")
    return post
```

## Router Integration

```python
# routers/posts.py

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.schemas import PostCreate, PostCreateResponse
from app.services import limiter
from app.services import post_service
from app.services.exceptions import DomainError

router = APIRouter(prefix="/api/posts", tags=["posts"])


@router.post("", response_model=PostCreateResponse, status_code=201)
@limiter.limit("5/minute")
async def create_post(
    request: Request,
    body: PostCreate,
    session: AsyncSession = Depends(get_session),
) -> PostCreateResponse:
    try:
        return await post_service.create(session, body)
    except DomainError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
```

## Cross-Cutting Services

These services provide shared functionality across domains:

| Service | Purpose | Pattern |
|---------|---------|---------|
| `auth.py` | JWT creation/verification, password hashing (bcrypt + legacy) | Pure + async functions |
| `cache.py` | In-memory LRU cache (256 entries) + PostgreSQL JWT blacklist | Singleton + async functions |
| `exceptions.py` | Centralized DomainError hierarchy | Exception classes |
| `sanitize.py` | XSS prevention, text cleaning | Pure functions |
| `spam.py` | Spam content detection (URL flood, keywords, repetition) | Pure functions |
| `storage.py` | Cloudflare R2 file upload/delete via aioboto3 | Async functions |
| `rate_limit.py` | SlowAPI limiter instance (in-memory) | Singleton |

### `services/__init__.py` re-exports:

```python
from app.services.auth import (
    create_admin_token, decode_admin_token, get_token_remaining_seconds,
    hash_password, needs_rehash, verify_admin_token,
    verify_admin_token_async, verify_password,
)
from app.services.exceptions import (
    ConflictError, DomainError, ForbiddenError,
    NotFoundError, SpamDetectedError, ValidationError,
)
from app.services.rate_limit import limiter
from app.services.sanitize import sanitize_text
from app.services.spam import SpamCheckResult, check_spam
```

## Anti-Patterns

```python
# ❌ NEVER — HTTPException in service
from fastapi import HTTPException

async def create(session, body):
    if not body.title:
        raise HTTPException(400, "Title required")  # framework-coupled!

# ✅ ALWAYS — DomainError (centralized)
from app.services.exceptions import ValidationError

async def create(session, body):
    if not body.title:
        raise ValidationError("Title required")
```

```python
# ❌ NEVER — per-service exception classes
class PostValidationError(Exception): ...  # don't create per-service errors

# ✅ ALWAYS — use centralized hierarchy
from app.services.exceptions import ValidationError, NotFoundError
```

```python
# ❌ NEVER — timezone-aware datetime for DB storage
now = datetime.now(timezone.utc)
post = Post(created_at=now, ...)  # DBAPIError with asyncpg 0.30+

# ✅ ALWAYS — strip tzinfo
now = datetime.now(timezone.utc).replace(tzinfo=None)
post = Post(created_at=now, ...)
```
