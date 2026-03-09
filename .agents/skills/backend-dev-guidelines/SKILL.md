---
name: backend-dev-guidelines
description: "Backend development standards for Python + FastAPI + SQLModel + async SQLAlchemy microservices. Covers layered architecture, Pydantic validation, async DB patterns, JWT auth with DB blacklist, rate limiting, Sentry integration, caching, structured logging, and pytest testing."
risk: low
source: custom
date_added: "2026-03-09"
date_updated: "2026-03-10"
---

# Backend Development Guidelines

**(Python · FastAPI · SQLModel · Async SQLAlchemy · Railway)**

You are a **senior backend engineer** operating production-grade FastAPI services under strict architectural and reliability constraints.

Your goal is to build **predictable, observable, and maintainable backend systems** using:

* Layered architecture (Routers → Services → Models)
* Pydantic-first validation & serialization (CamelModel for responses)
* Async-first database access (asyncpg + SQLAlchemy)
* Centralized configuration via `pydantic-settings`
* In-memory LRU cache + PostgreSQL-backed JWT blacklist
* Sentry integration for error monitoring
* Strong typing enforced by `mypy --strict`

This skill defines **how backend code must be written**, not merely suggestions.

---

## 1. When to Apply

Automatically applies when working on:

* FastAPI routers & endpoint handlers
* SQLModel / SQLAlchemy models
* Pydantic schemas (request/response)
* Service layer business logic
* Database queries & transactions
* Auth, security, middleware
* Configuration management
* Caching & JWT blacklist
* Sentry integration
* Backend tests & CI

---

## 2. Rule Categories by Priority

| Priority | Category | Impact | Resource |
|----------|----------|--------|----------|
| 1 | Layered Architecture | CRITICAL | [architecture-overview.md](resources/architecture-overview.md) |
| 2 | Type Safety (mypy strict) | CRITICAL | [models-and-schemas.md](resources/models-and-schemas.md) |
| 3 | Input Validation | HIGH | [validation-and-sanitize.md](resources/validation-and-sanitize.md) |
| 4 | Error Handling & Logging | HIGH | [error-handling.md](resources/error-handling.md) |
| 5 | Security | HIGH | [auth-and-security.md](resources/auth-and-security.md) |
| 6 | Database Patterns | MEDIUM | [database-patterns.md](resources/database-patterns.md) |
| 7 | Caching & Blacklist | MEDIUM | [caching-and-blacklist.md](resources/caching-and-blacklist.md) |
| 8 | Configuration | MEDIUM | [config-and-env.md](resources/config-and-env.md) |
| 9 | Sentry & Observability | MEDIUM | [sentry-and-observability.md](resources/sentry-and-observability.md) |
| 10 | Testing | MEDIUM | [testing-guide.md](resources/testing-guide.md) |
| 11 | Deployment | LOW | [deployment.md](resources/deployment.md) |

---

## 3. Core Architecture Doctrine (Non-Negotiable)

### Layered Architecture Is Mandatory

```
Routers → Services → Models/Repositories → Database
           ↕
        Schemas (Pydantic)
```

* **Routers** — HTTP handling only: parse request, call service, return response
* **Services** — Business logic, framework-agnostic, unit-testable
* **Models** — SQLModel table definitions, no business logic
* **Schemas** — Pydantic request/response models, validation rules (CamelModel for responses)
* **Middleware** — Cross-cutting concerns (Cache-Control headers)
* No layer skipping. No cross-layer leakage.

### Routers Only Route

```python
# ❌ NEVER — business logic in router
@router.post("")
async def create_post(body: PostCreate, session: AsyncSession = Depends(get_session)):
    spam_result = check_spam(body.content)   # business logic here
    post = Post(id=generate_id(), ...)       # model creation here
    session.add(post)                        # DB access here
    await session.commit()
    return {"success": True, "post": post}

# ✅ ALWAYS — delegate to service
@router.post("", response_model=PostCreateResponse, status_code=201)
async def create_post(body: PostCreate, session: AsyncSession = Depends(get_session)):
    result = await post_service.create(session, body)
    return result
```

### Validate All External Input with Pydantic

