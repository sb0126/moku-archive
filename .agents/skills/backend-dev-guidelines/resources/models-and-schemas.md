# Models & Schemas

## SQLModel Table Models

### Rules

1. **One file per aggregate** — `post.py` contains `Post`, `PostLike`, `PostCategory`, `ExperienceType`
2. **No business methods** — Models are pure data containers
3. **Use `ClassVar` for `__tablename__`** — Required for mypy strict
4. **Use `_utcnow()` factory** — Timezone-naive datetime for asyncpg 0.30+ compatibility
5. **Explicit column types** — Use `sa_column=Column(...)` for precise control

### The `_utcnow()` Pattern

Every model file defines this helper for datetime defaults:

```python
from datetime import datetime, timezone

def _utcnow() -> datetime:
    """Timezone-aware UTC now, then strip tzinfo for asyncpg 0.30+ compat."""
    return datetime.now(timezone.utc).replace(tzinfo=None)
```

**Why `replace(tzinfo=None)`?** asyncpg 0.30+ raises `DBAPIError` when passing timezone-aware
datetimes to `TIMESTAMP WITHOUT TIME ZONE` columns. This pattern produces UTC times
without the timezone info that causes the error.

### Correct Pattern

```python
from datetime import datetime, timezone
from typing import ClassVar, Optional

from sqlalchemy import Column, Text, BigInteger
from sqlmodel import SQLModel, Field


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Post(SQLModel, table=True):
    """Community board post."""

    __tablename__: ClassVar[str] = "posts"

    id: str = Field(sa_column=Column(Text, primary_key=True))
    numeric_id: int = Field(sa_column=Column(BigInteger, nullable=False, index=True))
    title: str = Field(sa_column=Column(Text, nullable=False))
    author: str = Field(sa_column=Column(Text, nullable=False))
    content: str = Field(sa_column=Column(Text, nullable=False))
    password: str = Field(sa_column=Column(Text, nullable=False))
    views: int = Field(default=0, nullable=False)
    comment_count: int = Field(default=0, nullable=False)
    pinned: bool = Field(default=False, nullable=False)
    pinned_at: Optional[datetime] = Field(default=None)
    experience: Optional[str] = Field(default=None)
    category: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=_utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=_utcnow, nullable=False)
```

### Common Mistakes

```python
# ❌ DEPRECATED — datetime.utcnow (naive datetime, deprecated Python 3.12)
created_at: datetime = Field(default_factory=datetime.utcnow)

# ❌ CAUSES DBAPIError with asyncpg 0.30+ (timezone-aware → TZ-less column)
created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# ✅ CORRECT — timezone-aware then strip tzinfo
created_at: datetime = Field(default_factory=_utcnow)
```

### Comment Model (with parent_id for Nested Replies)

```python
class Comment(SQLModel, table=True):
    __tablename__: ClassVar[str] = "comments"

    id: str = Field(sa_column=Column(Text, primary_key=True))
    post_id: str = Field(foreign_key="posts.id", nullable=False, index=True)
    parent_id: str | None = Field(default=None, foreign_key="comments.id",
                                   index=True, nullable=True)  # ← nested reply support
    author: str = Field(sa_column=Column(Text, nullable=False))
    content: str = Field(sa_column=Column(Text, nullable=False))
    password: str = Field(sa_column=Column(Text, nullable=False))
    created_at: datetime = Field(default_factory=_utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=_utcnow, nullable=False)
```

### Article Model (JSONB Locale Content)

```python
from sqlalchemy.dialects.postgresql import JSONB

class Article(SQLModel, table=True):
    __tablename__: ClassVar[str] = "articles"

    id: str = Field(sa_column=Column(Text, primary_key=True))  # slug-based
    image_url: Optional[str] = Field(default=None)
    date: Optional[str] = Field(default=None)
    ja: dict[str, Any] = Field(sa_column=Column(JSONB, nullable=False))
    ko: Optional[dict[str, Any]] = Field(default=None, sa_column=Column(JSONB, nullable=True))
    created_at: datetime = Field(default_factory=_utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=_utcnow, nullable=False)
```

### TokenBlacklist Model (PostgreSQL JWT Revocation)

```python
from sqlalchemy import Column, DateTime, String

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

**Note:** `TokenBlacklist` intentionally uses `DateTime(timezone=True)` because
it stores JWT expiry timestamps that need timezone info for comparison.

### Enum Types

Define enums alongside their model, re-export from `__init__.py`:

```python
from enum import Enum

class PostCategory(str, Enum):
    QUESTION = "question"
    INFO = "info"
    CHAT = "chat"

class ExperienceType(str, Enum):
    EXPERIENCED = "experienced"
    INEXPERIENCED = "inexperienced"

class InquiryStatus(str, Enum):
    PENDING = "pending"
    CONTACTED = "contacted"
    COMPLETED = "completed"
