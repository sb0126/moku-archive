# Services & Business Logic

## Purpose

The service layer encapsulates **all business logic**, keeping routers thin and services testable.

## Rules

1. **Services are framework-agnostic** — No FastAPI imports (`Request`, `HTTPException`, `Depends`)
2. **Services receive `AsyncSession` as parameter** — Not via Depends()
3. **Services raise domain exceptions** — Routers translate to HTTP errors
4. **Services are stateless** — No mutable module-level state
5. **One service per domain** — `post_service.py`, `comment_service.py`, etc.

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
from app.services.sanitize import sanitize_text
from app.services.spam import check_spam


class PostValidationError(Exception):
    """Raised when post validation fails."""
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


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
        raise PostValidationError("入力内容が無効です")

    # Spam check
    spam_result = check_spam(f"{title} {content}")
    if spam_result.is_spam:
        raise PostValidationError(spam_result.reason or "スパムが検出されました")

    # Generate numeric ID
    max_result = await session.execute(select(func.max(col(Post.numeric_id))))
    max_numeric: int | None = max_result.scalar_one_or_none()
    numeric_id = (max_numeric or 0) + 1

    now = datetime.now(timezone.utc)
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
    """Fetch a post by ID, raise if not found."""
    result = await session.execute(select(Post).where(col(Post.id) == post_id))
    post: Post | None = result.scalar_one_or_none()
    if post is None:
        raise PostValidationError("投稿が見つかりません", status_code=404)
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
from app.services.post_service import PostValidationError

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
    except PostValidationError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
```

## Cross-Cutting Services

These services provide shared functionality across domains:

| Service | Purpose | Pattern |
|---------|---------|---------|
| `auth.py` | JWT creation/verification, password hashing | Pure functions |
| `sanitize.py` | XSS prevention, text cleaning | Pure functions |
| `spam.py` | Spam content detection | Pure functions |
| `storage.py` | File storage (Supabase → Cloudflare R2) | Async functions |
| `rate_limit.py` | SlowAPI limiter instance | Singleton |

## Anti-Patterns

```python
# ❌ NEVER — HTTPException in service
from fastapi import HTTPException

async def create(session, body):
    if not body.title:
        raise HTTPException(400, "Title required")  # framework-coupled!

# ✅ ALWAYS — Domain exception
class PostValidationError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code

async def create(session, body):
    if not body.title:
        raise PostValidationError("Title required")
```
