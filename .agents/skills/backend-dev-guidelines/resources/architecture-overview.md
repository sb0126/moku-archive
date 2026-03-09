# Architecture Overview

## Layered Architecture

```
Routers (HTTP layer)
    ↓ calls
Services (Business logic)
    ↓ uses
Models (SQLModel tables) + Schemas (Pydantic DTOs)
    ↓ persists via
Database (async SQLAlchemy sessions)
```

### Layer Responsibilities

| Layer | Responsibility | May Import |
|-------|---------------|------------|
| **Routers** | Parse HTTP request, call service, format response | Services, Schemas, Dependencies |
| **Services** | Business rules, validation orchestration, transactions | Models, Schemas, other Services |
| **Models** | Table definitions, column constraints | Nothing (leaf) |
| **Schemas** | Request/response shapes, field validation (CamelModel) | Nothing (leaf) |
| **Dependencies** | Auth guards, session injection | Services, Config |
| **Middleware** | Cache-Control headers, cross-cutting concerns | Config |
| **Config** | Environment variable management | Nothing (leaf) |
| **Sentry** | Error monitoring, event filtering | Config |

### Rules

1. **No layer skipping** — Routers must not import Models directly for DB operations
2. **Services are framework-agnostic** — No `Request`, `Response`, or `HTTPException` in services
3. **Models have no methods** — Pure data containers (SQLModel tables)
4. **Schemas validate** — All constraints (min_length, regex, etc.) belong in schemas
5. **Services raise `DomainError`** — Not `HTTPException` (see `services/exceptions.py`)

## Directory Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # App factory, lifespan, middleware, Sentry init
│   ├── config.py             # Settings singleton (pydantic-settings)
│   ├── database.py           # Engine, session factory, URL sanitization
│   ├── dependencies.py       # Depends() callables (require_admin, get_admin_token_optional)
│   ├── sentry.py             # Sentry SDK init, before_send filter, helpers
│   ├── middleware/
│   │   └── __init__.py       # CacheHeaderMiddleware
│   ├── models/               # One file per aggregate
│   │   ├── __init__.py       # Re-export ALL models
│   │   ├── post.py           # Post, PostLike, PostCategory, ExperienceType
│   │   ├── comment.py        # Comment (with parent_id for nested replies)
│   │   ├── article.py        # Article (JSONB ja/ko locale content)
│   │   ├── inquiry.py        # Inquiry, InquiryStatus
│   │   └── token_blacklist.py # TokenBlacklist (PostgreSQL JWT revocation)
│   ├── schemas/              # One file per domain
│   │   ├── __init__.py       # Re-export ALL schemas
│   │   ├── common.py         # CamelModel base, SuccessResponse, ErrorResponse, HealthResponse
│   │   ├── post.py
│   │   ├── comment.py
│   │   ├── article.py
│   │   ├── inquiry.py
│   │   ├── admin.py
│   │   └── config.py
│   ├── services/             # Business logic modules
│   │   ├── __init__.py       # Re-export public API
│   │   ├── post_service.py
│   │   ├── comment_service.py
│   │   ├── article_service.py
│   │   ├── inquiry_service.py
│   │   ├── admin_service.py
│   │   ├── auth.py           # JWT + bcrypt + legacy password support
│   │   ├── cache.py          # In-memory LRU cache + PostgreSQL JWT blacklist
│   │   ├── exceptions.py     # DomainError hierarchy (centralized)
│   │   ├── storage.py        # Cloudflare R2 via aioboto3
│   │   ├── sanitize.py       # XSS sanitization
│   │   ├── spam.py           # Spam detection
│   │   └── rate_limit.py     # SlowAPI limiter singleton (in-memory)
│   └── routers/              # One file per API group
│       ├── __init__.py
│       ├── posts.py
│       ├── comments.py
│       ├── articles.py
│       ├── inquiries.py
│       ├── admin.py
│       └── config.py
├── alembic/
│   ├── env.py                # Dynamic DB URL from settings
│   └── versions/
├── tests/
│   ├── conftest.py           # Shared fixtures
│   └── ...
├── alembic.ini
├── requirements.txt
├── requirements-dev.txt
├── mypy.ini
├── pytest.ini
└── Dockerfile
```

## Dependency Flow

```mermaid
graph TD
    R[Routers] --> S[Services]
    R --> SC[Schemas]
    R --> D[Dependencies]
    S --> M[Models]
    S --> SC
    S --> EX[Exceptions]
    D --> S
    D --> C[Config]
    S --> C
    S --> CA[Cache/Blacklist]
    DB[database.py] --> C
    R --> DB
    MAIN[main.py] --> SENTRY[sentry.py]
    MAIN --> MW[Middleware]
    MW --> C
```

## Module Scope Rules

| Module | Max Lines | When to Split |
|--------|-----------|---------------|
| Router | ~200 | Split by sub-resource (e.g., post likes → separate router) |
| Service | ~300 | Split by domain concept |
| Schema | ~150 | Split when >10 models in a file |
| Model | ~100 | One file per DB table aggregate |
| Middleware | ~100 | One file per concern |
