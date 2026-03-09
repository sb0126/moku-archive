# Sentry & Observability

## Sentry SDK Initialization

Sentry MUST be initialized **before** the FastAPI app object is created so the
ASGI integration hooks into every request.

```python
# app/sentry.py — called from main.py top-level

def init_sentry() -> None:
    """Bootstrap Sentry SDK if a DSN is configured. No-ops if empty."""
    if not settings.sentry_dsn:
        logger.info("ℹ️  SENTRY_DSN not set — Sentry is disabled")
        return

    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    from sentry_sdk.integrations.starlette import StarletteIntegration
    from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
    from sentry_sdk.integrations.logging import LoggingIntegration

    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.environment,
        release="moku-api@0.1.0",
        send_default_pii=True,
        traces_sample_rate=1.0,
        profile_session_sample_rate=1.0,
        profile_lifecycle="trace",
        enable_logs=True,
        integrations=[
            FastApiIntegration(transaction_style="endpoint"),
            StarletteIntegration(transaction_style="endpoint"),
            SqlalchemyIntegration(),
            LoggingIntegration(
                level=logging.INFO,        # breadcrumbs from INFO+
                event_level=logging.ERROR,  # only ERROR+ create events
            ),
        ],
        before_send=_before_send,
    )
```

### Usage in main.py

```python
from app.sentry import init_sentry

init_sentry()  # ← BEFORE FastAPI() constructor

app = FastAPI(...)
```

## Event Filtering (`before_send`)

Expected errors are filtered out to avoid noise:

```python
def _before_send(event: dict, hint: dict) -> dict | None:
    exc_info = hint.get("exc_info")
    if exc_info:
        exc_value = exc_info[1] if len(exc_info) > 1 else None
        # Drop domain errors — expected validation/auth failures
        if isinstance(exc_value, DomainError):
            return None
        # Drop FastAPI HTTPExceptions with 4xx status codes
        if isinstance(exc_value, HTTPException):
            if 400 <= exc_value.status_code < 500:
                return None
    return event
```

**What gets captured:**
- ✅ 5xx errors (unhandled exceptions)
- ✅ Database connection failures
- ✅ Storage (R2) errors
- ❌ 4xx errors (filtered — expected client errors)
- ❌ DomainError (filtered — expected validation/auth failures)

## Helper Functions

### User Context

```python
from app.sentry import set_user_context

def set_user_context(*, admin: bool = False, ip: str | None = None) -> None:
    """Attach user context to current Sentry scope."""
    scope = sentry_sdk.get_current_scope()
    user_data = {"role": "admin" if admin else "visitor"}
    if ip:
        user_data["ip_address"] = ip
    scope.set_user(user_data)
```

### Custom Messages

```python
from app.sentry import capture_message

capture_message("Unusual traffic spike detected", level="warning")
```

### Breadcrumbs

```python
from app.sentry import add_breadcrumb

add_breadcrumb(
    message="Article created",
    category="content",
    level="info",
    data={"article_id": "visa-guide-2026"},
)
```

## Unhandled Exception Handler

All unhandled exceptions are forwarded to Sentry via the global handler:

```python
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    sentry_sdk.capture_exception(exc)
    return JSONResponse(
        status_code=500,
        content={"error": "内部サーバーエラーが発生しました。"},
    )
```

## Configuration

| Setting | Env Var | Default | Description |
|---------|---------|---------|-------------|
| `sentry_dsn` | `SENTRY_DSN` | `""` | Sentry DSN (empty = disabled) |
| `environment` | `ENVIRONMENT` | `development` | Environment tag in Sentry |

## Sentry Debug Endpoint

Available only when `DEBUG=true`:

```python
if settings.debug:
    @app.get("/sentry-debug")
    async def trigger_error() -> None:
        """Intentional error to verify Sentry integration."""
        division_by_zero = 1 / 0
```

## Rules

1. **Init before FastAPI()** — Sentry must hook into ASGI middleware
2. **Filter 4xx errors** — Only 5xx should create Sentry events
3. **All helpers are safe** — They no-op if `sentry_sdk` is not installed
4. **Use lazy imports** — `import sentry_sdk` inside functions to avoid ImportError
5. **breadcrumbs from INFO+** — Don't create breadcrumbs from DEBUG logs
6. **events from ERROR+** — Only ERROR and above create Sentry events
