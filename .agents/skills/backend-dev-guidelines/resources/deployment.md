# Deployment

## Dockerfile (Multi-stage for Railway)

```dockerfile
# ── Build stage ─────────────────────────────────────────
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Runtime stage ───────────────────────────────────────
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends libpq5 curl && \
    rm -rf /var/lib/apt/lists/*

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

COPY --chown=appuser:appgroup backend/ .

USER appuser
EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=15s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8080}/api/health || exit 1

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080} --workers ${WEB_CONCURRENCY:-1} --log-level info"]
```

## Rules

### 1. Multi-stage Build

- **Builder stage** — Install build tools (gcc, libpq-dev) and pip packages
- **Runtime stage** — Copy only installed packages, minimal OS libs
- Result: smaller image, no build tools in production

### 2. Non-root User

```dockerfile
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser
USER appuser
```

### 3. Port Configuration

Railway provides a `PORT` env var. The app listens on `${PORT:-8080}`:

```dockerfile
EXPOSE 8080
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080} ..."]
```

**Important:** Default port is **8080** (not 8000). Railway sets `PORT` dynamically.

### 4. Worker Count

Single worker by default to prevent concurrent Alembic migration deadlocks:

```dockerfile
CMD ["sh", "-c", "... --workers ${WEB_CONCURRENCY:-1} ..."]
```

Scale up by setting `WEB_CONCURRENCY=2` or higher in Railway env vars after migrations are stable.

### 5. Health Checks

Two probes in the app:

```python
# Liveness — is the process alive?
@app.get("/api/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    return HealthResponse(status="ok")

# Readiness — can we serve traffic?
@app.get("/api/ready", response_model=ReadinessResponse)
async def readiness_check() -> ReadinessResponse:
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return ReadinessResponse(status="ready", db="ok")
    except Exception as exc:
        logger.error("Readiness check failed: %s", exc)
        raise HTTPException(status_code=503, detail="Database is unreachable") from exc
```

Docker HEALTHCHECK uses the liveness probe with extended `--start-period=60s` to allow time for DB migration on first boot.

### 6. Lifespan Management (Resilient Startup)

```python
@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    # DB connection check with retries (5 attempts, exponential backoff)
    db_connected = False
    for attempt in range(1, 6):
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            db_connected = True
            break
        except Exception as exc:
            wait = 2.0 ** attempt
            logger.warning("DB attempt %d/5 failed: %s — retrying in %.1fs", attempt, exc, wait)
            await asyncio.sleep(wait)

    if db_connected:
        # Create tables + cleanup expired JWT blacklist
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)
        cleaned = await cleanup_expired_tokens()
    else:
        # Non-fatal — health check still passes, readiness fails
        logger.warning("DB connection failed. App starts but /api/ready will report unhealthy.")

    yield  # app is running

    await engine.dispose()
```

**Key Design Decision:** DB failure is **non-fatal** so the liveness probe passes and Railway doesn't restart the container in a loop.

### 7. Environment Variables (Railway)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | ✅ | localhost | PostgreSQL connection string (asyncpg) |
| `PORT` | ✅ (Railway auto) | 8080 | Server listen port |
| `JWT_SECRET_KEY` | ✅ | change-me | JWT signing key |
| `MOKU_ADMIN_PASSWORD` | ✅ | (empty) | Admin login password |
| `CORS_ORIGINS` | ✅ | localhost | Allowed origins |
| `R2_ACCESS_KEY_ID` | ✅ | (empty) | Cloudflare R2 access key |
| `R2_SECRET_ACCESS_KEY` | ✅ | (empty) | Cloudflare R2 secret key |
| `R2_ENDPOINT_URL` | ✅ | (empty) | Cloudflare R2 endpoint |
| `R2_PUBLIC_URL` | ✅ | (empty) | R2 public dev URL |
| `SENTRY_DSN` | ❌ | (empty) | Sentry DSN (empty = disabled) |
| `ENVIRONMENT` | ❌ | development | Sentry environment tag |
| `DEBUG` | ❌ | false | Enable debug mode/docs |
| `WEB_CONCURRENCY` | ❌ | 1 | Uvicorn worker count |

### 8. Production Docs

Disable Swagger/ReDoc in production:

```python
app = FastAPI(
    docs_url="/api/docs" if settings.debug else None,
    redoc_url="/api/redoc" if settings.debug else None,
    openapi_url="/api/openapi.json" if settings.debug else None,
)
```

### 9. Sentry Init Before App Creation

Sentry must initialize before the FastAPI app object is created so ASGI integration hooks into every request:

```python
# main.py (top-level)
from app.sentry import init_sentry
init_sentry()  # ← before FastAPI() constructor

app = FastAPI(...)
```

### 10. Monorepo Dockerfile Path

The Dockerfile lives at the repo root and copies `backend/` into the container:

```dockerfile
COPY backend/requirements.txt .
# ...
COPY --chown=appuser:appgroup backend/ .
```

Railway root directory should be set to the repo root, with the Dockerfile at `Dockerfile`.
