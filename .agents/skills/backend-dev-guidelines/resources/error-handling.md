# Error Handling

## Exception Hierarchy

```python
# services/exceptions.py

class AppError(Exception):
    """Base exception for all application errors."""
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class NotFoundError(AppError):
    """Resource not found."""
    def __init__(self, message: str = "リソースが見つかりません"):
        super().__init__(message, status_code=404)


class ValidationError(AppError):
    """Input validation failed."""
    def __init__(self, message: str = "入力内容が無効です"):
        super().__init__(message, status_code=400)


class AuthenticationError(AppError):
    """Authentication failed."""
    def __init__(self, message: str = "認証に失敗しました"):
        super().__init__(message, status_code=401)


class ForbiddenError(AppError):
    """Access denied."""
    def __init__(self, message: str = "アクセス権限がありません"):
        super().__init__(message, status_code=403)
```

## Global Exception Handler

```python
# main.py

from app.services.exceptions import AppError

@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    logger.warning("AppError: %s (status=%d, path=%s)", exc.message, exc.status_code, request.url.path)
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "error": exc.message},
    )
```

## Rules

### 1. Never Swallow Errors

```python
# ❌ NEVER
try:
    client.storage.from_(BUCKET).remove([path])
except Exception:
    pass  # error silently lost!

# ✅ ALWAYS — log then continue if non-critical
try:
    client.storage.from_(BUCKET).remove([path])
except Exception:
    logger.exception("Failed to remove storage object: %s", path)
```

### 2. Service Layer Raises Domain Exceptions

```python
# ❌ NEVER — HTTPException in service (framework-coupled)
async def get_post(session, post_id):
    post = await session.get(Post, post_id)
    if not post:
        raise HTTPException(404, "Not found")  # ← Bad!

# ✅ ALWAYS — Domain exception
async def get_post(session, post_id):
    post = await session.get(Post, post_id)
    if not post:
        raise NotFoundError("投稿が見つかりません")
```

### 3. Router Translates Exceptions

```python
@router.get("/{post_id}", response_model=PostResponse)
async def get_post(post_id: str, session: AsyncSession = Depends(get_session)):
    try:
        return await post_service.get(session, post_id)
    except AppError:
        raise  # handled by global handler
```

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
    "success": false,
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
