# Moku Migration Roadmap
# React SPA (Vite) + Supabase Edge Functions (Hono/Deno)
# -> Next.js 15 (TypeScript) + FastAPI (Python) + SQLModel + Pydantic
# Last updated: 2026-03-08

---

## Architecture Overview

```
┌─────────────────────────────────┐     ┌──────────────────────────────────┐
│  FRONTEND (Vercel)              │     │  BACKEND (Railway / Fly.io)      │
│                                 │     │                                  │
│  Next.js 15 (App Router)       │────▶│  FastAPI + Uvicorn               │
│  TypeScript                     │     │  Pydantic v2 (validation)        │
│  Tailwind CSS v4               │     │  SQLModel (ORM)                  │
│  shadcn/ui + Radix UI          │     │  PostgreSQL (Supabase)           │
│  i18next (ja/ko/en)            │     │  Supabase Storage (images)       │
│  Motion, Lucide, Sonner        │     │  python-jose (JWT)               │
│                                 │     │  passlib[bcrypt] (password hash) │
└─────────────────────────────────┘     └──────────────────────────────────┘
         │                                         │
         └─────────────┬───────────────────────────┘
                        ▼
              ┌──────────────────┐
              │  Supabase        │
              │  PostgreSQL      │
              │  Storage (S3)    │
              └──────────────────┘
```

---

## Phase 0: Pre-Migration Preparation (1-2 days)

### 0-1. Export Current Data
- Supabase DB dump: `posts`, `post_likes`, `comments`, `inquiries`, `articles`, `kv_store` tables
- Supabase Storage bucket `make-466b4f31-images` -> download all article images
- Environment variables backup:
  - `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`
  - `MOKU_ADMIN_PASSWORD`
  - `GA_MEASUREMENT_ID` (default: G-M0EESK8HQK)
  - `GOOGLE_SITE_VERIFICATION`, `NAVER_SITE_VERIFICATION`

### 0-2. Freeze Current i18n Strings
- `/src/app/i18n/locales/ja.ts` (~500+ keys) - PRIMARY
- `/src/app/i18n/locales/ko.ts` - Korean
- `/src/app/i18n/locales/en.ts` - English

### 0-3. Password Migration Decision
Current: SHA-256 + random salt (`saltHex:hashHex` format) + legacy plaintext
Target: bcrypt via passlib

**Strategy: Lazy migration**
- Keep verification logic that handles BOTH formats (SHA-256 salt:hash, legacy plaintext)
- On successful login/verify, re-hash with bcrypt and update DB
- New passwords always use bcrypt
- See Phase 3 for implementation details

---

## Phase 1: Backend - FastAPI Project Scaffolding (2 days)

### 1-1. Project Structure
```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI app, CORS, startup events
│   ├── config.py                  # Settings via pydantic-settings
│   ├── database.py                # SQLModel engine, session dependency
│   │
│   ├── models/                    # SQLModel table models (DB schema)
│   │   ├── __init__.py
│   │   ├── post.py                # Post, PostLike
│   │   ├── comment.py             # Comment
│   │   ├── inquiry.py             # Inquiry
│   │   ├── article.py             # Article, ArticleLocale
│   │   └── kv_store.py            # KVStore (legacy)
│   │
│   ├── schemas/                   # Pydantic request/response schemas
│   │   ├── __init__.py
│   │   ├── post.py                # PostCreate, PostUpdate, PostResponse, PostListResponse, ...
│   │   ├── comment.py             # CommentCreate, CommentUpdate, CommentResponse, ...
│   │   ├── inquiry.py             # InquiryCreate, InquiryResponse, InquiryStatusUpdate, ...
│   │   ├── article.py             # ArticleCreate, ArticleUpdate, ArticleResponse, ...
│   │   ├── admin.py               # AdminLoginRequest, AdminLoginResponse, AdminStatsResponse
│   │   ├── common.py              # SuccessResponse, ErrorResponse, PaginatedResponse
│   │   └── config.py              # SiteConfigResponse
│   │
│   ├── routers/                   # API route modules
│   │   ├── __init__.py
│   │   ├── posts.py               # /api/posts/...
│   │   ├── comments.py            # /api/comments/...
│   │   ├── inquiries.py           # /api/inquiries/...
│   │   ├── articles.py            # /api/articles/...
│   │   ├── admin.py               # /api/admin/...
│   │   └── config.py              # /api/config
│   │
│   ├── services/                  # Business logic layer
│   │   ├── __init__.py
│   │   ├── auth.py                # JWT create/verify, password hash/verify
│   │   ├── spam.py                # Spam detection
│   │   ├── sanitize.py            # XSS sanitization
│   │   ├── storage.py             # Supabase Storage operations
│   │   └── rate_limit.py          # Rate limiting (slowapi)
│   │
│   └── dependencies.py            # get_db, get_admin_user, rate limiters
│
├── alembic/                       # DB migrations
│   ├── versions/
│   └── env.py
├── alembic.ini
├── pyproject.toml                 # Dependencies (uv / poetry)
├── Dockerfile
├── docker-compose.yml             # Local dev: FastAPI + PostgreSQL
└── .env.example
```