```

### `models/__init__.py` Re-exports

```python
from app.models.article import Article
from app.models.comment import Comment
from app.models.inquiry import Inquiry, InquiryStatus
from app.models.post import ExperienceType, Post, PostCategory, PostLike
from app.models.token_blacklist import TokenBlacklist

__all__ = [
    "Article", "Comment", "ExperienceType", "Inquiry",
    "InquiryStatus", "Post", "PostCategory", "PostLike", "TokenBlacklist",
]
```

---

## Pydantic Schemas

### CamelModel Base (Auto camelCase Serialization)

All response schemas inherit from `CamelModel` for automatic `snake_case → camelCase` JSON:

```python
from pydantic import BaseModel
from pydantic.alias_generators import to_camel

class CamelModel(BaseModel):
    """Base model that serialises fields as camelCase JSON."""

    model_config = {
        "alias_generator": to_camel,
        "populate_by_name": True,  # also accept snake_case in tests
    }
```

### Rules

1. **Separate schemas for Create/Update/Response** — Never reuse request as response
2. **Use `Field()` constraints** — min_length, max_length, ge, le, regex
3. **Use `BaseModel` for requests** — Not `SQLModel` or `CamelModel`
4. **Use `CamelModel` for responses** — Automatic camelCase serialization
5. **Explicit `model_config`** for alias support

### Request Schemas (BaseModel)

```python
from pydantic import BaseModel, Field
from typing import Optional, Literal

class PostCreate(BaseModel):
    """Request body for creating a post."""
    author: str = Field(min_length=1, max_length=50)
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1, max_length=10000)
    password: str = Field(min_length=4, max_length=50)
    experience: Optional[Literal["experienced", "inexperienced"]] = None
    category: Optional[Literal["question", "info", "chat"]] = None


class PostUpdate(BaseModel):
    """Partial update — only provided fields are changed."""
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    content: Optional[str] = Field(default=None, min_length=1, max_length=10000)
    password: str = Field(min_length=4, max_length=50)
```

### Response Schemas (CamelModel)

```python
from app.schemas.common import CamelModel

class PostResponse(CamelModel):
    """Single post in API responses — auto camelCase output."""
    id: str
    numeric_id: int
    title: str
    author: str
    content: str
    views: int
    comments: int          # ← snake_case field → serialized as "comments"
    pinned: bool
    pinned_at: datetime | None
    experience: str | None
    category: str | None
    like_count: int = 0    # ← serialized as "likeCount"
    created_at: datetime   # ← serialized as "createdAt"
    updated_at: datetime


class PostCreateResponse(CamelModel):
    """Response after creating a post."""
    success: bool = True
    message: str
    post: PostResponse
```

### Alias Support (Frontend → Backend)

For request schemas that need to accept both camelCase and snake_case:

```python
class LikeToggleRequest(BaseModel):
    visitor_id: str = Field(alias="visitorId", min_length=8)
    model_config = {"populate_by_name": True}
```

### `schemas/__init__.py` Re-exports

Always re-export all schemas for clean imports:

```python
# schemas/__init__.py
from app.schemas.common import CamelModel, SuccessResponse, ErrorResponse, ...
from app.schemas.post import PostCreate, PostResponse, PostListResponse, ...
from app.schemas.comment import CommentCreate, CommentResponse, ...
from app.schemas.inquiry import InquiryCreate, InquiryResponse, ...
from app.schemas.article import ArticleCreate, ArticleResponse, ...
from app.schemas.admin import AdminLoginRequest, AdminLoginResponse, ...
from app.schemas.config import SiteConfigResponse, VerificationConfig

__all__ = ["CamelModel", "PostCreate", "PostResponse", ...]
```

---

## Type Safety

### mypy --strict Rules

1. **No bare `type: ignore`** — Always add explanation:
   ```python
   # ❌
   result = session.execute(query)  # type: ignore
   
   # ✅
   result = session.execute(query)  # type: ignore[arg-type]  # SQLModel col() typing
   ```

2. **Use `col()` for SQLModel column comparisons**:
   ```python
   from sqlmodel import col
   
   # ❌ mypy error
   .where(Post.id == post_id)
   
   # ✅ mypy-safe
   .where(col(Post.id) == post_id)
   ```

3. **Explicit return types** on all functions:
   ```python
   # ❌
   def generate_id():
       return f"post_{int(time.time() * 1000)}"
   
   # ✅
   def generate_id() -> str:
       return f"post_{int(time.time() * 1000)}"
   ```

4. **mypy.ini third-party ignores**:
   ```ini
   [mypy]
   plugins = sqlalchemy.ext.mypy.plugin
   strict = True

   [mypy-aioboto3.*]
   ignore_missing_imports = True
   [mypy-jose.*]
   ignore_missing_imports = True
   [mypy-slowapi.*]
   ignore_missing_imports = True
   [mypy-passlib.*]
   ignore_missing_imports = True
   ```
