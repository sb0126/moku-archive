---
name: backend-dev-guidelines
description: "Backend development standards for Python + FastAPI + SQLModel + async SQLAlchemy microservices. Covers layered architecture, Pydantic validation, async DB patterns, JWT auth, rate limiting, structured logging, and pytest testing."
risk: low
source: custom
date_added: "2026-03-09"
---

# Backend Development Guidelines

**(Python · FastAPI · SQLModel · Async SQLAlchemy)**

You are a **senior backend engineer** operating production-grade FastAPI services under strict architectural and reliability constraints.

Your goal is to build **predictable, observable, and maintainable backend systems** using:

* Layered architecture (Routers → Services → Models)
* Pydantic-first validation & serialization
* Async-first database access
* Centralized configuration via `pydantic-settings`
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
| 7 | Configuration | MEDIUM | [config-and-env.md](resources/config-and-env.md) |
| 8 | Testing | MEDIUM | [testing-guide.md](resources/testing-guide.md) |
| 9 | Deployment | LOW | [deployment.md](resources/deployment.md) |

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
* **Schemas** — Pydantic request/response models, validation rules
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
│   ├── database.py           # async engine & session factory
│   ├── dependencies.py       # FastAPI Depends (auth guards, etc.)
│   ├── models/               # SQLModel table definitions
│   │   ├── __init__.py       # re-export all models
│   │   ├── post.py
│   │   └── ...
│   ├── schemas/              # Pydantic request/response models
│   │   ├── __init__.py       # re-export all schemas
│   │   ├── post.py
│   │   └── ...
│   ├── services/             # Business logic (framework-agnostic)
│   │   ├── __init__.py
│   │   ├── post_service.py
│   │   └── ...
│   ├── routers/              # FastAPI routers (HTTP layer only)
│   │   ├── __init__.py
│   │   ├── posts.py
│   │   └── ...
│   └── utils/                # Pure utility functions
├── tests/                    # pytest tests
│   ├── conftest.py
│   ├── test_posts.py
│   └── ...
├── requirements.txt
├── mypy.ini
├── Dockerfile
└── .env.example
```

---

## 5. Naming Conventions (Strict)

| Layer | Convention | Example |
|-------|-----------|---------|
| Model | `PascalCase` class, `snake_case` file | `Post` in `post.py` |
| Schema | `PascalCase` class, `snake_case` file | `PostCreate` in `post.py` |
| Service | `snake_case` module with functions/class | `post_service.py` |
| Router | `snake_case` module, `router` variable | `posts.py` |
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

---

## 7. Operator Validation Checklist

Before finalizing backend work:

* [ ] Layered architecture respected (router → service → model)
* [ ] All inputs validated with Pydantic schemas
* [ ] All endpoints have `response_model`
* [ ] `mypy --strict` passes
* [ ] Errors are logged, not swallowed
* [ ] Rate limiting on all public endpoints
* [ ] Admin endpoints use `Depends(require_admin)` only
* [ ] No deprecated APIs used
* [ ] Tests written for new/changed logic

---

## 8. Detailed Resources

Read individual resource files for in-depth rules and code examples:

| Resource | Coverage |
|----------|----------|
| [architecture-overview.md](resources/architecture-overview.md) | Directory structure, layer responsibilities, dependency flow |
| [routing-and-endpoints.md](resources/routing-and-endpoints.md) | Router patterns, path operations, dependency injection |
| [models-and-schemas.md](resources/models-and-schemas.md) | SQLModel tables, Pydantic schemas, type safety |
| [services-and-business.md](resources/services-and-business.md) | Service layer patterns, business logic separation |
| [database-patterns.md](resources/database-patterns.md) | Async sessions, transactions, query optimization |
| [auth-and-security.md](resources/auth-and-security.md) | JWT, bcrypt, CORS, rate limiting, admin guards |
| [validation-and-sanitize.md](resources/validation-and-sanitize.md) | Input validation, XSS prevention, spam detection |
| [error-handling.md](resources/error-handling.md) | Exception hierarchy, structured logging, error responses |
| [config-and-env.md](resources/config-and-env.md) | pydantic-settings, environment management |
| [testing-guide.md](resources/testing-guide.md) | pytest-asyncio, httpx AsyncClient, fixtures |
| [deployment.md](resources/deployment.md) | Docker, health/readiness probes, production config |

---

## Skill Status

**Status:** Stable · Enforceable · Production-grade  
**Stack:** Python 3.12 · FastAPI · SQLModel · async SQLAlchemy · Pydantic v2  
**Intended Use:** Production FastAPI services with real traffic and real risk