### 1-2. Python Dependencies
```toml
# pyproject.toml
[project]
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.34.0",
    "sqlmodel>=0.0.22",
    "pydantic>=2.10.0",
    "pydantic-settings>=2.7.0",
    "asyncpg>=0.30.0",           # Async PostgreSQL driver
    "sqlalchemy[asyncio]>=2.0.36",
    "alembic>=1.14.0",           # DB migrations
    "python-jose[cryptography]>=3.3.0",  # JWT
    "passlib[bcrypt]>=1.7.4",    # Password hashing
    "python-multipart>=0.0.18",  # File uploads
    "slowapi>=0.1.9",            # Rate limiting
    "supabase>=2.11.0",          # Supabase Storage client
    "httpx>=0.28.0",             # HTTP client (for storage signed URLs)
    "bleach>=6.2.0",             # HTML sanitization (replaces DOMPurify server-side)
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.25.0",
    "httpx",                      # TestClient
    "ruff>=0.8.0",               # Linter + formatter
    "mypy>=1.13.0",              # Static type checking
]
```

### 1-3. Config (Pydantic Settings)
```python
# app/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    database_url: str                        # postgresql+asyncpg://...
    
    # Supabase Storage
    supabase_url: str
    supabase_service_role_key: str
    storage_bucket_name: str = "moku-images"
    
    # Admin Auth
    admin_password: str                      # MOKU_ADMIN_PASSWORD
    jwt_secret_key: str                      # same as admin_password or separate
    jwt_algorithm: str = "HS256"
    jwt_expire_hours: int = 24
    
    # Analytics & Verification
    ga_measurement_id: str = "G-M0EESK8HQK"
    google_site_verification: str = ""
    naver_site_verification: str = ""
    
    # CORS
    frontend_url: str = "https://moku.com"
    
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}
```

### 1-4. Database Setup (SQLModel + AsyncPG)
```python
# app/database.py
from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

engine = create_async_engine(settings.database_url, echo=False, pool_size=20)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session
```

---

## Phase 2: Backend - SQLModel Models & Pydantic Schemas (2-3 days)

### 2-1. SQLModel Table Models (ALL fields strictly typed)

