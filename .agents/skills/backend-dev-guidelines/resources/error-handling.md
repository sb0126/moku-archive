# Error Handling

## Exception Hierarchy (Centralized in `services/exceptions.py`)

```python
# services/exceptions.py

class DomainError(Exception):
    """Base exception for all domain-level errors."""
    def __init__(self, message: str, *, status_code: int = 400) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class NotFoundError(DomainError):
    """Raised when a requested resource does not exist."""
    def __init__(self, message: str = "リソースが見つかりません") -> None:
        super().__init__(message, status_code=404)


class ForbiddenError(DomainError):
    """Raised when authentication succeeds but authorization fails."""
    def __init__(self, message: str = "パスワードが正しくありません") -> None:
        super().__init__(message, status_code=403)


class ConflictError(DomainError):
    """Raised when a unique-constraint would be violated."""
    def __init__(self, message: str = "リソースが既に存在します") -> None:
        super().__init__(message, status_code=409)


class ValidationError(DomainError):
    """Raised when input validation (beyond Pydantic) fails."""
    def __init__(self, message: str = "入力内容が無効です") -> None:
        super().__init__(message, status_code=400)


class SpamDetectedError(DomainError):
    """Raised when spam content is detected."""
    def __init__(self, message: str = "スパムが検出されました") -> None:
        super().__init__(message, status_code=400)
```

## Global Exception Handlers (in `main.py`)

### Rate Limit Handler

```python
from slowapi.errors import RateLimitExceeded

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """Return a JSON 429 with a Japanese message."""
    return JSONResponse(
        status_code=429,
        content={"error": "リクエストが多すぎます。しばらくしてからもう一度お試しください。"},
    )
```

### Unhandled Exception Handler (with Sentry)

```python
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all for unhandled errors — log + forward to Sentry."""
    import sentry_sdk
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    sentry_sdk.capture_exception(exc)
    return JSONResponse(
        status_code=500,
        content={"error": "内部サーバーエラーが発生しました。"},
    )
```

## Rules

### 1. Never Swallow Errors

```python
# ❌ NEVER
try:
    await storage.remove_files([path])
except Exception:
    pass  # error silently lost!

# ✅ ALWAYS — log then continue if non-critical
try:
    await storage.remove_files([path])
except Exception:
    logger.exception("Failed to remove storage object: %s", path)
```

### 2. Service Layer Raises DomainError (Not HTTPException)

```python
# ❌ NEVER — HTTPException in service (framework-coupled)
from fastapi import HTTPException

async def get_post(session, post_id):
    post = await session.get(Post, post_id)
    if not post:
        raise HTTPException(404, "Not found")  # ← Bad!

# ✅ ALWAYS — Domain exception
from app.services.exceptions import NotFoundError

async def get_post(session, post_id):
    post = await session.get(Post, post_id)
    if not post:
        raise NotFoundError("投稿が見つかりません")
```

### 3. Router Translates DomainError to HTTP

```python
@router.get("/{post_id}", response_model=PostResponse)
async def get_post(post_id: str, session: AsyncSession = Depends(get_session)):
    try:
        return await post_service.get(session, post_id)
    except DomainError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
```

### 4. Sentry Integration for Errors

- **5xx errors** → Captured by `unhandled_exception_handler` and forwarded to Sentry
- **4xx errors** → Filtered out by `sentry.py::_before_send()` to avoid noise
- **DomainError** → Suppressed in Sentry (`_before_send` returns `None`)
- **HTTPException (4xx)** → Suppressed in Sentry

## Structured Logging

```python
import logging

logger: logging.Logger = logging.getLogger(__name__)

# ✅ Use structured format with context
logger.info("Post created: id=%s author=%s", post.id, post.author)
logger.warning("Spam detected: content_length=%d", len(content))
logger.error("Database error: %s", exc, exc_info=True)
logger.exception("Unexpected error in %s", func_name)  # auto includes traceback
```

### Rules

1. **Use `logging.getLogger(__name__)`** in every module
2. **Use `%s` formatting** — Not f-strings (avoids evaluation if log level is filtered)
3. **Include context** — IDs, counts, paths in log messages
4. **Use appropriate levels:**
   - `DEBUG` — Development-only detail
   - `INFO` — Normal operations (created, updated, deleted)
   - `WARNING` — Recoverable issues (spam detected, rate limited)
   - `ERROR` — Failed operations that affect users
   - `EXCEPTION` — Unexpected errors (includes traceback)

## Error Response Format

All error responses follow a consistent structure:

```json
{
    "error": "エラーメッセージ"
}
```

For validation errors (Pydantic):

```json
{
    "detail": [
        {
            "loc": ["body", "title"],
            "msg": "String should have at least 1 character",
            "type": "string_too_short"
        }
    ]
}
```

For rate limiting:

```json
{
    "error": "リクエストが多すぎます。しばらくしてからもう一度お試しください。"
}
```