* Request bodies → Pydantic `BaseModel`
* Query params → `Query()` with constraints
* Path params → type annotations + validation
* **No `dict[str, Any]` request bodies** — always use typed schemas

```python
# ❌ NEVER
async def delete_image(body: dict[str, str]): ...

# ✅ ALWAYS
class DeleteImageRequest(BaseModel):
    path: str = Field(min_length=1)

async def delete_image(body: DeleteImageRequest): ...
```

### All Endpoints Must Have `response_model`

```python
# ❌ NEVER
@router.post("") 
async def create(body: CreateReq, ...) -> dict[str, Any]: ...

# ✅ ALWAYS
@router.post("", response_model=CreateResponse, status_code=201)
async def create(body: CreateReq, ...) -> CreateResponse: ...
```

### Response Schemas Inherit CamelModel

```python
from app.schemas.common import CamelModel

# ✅ All response schemas use CamelModel for automatic camelCase serialization
class PostResponse(CamelModel):
    id: str
    numeric_id: int
    # snake_case fields → serialized as camelCase JSON
```

### Settings Is the Only Config Source

```python
# ❌ NEVER
import os
os.environ["JWT_SECRET"]

# ✅ ALWAYS
from app.config import settings
settings.jwt_secret_key
```

---

## 4. Directory Structure (Canonical)

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app, lifespan, middleware, router registration
│   ├── config.py             # pydantic-settings Settings singleton
│   ├── database.py           # Async engine & session factory (URL sanitization)
│   ├── dependencies.py       # FastAPI Depends (auth guards: require_admin, get_admin_token_optional)
│   ├── sentry.py             # Sentry SDK init, event filtering, helpers
│   ├── middleware/            # Custom middleware
│   │   ├── __init__.py       # CacheHeaderMiddleware (Cache-Control by route)
│   ├── models/               # SQLModel table definitions
│   │   ├── __init__.py       # Re-export all models
│   │   ├── post.py           # Post, PostLike, PostCategory, ExperienceType
│   │   ├── comment.py        # Comment (with parent_id for replies)
│   │   ├── article.py        # Article (JSONB locale content)
│   │   ├── inquiry.py        # Inquiry, InquiryStatus
│   │   └── token_blacklist.py # TokenBlacklist (JWT revocation via PostgreSQL)
│   ├── schemas/              # Pydantic request/response models (CamelModel base)
│   │   ├── __init__.py       # Re-export all schemas
│   │   ├── common.py         # CamelModel, SuccessResponse, ErrorResponse, HealthResponse
│   │   ├── post.py
│   │   ├── comment.py
│   │   ├── article.py
│   │   ├── inquiry.py
│   │   ├── admin.py
│   │   └── config.py
│   ├── services/             # Business logic (framework-agnostic)
│   │   ├── __init__.py       # Re-export public API (auth, exceptions, limiter, etc.)
│   │   ├── post_service.py
│   │   ├── comment_service.py
│   │   ├── article_service.py
│   │   ├── inquiry_service.py
│   │   ├── admin_service.py
│   │   ├── auth.py           # JWT creation/verification, password hashing (bcrypt + legacy)
│   │   ├── cache.py          # In-memory LRU cache + PostgreSQL JWT blacklist
│   │   ├── exceptions.py     # DomainError hierarchy (centralized)
│   │   ├── storage.py        # Cloudflare R2 via aioboto3
│   │   ├── sanitize.py       # XSS sanitization
│   │   ├── spam.py           # Spam detection
│   │   └── rate_limit.py     # SlowAPI limiter singleton
│   └── routers/              # FastAPI routers (HTTP layer only)
│       ├── __init__.py
│       ├── posts.py
│       ├── comments.py
│       ├── articles.py
│       ├── inquiries.py
│       ├── admin.py
│       └── config.py
├── alembic/                  # Alembic migrations
│   ├── env.py
│   └── versions/
├── tests/                    # pytest tests
│   ├── conftest.py
│   └── ...
├── alembic.ini
├── requirements.txt
├── requirements-dev.txt
├── mypy.ini
├── pytest.ini
└── Dockerfile
```

---

## 5. Naming Conventions (Strict)

| Layer | Convention | Example |
|-------|-----------|---------| 
| Model | `PascalCase` class, `snake_case` file | `Post` in `post.py` |
| Schema | `PascalCase` class, `snake_case` file | `PostCreate` in `post.py` |
| Service | `snake_case` module with functions/class | `post_service.py` |
| Router | `snake_case` module, `router` variable | `posts.py` |
| Middleware | `PascalCase` class, `snake_case` file | `CacheHeaderMiddleware` in `__init__.py` |
| Utils | `snake_case` module & functions | `sanitize.py` |

---

## 6. Anti-Patterns (Immediate Rejection)

❌ Business logic in routers  
❌ `dict[str, Any]` as request body type  
❌ Missing `response_model` on endpoints  
❌ `datetime.utcnow()` (deprecated in Python 3.12)  
❌ `process.env` / `os.environ` instead of `settings`  
❌ `type: ignore` without explanation comment  
❌ `except Exception: pass` (swallowed errors)  
❌ Synchronous I/O inside async functions  
❌ Missing rate limiting on public endpoints  
❌ Admin actions validated by request body fields  
❌ `HTTPException` raised in service layer  
❌ Response schemas not inheriting `CamelModel`  
❌ Timezone-aware datetimes stored in TIMESTAMP WITHOUT TIME ZONE columns  

---

## 7. Operator Validation Checklist

Before finalizing backend work:

* [ ] Layered architecture respected (router → service → model)
* [ ] All inputs validated with Pydantic schemas
* [ ] All endpoints have `response_model`
* [ ] Response schemas inherit `CamelModel`
* [ ] `mypy --strict` passes
* [ ] Errors are logged, not swallowed
* [ ] Rate limiting on all public endpoints
* [ ] Admin endpoints use `Depends(require_admin)` only
* [ ] No deprecated APIs used
* [ ] Tests written for new/changed logic
* [ ] Sentry captures 5xx errors (4xx filtered)
* [ ] Datetimes are timezone-naive for asyncpg 0.30+ compatibility

---

## 8. Detailed Resources

Read individual resource files for in-depth rules and code examples:

| Resource | Coverage |
|----------|----------|
| [architecture-overview.md](resources/architecture-overview.md) | Directory structure, layer responsibilities, dependency flow |
| [routing-and-endpoints.md](resources/routing-and-endpoints.md) | Router patterns, path operations, dependency injection |
| [models-and-schemas.md](resources/models-and-schemas.md) | SQLModel tables, CamelModel, Pydantic schemas, type safety |
| [services-and-business.md](resources/services-and-business.md) | Service layer patterns, DomainError hierarchy, business logic separation |
| [database-patterns.md](resources/database-patterns.md) | Async sessions, URL sanitization, transactions, _utcnow() pattern |
| [auth-and-security.md](resources/auth-and-security.md) | JWT with blacklist, bcrypt, CORS, rate limiting, admin guards |
| [caching-and-blacklist.md](resources/caching-and-blacklist.md) | In-memory LRU cache, PostgreSQL JWT blacklist |
| [validation-and-sanitize.md](resources/validation-and-sanitize.md) | Input validation, XSS prevention, spam detection |
| [error-handling.md](resources/error-handling.md) | DomainError hierarchy, Sentry forwarding, structured logging |
| [sentry-and-observability.md](resources/sentry-and-observability.md) | Sentry SDK init, event filtering, breadcrumbs |
| [config-and-env.md](resources/config-and-env.md) | pydantic-settings, Cloudflare R2, environment management |
| [testing-guide.md](resources/testing-guide.md) | pytest-asyncio, httpx AsyncClient, fixtures |
| [deployment.md](resources/deployment.md) | Docker multi-stage, Railway, health/readiness probes |

---

## Skill Status

**Status:** Stable · Enforceable · Production-grade  
**Stack:** Python 3.12 · FastAPI · SQLModel · async SQLAlchemy · Pydantic v2 · asyncpg · Sentry  
**Hosting:** Railway (Docker) · PostgreSQL (Railway) · Cloudflare R2  
**Intended Use:** Production FastAPI services with real traffic and real risk