```python
# app/models/post.py
import uuid
from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field
from sqlalchemy import Column, Text, BigInteger

class Post(SQLModel, table=True):
    __tablename__ = "posts"
    
    id: str = Field(primary_key=True, max_length=50, sa_column=Column(Text, primary_key=True))
    numeric_id: int = Field(sa_column=Column(BigInteger, index=True))
    title: str = Field(max_length=200, sa_column=Column(Text, nullable=False))
    author: str = Field(max_length=50, sa_column=Column(Text, nullable=False))
    content: str = Field(sa_column=Column(Text, nullable=False))
    password: str = Field(sa_column=Column(Text, nullable=False))
    views: int = Field(default=0)
    comment_count: int = Field(default=0)
    pinned: bool = Field(default=False)
    pinned_at: Optional[datetime] = Field(default=None)
    experience: Optional[str] = Field(default=None, max_length=20)    # "experienced" | "inexperienced"
    category: Optional[str] = Field(default=None, max_length=20)       # "question" | "info" | "chat"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class PostLike(SQLModel, table=True):
    __tablename__ = "post_likes"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    post_id: str = Field(foreign_key="posts.id", max_length=50, index=True)
    visitor_id: str = Field(max_length=100, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        # UNIQUE(post_id, visitor_id) handled by Alembic migration or existing DB constraint
        pass


# app/models/comment.py
class Comment(SQLModel, table=True):
    __tablename__ = "comments"
    
    id: str = Field(primary_key=True, max_length=100, sa_column=Column(Text, primary_key=True))
    post_id: str = Field(foreign_key="posts.id", max_length=50, index=True)
    author: str = Field(max_length=50, sa_column=Column(Text, nullable=False))
    content: str = Field(sa_column=Column(Text, nullable=False))
    password: str = Field(sa_column=Column(Text, nullable=False))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# app/models/inquiry.py
from enum import Enum

class InquiryStatus(str, Enum):
    PENDING = "pending"
    CONTACTED = "contacted"
    COMPLETED = "completed"

class Inquiry(SQLModel, table=True):
    __tablename__ = "inquiries"
    
    id: str = Field(primary_key=True, max_length=50, sa_column=Column(Text, primary_key=True))
    name: str = Field(max_length=100, sa_column=Column(Text, nullable=False))
    email: str = Field(max_length=200, sa_column=Column(Text, nullable=False))
    phone: str = Field(max_length=30, sa_column=Column(Text, nullable=False))
    age: int = Field(ge=18, le=30)
    preferred_date: Optional[str] = Field(default=None, max_length=20)
    plan: Optional[str] = Field(default=None, max_length=50)
    message: str = Field(default="", max_length=2000)
    status: InquiryStatus = Field(default=InquiryStatus.PENDING)
    admin_note: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# app/models/article.py
from typing import Any

class ArticleLocaleContent(SQLModel):
    """Typed structure for the ja/ko JSONB columns."""
    title: str
    category: str
    excerpt: str = ""
    content: str = ""           # HTML string
    imageAlt: str = ""
    author: str = ""
    readTime: str = ""
    tags: list[str] = []

class Article(SQLModel, table=True):
    __tablename__ = "articles"
    
    id: str = Field(primary_key=True, max_length=100, sa_column=Column(Text, primary_key=True))
    image_url: Optional[str] = Field(default=None)   # URL or "storage:path"
    date: Optional[str] = Field(default=None, max_length=10)  # "YYYY-MM-DD"
    ja: dict[str, Any] = Field(sa_column=Column(JSONB, nullable=False))   # ArticleLocaleContent shape
    ko: Optional[dict[str, Any]] = Field(default=None, sa_column=Column(JSONB))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
```

### 2-2. Pydantic Request/Response Schemas (ALL strictly typed)

