# Routing & Endpoints

## Router Structure

```python
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
    """Create a new post."""
    try:
        return await post_service.create(session, body)
    except DomainError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
```

## Rules

### 1. Every Endpoint Must Have `response_model`

```python
# ❌ NEVER
@router.post("")
async def create(...) -> dict[str, Any]: ...

# ✅ ALWAYS
@router.post("", response_model=CreateResponse, status_code=201)
async def create(...) -> CreateResponse: ...
```

### 2. Routers Must Not Contain Business Logic

Router functions should be 5-15 lines max:

```python
# ❌ BAD — logic in router (40+ lines)
@router.post("")
async def create_post(body: PostCreate, session: ...):
    author = sanitize_text(body.author)           # ← logic
    spam_result = check_spam(body.content)        # ← logic
    if spam_result.is_spam:                       # ← logic
        raise HTTPException(400, ...)
    max_id = await session.execute(...)           # ← DB access
    post = Post(id=generate_id(), ...)            # ← model creation
    session.add(post)                             # ← DB access
    await session.commit()                        # ← DB access
    return {"success": True, "post": post}

# ✅ GOOD — delegate to service
@router.post("", response_model=PostCreateResponse, status_code=201)
async def create_post(body: PostCreate, session: ...):
    try:
        return await post_service.create(session, body)
    except DomainError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
```

### 3. Use Correct HTTP Status Codes

| Operation | Method | Status | response_model |
|-----------|--------|--------|----------------|
| List | GET | 200 | `ListResponse` |
| Detail | GET | 200 | `DetailResponse` |
| Create | POST | 201 | `CreateResponse` |
| Update | PUT/PATCH | 200 | `UpdateResponse` |
| Delete | DELETE | 200 | `SuccessResponse` |
| Action | POST | 200 | action-specific |

### 4. Rate Limiting on All Public Endpoints

```python
from app.services import limiter

@router.post("", ...)
@limiter.limit("5/minute")   # ← required for mutation endpoints
async def create(request: Request, ...):
    ...

@router.get("", ...)
@limiter.limit("30/minute")   # ← required for read endpoints
async def list_items(request: Request, ...):
    ...
```

**Important:** `request: Request` parameter is required for SlowAPI to work.

### 5. Path Parameter Naming

```python
# ❌ Inconsistent
@router.get("/{id}")
@router.get("/{postId}")

# ✅ Consistent snake_case matching model
@router.get("/{post_id}")
```

### 6. Query Parameter Validation

```python
# ❌ No validation
@router.get("")
async def list_items(page: int, limit: int): ...

# ✅ With constraints
@router.get("")
async def list_items(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=100),
    search: str = Query(default="", max_length=200),
): ...
```

### 7. Dependency Injection for Auth

```python
# ❌ Auth check in function body
@router.delete("/{post_id}")
async def delete(post_id: str, body: DeleteReq, session: ...):
    if body.is_admin:  # ← SECURITY HOLE!
        ...

# ✅ Auth via Depends()
@router.delete("/{post_id}")
async def delete(
    post_id: str,
    body: DeleteReq,
    session: AsyncSession = Depends(get_session),
    is_admin: bool = Depends(get_admin_token_optional),
):
    if not is_admin:
        verify_ownership(body.password, ...)
```

### 8. DomainError → HTTPException Translation

All routers should catch `DomainError` and translate to HTTP:

```python
try:
    return await service.action(session, ...)
except DomainError as exc:
    raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
```

### 9. Registered Routers

All routers are registered in `main.py`:

```python
app.include_router(posts.router)      # /api/posts
app.include_router(comments.router)   # /api/comments
app.include_router(inquiries.router)  # /api/inquiries
app.include_router(articles.router)   # /api/articles
app.include_router(admin.router)      # /api/admin
app.include_router(config.router)     # /api/config
```
