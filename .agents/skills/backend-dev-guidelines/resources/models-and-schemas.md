# Models & Schemas

## SQLModel Table Models

### Rules

1. **One file per aggregate** — `post.py` contains `Post` and `PostLike`
2. **No business methods** — Models are pure data containers
3. **Use `ClassVar` for `__tablename__`** — Required for mypy strict
4. **Use `timezone.utc`** — Never use `datetime.utcnow()` (deprecated)
5. **Explicit column types** — Use `sa_column=Column(...)` for precise control

### Correct Pattern

```python
from datetime import datetime, timezone
from typing import ClassVar, Optional

from sqlalchemy import Column, Text, BigInteger
from sqlmodel import SQLModel, Field


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

    # ✅ CORRECT — timezone-aware
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), nullable=False
    )
```

### Common Mistakes

```python
# ❌ DEPRECATED — datetime.utcnow (naive datetime, deprecated Python 3.12)
created_at: datetime = Field(default_factory=datetime.utcnow)

# ✅ CORRECT — timezone-aware
created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
```

### Enum Types

Define enums alongside their model, re-export from `__init__.py`:

```python
from enum import Enum

class PostCategory(str, Enum):
    QUESTION = "question"
    INFO = "info"
    CHAT = "chat"
```

---

## Pydantic Schemas

### Rules

1. **Separate schemas for Create/Update/Response** — Never reuse request as response
2. **Use `Field()` constraints** — min_length, max_length, ge, le, regex
3. **Use `BaseModel`, not `SQLModel`** — Schemas must not be table models
4. **Explicit `model_config`** for alias support

### Request Schemas

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

### Response Schemas

```python
class PostResponse(BaseModel):
    """Single post in API responses."""
    id: str
    numeric_id: int
    title: str
    author: str
    content: str
    views: int
    comments: int
    pinned: bool
    pinned_at: datetime | None
    experience: str | None
    category: str | None
    created_at: datetime
    updated_at: datetime


class PostCreateResponse(BaseModel):
    """Response after creating a post."""
    success: bool = True
    message: str
    post: PostResponse
```

### Alias Support (camelCase ↔ snake_case)

```python
class LikeToggleRequest(BaseModel):
    visitor_id: str = Field(alias="visitorId", min_length=8)
    model_config = {"populate_by_name": True}
```

### `__init__.py` Re-exports

Always re-export all schemas for clean imports:

```python
# schemas/__init__.py
from app.schemas.post import PostCreate, PostResponse, PostListResponse, ...
from app.schemas.comment import CommentCreate, CommentResponse, ...

__all__ = ["PostCreate", "PostResponse", ...]
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