```python
# app/schemas/common.py
from pydantic import BaseModel

class SuccessResponse(BaseModel):
    success: bool = True
    message: str

class ErrorResponse(BaseModel):
    error: str
    details: str | None = None

class PaginatedMeta(BaseModel):
    count: int
    total: int
    total_pages: int
    current_page: int
    limit: int


# app/schemas/post.py
from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field, field_validator

class PostCreate(BaseModel):
    author: str = Field(min_length=1, max_length=50)
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1, max_length=10000)
    password: str = Field(min_length=4, max_length=50)
    experience: Optional[Literal["experienced", "inexperienced"]] = None
    category: Optional[Literal["question", "info", "chat"]] = None

class PostUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    content: Optional[str] = Field(default=None, min_length=1, max_length=10000)
    password: str = Field(min_length=4, max_length=50)

class PostResponse(BaseModel):
    id: str
    numeric_id: int
    title: str
    author: str
    content: str
    views: int
    comments: int              # mapped from comment_count
    pinned: bool
    pinned_at: Optional[datetime]
    experience: Optional[str]
    category: Optional[str]
    created_at: datetime
    updated_at: datetime

class PostListResponse(BaseModel):
    success: bool = True
    posts: list[PostResponse]
    count: int
    total: int
    total_pages: int
    current_page: int
    limit: int

class PostDeleteRequest(BaseModel):
    password: Optional[str] = None
    is_admin: bool = False

class PasswordVerifyRequest(BaseModel):
    password: str = Field(min_length=1)

class LikeToggleRequest(BaseModel):
    visitor_id: str = Field(alias="visitorId", min_length=8)

class LikeResponse(BaseModel):
    success: bool = True
    liked: bool
    likes: int

class BulkLikesRequest(BaseModel):
    post_ids: list[str] = Field(alias="postIds", max_length=100)

class BulkLikesResponse(BaseModel):
    success: bool = True
    likes: dict[str, int]

class PostSortField(str, Enum):
    NEWEST = "newest"
    OLDEST = "oldest"
    LIKES = "likes"
    VIEWS = "views"
    COMMENTS = "comments"

class PostSearchType(str, Enum):
    TITLE = "title"
    AUTHOR = "author"
    CONTENT = "content"

class PostCategoryFilter(str, Enum):
    QUESTION = "question"
    INFO = "info"
    CHAT = "chat"


# app/schemas/comment.py
class CommentCreate(BaseModel):
    author: str = Field(min_length=1, max_length=50)
    content: str = Field(min_length=1, max_length=5000)
    password: str = Field(min_length=4, max_length=50)

class CommentUpdate(BaseModel):
    content: str = Field(min_length=1, max_length=5000)
    password: str = Field(min_length=4, max_length=50)

class CommentResponse(BaseModel):
    id: str
    post_id: str
    author: str
    content: str
    created_at: datetime
    updated_at: datetime

class CommentListResponse(BaseModel):
    success: bool = True
    comments: list[CommentResponse]
    count: int


# app/schemas/inquiry.py
from pydantic import EmailStr

class InquiryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    phone: str = Field(min_length=10, max_length=20)
    age: int = Field(ge=18, le=30)
    preferred_date: str = Field(alias="preferredDate")
    plan: str
    message: str = Field(default="", max_length=2000)

    @field_validator("phone")
    @classmethod
    def validate_japanese_phone(cls, v: str) -> str:
        import re
        cleaned = re.sub(r"[\s\-()]", "", v)
        patterns = [
            r"^0[6-9]0\d{8}$",        # Mobile
            r"^\+?81[6-9]0\d{8}$",     # International mobile
            r"^0\d{9,10}$",            # Landline
        ]
        if not any(re.match(p, cleaned) for p in patterns):
            raise ValueError("有効な電話番号を入力してください")
        return v

class InquiryResponse(BaseModel):
    id: str
    name: str
    email: str
    phone: str
    age: int
    preferred_date: Optional[str]
    plan: Optional[str]
    message: str
    status: str
    admin_note: Optional[str]
    created_at: datetime
    updated_at: datetime

class InquiryStatusUpdate(BaseModel):
    status: Literal["pending", "contacted", "completed"]
    admin_note: Optional[str] = None


# app/schemas/article.py
class ArticleLocaleInput(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    category: str = Field(min_length=1, max_length=50)
    excerpt: str = Field(default="", max_length=500)
    content: str = Field(default="")              # HTML
    image_alt: str = Field(default="", alias="imageAlt", max_length=200)
    author: str = Field(default="", max_length=100)
    read_time: str = Field(default="", alias="readTime", max_length=20)
    tags: list[str] = Field(default_factory=list, max_length=20)

class ArticleCreate(BaseModel):
    id: str = Field(min_length=1, max_length=100)   # slug
    ja: ArticleLocaleInput
    ko: Optional[ArticleLocaleInput] = None
    image_url: Optional[str] = Field(default=None, alias="imageUrl")
    date: Optional[str] = None                       # "YYYY-MM-DD"

class ArticleUpdate(BaseModel):
    ja: Optional[ArticleLocaleInput] = None
    ko: Optional[ArticleLocaleInput] = None
    image_url: Optional[str] = Field(default=None, alias="imageUrl")
    date: Optional[str] = None

class ArticleResponse(BaseModel):
    id: str
    image_url: Optional[str]
    image_url_raw: Optional[str] = None   # original "storage:..." value
    date: Optional[str]
    ja: dict[str, Any]
    ko: Optional[dict[str, Any]]
    created_at: datetime
    updated_at: datetime

class ArticleListResponse(BaseModel):
    success: bool = True
    articles: list[ArticleResponse]
    count: int


# app/schemas/admin.py
class AdminLoginRequest(BaseModel):
    password: str = Field(min_length=1)

class AdminLoginResponse(BaseModel):
    success: bool = True
    authenticated: bool = True
    token: str

class AdminStatsResponse(BaseModel):
    success: bool = True
    stats: "AdminStats"

class AdminStats(BaseModel):
    total_inquiries: int
    pending_inquiries: int
    contacted_inquiries: int
    completed_inquiries: int
    total_posts: int
    total_views: int
    total_comments: int


# app/schemas/config.py
class SiteConfigResponse(BaseModel):
    ga_measurement_id: str = Field(alias="gaMeasurementId")
    verification: "VerificationConfig"

class VerificationConfig(BaseModel):
    google: Optional[str] = None
    naver: Optional[str] = None
```

