# Deployment

## Dockerfile (Multi-stage)

```dockerfile
# ── Build stage ─────────────────────────────────────────
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
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

COPY --chown=appuser:appgroup . .

USER appuser
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers ${WEB_CONCURRENCY:-2} --log-level info"]
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

### 3. Health Checks

Two probes in the app:

```python
# Liveness — is the process alive?
@app.get("/api/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}

# Readiness — can we serve traffic?
@app.get("/api/ready")
async def readiness_check() -> dict[str, str]:
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return {"status": "ready", "db": "ok"}
    except Exception as exc:
        logger.error("Readiness check failed: %s", exc)
        return JSONResponse(status_code=503, content={"status": "not ready"})
```

### 4. Lifespan Management

```python
@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    # Startup: verify DB connection
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
    logger.info("✅ Database connection verified")

    yield  # app is running

    # Shutdown: clean up
    await engine.dispose()
    logger.info("Database engine disposed")
```

### 5. Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | ✅ | localhost | PostgreSQL connection string |
| `JWT_SECRET_KEY` | ✅ | change-me | JWT signing key |
| `MOKU_ADMIN_PASSWORD` | ✅ | (empty) | Admin login password |
| `CORS_ORIGINS` | ✅ | localhost | Allowed origins JSON array |
| `DEBUG` | ❌ | false | Enable debug mode/docs |
| `WEB_CONCURRENCY` | ❌ | 2 | Uvicorn worker count |

### 6. Production Docs

Disable Swagger/ReDoc in production:

```python
app = FastAPI(
    docs_url="/api/docs" if settings.debug else None,
    redoc_url="/api/redoc" if settings.debug else None,
    openapi_url="/api/openapi.json" if settings.debug else None,
)
```