---

## Phase 3: Backend - Services & Routers (3-4 days)

### 3-1. Auth Service (JWT + Password Hashing)
```python
# app/services/auth.py
import hashlib
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import jwt, JWTError
from passlib.context import CryptContext

from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ── JWT ──

def create_admin_token() -> str:
    payload = {
        "role": "admin",
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(hours=settings.jwt_expire_hours),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

def verify_admin_token(token: str) -> bool:
    try:
        payload: dict[str, str] = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
        return payload.get("role") == "admin"
    except JWTError:
        return False

# ── Password Hashing ──

def hash_password(password: str) -> str:
    """Hash with bcrypt (new standard)."""
    return pwd_context.hash(password)

def verify_password(plain: str, stored_hash: str) -> bool:
    """
    Verify password against stored hash.
    Supports three formats for backward compatibility:
    1. bcrypt hash ($2b$...)
    2. SHA-256 salted (saltHex:hashHex) — legacy from Hono/Deno
    3. Plaintext — legacy from early development
    """
    # Format 1: bcrypt
    if stored_hash.startswith("$2b$") or stored_hash.startswith("$2a$"):
        return pwd_context.verify(plain, stored_hash)
    
    # Format 2: SHA-256 salt:hash (legacy Hono)
    if ":" in stored_hash and len(stored_hash.split(":")) == 2:
        salt_hex, expected_hash = stored_hash.split(":")
        data = (salt_hex + plain).encode("utf-8")
        computed = hashlib.sha256(data).hexdigest()
        return computed == expected_hash
    
    # Format 3: Plaintext (legacy)
    return plain == stored_hash

def needs_rehash(stored_hash: str) -> bool:
    """Check if hash should be upgraded to bcrypt."""
    return not (stored_hash.startswith("$2b$") or stored_hash.startswith("$2a$"))
```

### 3-2. Spam Detection Service
```python
# app/services/spam.py
import re
from pydantic import BaseModel

class SpamCheckResult(BaseModel):
    is_spam: bool
    reason: str | None = None

SPAM_URL_THRESHOLD: int = 3

SPAM_KEYWORDS: re.Pattern[str] = re.compile(
    r"\b(casino|gambling|viagra|cialis|forex|crypto\s*trading|click\s*here|free\s*money|"
    r"buy\s*now|limited\s*offer|カジノ|ギャンブル|出会い系|副業|簡単に稼|即金|アダルト)\b",
    re.IGNORECASE,
)

def check_spam(content: str) -> SpamCheckResult:
    if not content:
        return SpamCheckResult(is_spam=False)
    
    # URL density
    urls: list[str] = re.findall(r"https?://\S+", content, re.IGNORECASE)
    if len(urls) > SPAM_URL_THRESHOLD:
        return SpamCheckResult(is_spam=True, reason=f"URLが多すぎます ({len(urls)}個検出)")
    
    # Excessive repetition
    if re.search(r"(.)\1{10,}", content):
        return SpamCheckResult(is_spam=True, reason="同じ文字の過度な繰り返しが検出されました")
    
    # Spam keywords (2+ matches)
    keyword_matches: list[str] = SPAM_KEYWORDS.findall(content)
    if len(keyword_matches) >= 2:
        return SpamCheckResult(is_spam=True, reason="スパムの可能性があるコンテンツが検出されました")
    
    # Identical repeated lines
    lines: list[str] = [line.strip().lower() for line in content.split("\n") if line.strip()]
    if len(lines) >= 5 and len(set(lines)) == 1:
        return SpamCheckResult(is_spam=True, reason="同じ内容の繰り返しが検出されました")
    
    return SpamCheckResult(is_spam=False)
```

### 3-3. Rate Limiting (slowapi)
```python
# app/services/rate_limit.py
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

# Usage in routers:
# @router.post("/posts")
# @limiter.limit("5/minute")
# async def create_post(request: Request, ...):
```

### 3-4. Router Implementation (Example: Posts)
```python
# app/routers/posts.py
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, func, col

from app.database import get_db
from app.dependencies import get_admin_token_optional
from app.models.post import Post, PostLike
from app.schemas.post import (
    PostCreate, PostUpdate, PostResponse, PostListResponse,
    PostDeleteRequest, PasswordVerifyRequest,
    LikeToggleRequest, LikeResponse, BulkLikesRequest, BulkLikesResponse,
    PostSortField, PostSearchType, PostCategoryFilter,
)
from app.services.auth import hash_password, verify_password, needs_rehash
from app.services.spam import check_spam
from app.services.sanitize import sanitize_text
from app.services.rate_limit import limiter

router = APIRouter(prefix="/api/posts", tags=["posts"])

def post_to_response(post: Post) -> PostResponse:
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

@router.get("", response_model=PostListResponse)
async def list_posts(
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: str = Query("", max_length=200),
    search_type: PostSearchType = Query(PostSearchType.TITLE, alias="searchType"),
    category: Optional[PostCategoryFilter] = Query(None),
    sort: PostSortField = Query(PostSortField.NEWEST),
) -> PostListResponse:
    ...  # Full implementation with pinned-first, search, filter, sort, pagination

@router.post("", response_model=PostResponse, status_code=201)
@limiter.limit("5/minute")
async def create_post(
    request: Request,
    body: PostCreate,
    db: AsyncSession = Depends(get_db),
) -> PostResponse:
    # Sanitize, spam check, hash password, insert, return
    ...
```

### 3-5. Router -> Endpoint Mapping (Complete)
```
app/routers/posts.py
  GET    /api/posts                        -> list_posts()
  POST   /api/posts                        -> create_post()
  PUT    /api/posts/{post_id}              -> update_post()
  DELETE /api/posts/{post_id}              -> delete_post()
  POST   /api/posts/{post_id}/view         -> increment_view()
  POST   /api/posts/{post_id}/like         -> toggle_like()
  GET    /api/posts/{post_id}/likes        -> get_like_status()
  POST   /api/posts/likes/bulk             -> bulk_like_counts()
  POST   /api/posts/{post_id}/verify-password -> verify_post_password()
  POST   /api/posts/{post_id}/pin          -> toggle_pin()   [admin]
  GET    /api/posts/{post_id}/comments     -> list_comments()
  POST   /api/posts/{post_id}/comments     -> create_comment()

app/routers/comments.py
  PUT    /api/comments/{comment_id}              -> update_comment()
  DELETE /api/comments/{comment_id}              -> delete_comment()
  POST   /api/comments/{comment_id}/verify-password -> verify_comment_password()

app/routers/inquiries.py
  POST   /api/inquiries                    -> submit_inquiry()
  GET    /api/inquiries                    -> list_inquiries()      [admin]
  PUT    /api/inquiries/{id}/status        -> update_status()       [admin]
  DELETE /api/inquiries/{id}               -> delete_inquiry()      [admin]

app/routers/articles.py
  GET    /api/articles                     -> list_articles()
  GET    /api/articles/{id}                -> get_article()
  POST   /api/articles                     -> create_article()      [admin]
  PUT    /api/articles/{id}                -> update_article()      [admin]
  DELETE /api/articles/{id}                -> delete_article()      [admin]

app/routers/admin.py
  POST   /api/admin/login                  -> admin_login()
  GET    /api/admin/stats                  -> get_stats()           [admin]
  POST   /api/admin/upload-image           -> upload_image()        [admin]
  POST   /api/admin/delete-image           -> delete_image()        [admin]
  DELETE /api/admin/cleanup-kv-likes       -> cleanup_kv_likes()    [admin]

app/routers/config.py
  GET    /api/config                       -> get_site_config()
```

### 3-6. Admin Dependency
```python
# app/dependencies.py
from fastapi import Header, HTTPException
from app.services.auth import verify_admin_token

async def require_admin(x_admin_token: str = Header(...)) -> bool:
    if not verify_admin_token(x_admin_token):
        raise HTTPException(status_code=401, detail="管理者認証が必要です")
    return True

async def get_admin_token_optional(
    x_admin_token: str | None = Header(default=None),
) -> bool:
    if x_admin_token and verify_admin_token(x_admin_token):
        return True
    return False
```

### 3-7. FastAPI Main App
```python
# app/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.services.rate_limit import limiter
from app.routers import posts, comments, inquiries, articles, admin, config

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure storage bucket exists
    yield
    # Shutdown: cleanup

app = FastAPI(title="Moku API", version="2.0.0", lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(posts.router)
app.include_router(comments.router)
app.include_router(inquiries.router)
app.include_router(articles.router)
app.include_router(admin.router)
app.include_router(config.router)

@app.get("/api/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
```

---

## Phase 4: Frontend - Next.js 15 Project (3-5 days)

### 4-1. Init Project
```bash
npx create-next-app@latest moku-web --typescript --tailwind --app --src-dir
```

### 4-2. Frontend Dependencies
```bash
# UI
pnpm add @radix-ui/react-accordion @radix-ui/react-dialog @radix-ui/react-select \
  @radix-ui/react-tabs @radix-ui/react-tooltip @radix-ui/react-popover \
  @radix-ui/react-dropdown-menu @radix-ui/react-checkbox @radix-ui/react-switch \
  @radix-ui/react-separator @radix-ui/react-avatar @radix-ui/react-label \
  @radix-ui/react-scroll-area @radix-ui/react-slot
pnpm add class-variance-authority clsx tailwind-merge tw-animate-css
pnpm add lucide-react sonner motion date-fns dompurify
pnpm add i18next react-i18next
pnpm add react-hook-form

# REMOVED from current stack (no longer needed):
# react-router          -> Next.js file-based routing
# react-helmet-async    -> Next.js Metadata API
# @supabase/supabase-js -> Backend handles all DB access now
# jose                  -> Backend handles JWT
```

### 4-3. Frontend API Client (typed)
```typescript
// src/lib/api.ts
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public details?: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const url = `${API_BASE}${path}`;
  const res = await fetch(url, {
    headers: { "Content-Type": "application/json", ...options.headers },
    ...options,
  });
  const data = await res.json();
  if (!res.ok) throw new ApiError(data.error || data.detail, res.status, data.details);
  return data as T;
}

// Typed convenience wrappers
export const api = {
  get: <T>(path: string, init?: RequestInit) => apiFetch<T>(path, { method: "GET", ...init }),
  post: <T>(path: string, body?: unknown, init?: RequestInit) =>
    apiFetch<T>(path, { method: "POST", body: JSON.stringify(body), ...init }),
  put: <T>(path: string, body?: unknown, init?: RequestInit) =>
    apiFetch<T>(path, { method: "PUT", body: JSON.stringify(body), ...init }),
  del: <T>(path: string, body?: unknown, init?: RequestInit) =>
    apiFetch<T>(path, { method: "DELETE", body: body ? JSON.stringify(body) : undefined, ...init }),
};
```

### 4-4. Frontend TypeScript Types (mirror Pydantic schemas)
```typescript
// src/types/post.ts
export interface PostResponse {
  id: string;
  numericId: number;
  title: string;
  author: string;
  content: string;
  views: number;
  comments: number;
  pinned: boolean;
  pinnedAt: string | null;
  experience: "experienced" | "inexperienced" | null;
  category: "question" | "info" | "chat" | null;
  createdAt: string;
  updatedAt: string;
}

export interface PostListResponse {
  success: boolean;
  posts: PostResponse[];
  count: number;
  total: number;
  totalPages: number;
  currentPage: number;
  limit: number;
}

export interface PostCreateRequest {
  author: string;
  title: string;
  content: string;
  password: string;
  experience?: "experienced" | "inexperienced";
  category?: "question" | "info" | "chat";
}

export type PostSearchType = "title" | "author" | "content";
export type PostSortField = "newest" | "oldest" | "likes" | "views" | "comments";
export type PostCategoryFilter = "question" | "info" | "chat";

// src/types/comment.ts
export interface CommentResponse {
  id: string;
  postId: string;
  author: string;
  content: string;
  createdAt: string;
  updatedAt: string;
}

// src/types/inquiry.ts
export interface InquiryCreateRequest {
  name: string;
  email: string;
  phone: string;
  age: number;
  preferredDate: string;
  plan: string;
  message?: string;
}

// src/types/article.ts
export interface ArticleLocale {
  title: string;
  category: string;
  excerpt: string;
  content: string;        // HTML
  imageAlt: string;
  author: string;
  readTime: string;
  tags: string[];
}

export interface ArticleResponse {
  id: string;
  imageUrl: string | null;
  date: string | null;
  ja: ArticleLocale;
  ko: ArticleLocale | null;
  createdAt: string;
  updatedAt: string;
}

// src/types/admin.ts
export interface AdminStats {
  totalInquiries: number;
  pendingInquiries: number;
  contactedInquiries: number;
  completedInquiries: number;
  totalPosts: number;
  totalViews: number;
  totalComments: number;
}
```

### 4-5. Route Mapping
```
CURRENT (React Router)              NEXT.JS (App Router)
───────────────────────             ─────────────────────
/                                   app/page.tsx (SSG + ISR)
/archive                            app/archive/page.tsx (SSG + ISR)
/archive/:id                        app/archive/[id]/page.tsx (SSG + generateStaticParams)
/guideline                          app/guideline/page.tsx (SSG)
/community                          app/community/page.tsx ('use client')
/partners                           app/partners/page.tsx (SSG + ISR)
/admin                              app/admin/page.tsx ('use client')
/privacy                            app/privacy/page.tsx (SSG)
/terms                              app/terms/page.tsx (SSG)
/tokushoho                          app/tokushoho/page.tsx (SSG)
*                                   app/not-found.tsx
```

### 4-6. SEO (Next.js Metadata API)
```tsx
// app/archive/[id]/page.tsx
import type { Metadata } from "next";

export async function generateMetadata({ params }: { params: { id: string } }): Promise<Metadata> {
  const res = await fetch(`${API_BASE}/api/articles/${params.id}`);
  const { article }: { article: ArticleResponse } = await res.json();
  return {
    title: `${article.ja.title} | Moku`,
    description: article.ja.excerpt,
    openGraph: { images: article.imageUrl ? [article.imageUrl] : [] },
  };
}

// app/sitemap.ts
export default async function sitemap(): Promise<MetadataRoute.Sitemap> { ... }

// app/robots.ts
export default function robots(): MetadataRoute.Robots { ... }
```

---

## Phase 5: i18n, Design Tokens, Fonts (1 day)

### 5-1. i18n (keep i18next client-side)
- Copy `ja.ts`, `ko.ts`, `en.ts` locale files as-is
- Same lazy-loading pattern: ja bundled, ko/en dynamic import
- Wrap in `I18nextProvider` in layout.tsx

### 5-2. Design Tokens
- Copy all CSS variables from current `theme.css` into `globals.css`
- No changes to color values or token names

### 5-3. Fonts
```tsx
// app/layout.tsx
import { Noto_Sans_JP, Noto_Sans_KR, M_PLUS_1p } from "next/font/google";

const notoSansJP = Noto_Sans_JP({ subsets: ["latin"], weight: ["400", "500", "700"], display: "swap" });
const notoSansKR = Noto_Sans_KR({ subsets: ["latin"], weight: ["400", "500", "700"], display: "swap" });
const mPlus1p = M_PLUS_1p({ subsets: ["latin"], weight: ["400", "500", "700"], display: "swap" });
```

---

## Phase 6: Testing & Deployment (2-3 days)

### 6-1. Backend Testing
```python
# tests/test_posts.py
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

@pytest.mark.asyncio
async def test_create_post(client: AsyncClient) -> None:
    response = await client.post("/api/posts", json={
        "author": "テスト太郎",
        "title": "テスト投稿",
        "content": "テスト内容です",
        "password": "test1234",
        "category": "question",
    })
    assert response.status_code == 201
    data: dict = response.json()
    assert data["success"] is True
    assert data["post"]["title"] == "テスト投稿"
```

### 6-2. Type Checking
```bash
# Backend
mypy app/ --strict
ruff check app/

# Frontend
tsc --noEmit
```

### 6-3. Deployment
```
Backend:  Railway / Fly.io / Render
          Docker image: python:3.12-slim + uvicorn
          Env vars: DATABASE_URL, SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, MOKU_ADMIN_PASSWORD, ...

Frontend: Vercel
          NEXT_PUBLIC_API_URL=https://api.moku.com
          
Database: Supabase PostgreSQL (same instance, apply Alembic migrations for any schema changes)
Storage:  Supabase Storage (same bucket)
Domain:   moku.com -> Vercel, api.moku.com -> Backend
```

---

## Total Estimated Timeline

| Phase | Duration | Description |
|-------|----------|-------------|
| 0 | 1-2 days | Data export, schema doc, env backup |
| 1 | 2 days | FastAPI scaffold, config, database setup |
| 2 | 2-3 days | SQLModel models + Pydantic schemas (full type coverage) |
| 3 | 3-4 days | Services + Routers (25+ endpoints, auth, spam, storage) |
| 4 | 3-5 days | Next.js frontend (15 pages + 30 UI components) |
| 5 | 1 day | i18n, design tokens, fonts |
| 6 | 2-3 days | Testing (pytest + mypy + tsc), deployment |
| **Total** | **14-20 days** | |
