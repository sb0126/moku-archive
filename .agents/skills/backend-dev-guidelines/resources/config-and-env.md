# Configuration & Environment

## pydantic-settings Pattern

All configuration MUST flow through a single `Settings` class:

```python
# app/config.py
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ── Database ───────────────────────────────────
    database_url: str = "postgresql+asyncpg://localhost:5432/moku"

    # ── Cloudflare R2 (S3-compatible storage) ──────
    r2_access_key_id: str = ""
    r2_secret_access_key: str = ""       # NEVER expose to frontend
    r2_endpoint_url: str = ""            # https://<account_id>.r2.cloudflarestorage.com
    r2_bucket_name: str = "moku-archive"
    r2_public_url: str = ""              # e.g. https://pub-xxx.r2.dev

    # ── Auth / JWT ─────────────────────────────────
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_hours: int = 24
    moku_admin_password: str = ""

    # ── Analytics & Verification ───────────────────
    ga_measurement_id: str = "G-M0EESK8HQK"
    google_site_verification: str = ""
    naver_site_verification: str = ""

    # ── CORS ───────────────────────────────────────
    cors_origins: list[str] = [
        "http://localhost:3000",
        "https://moku-archive-bt2u.vercel.app",
    ]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _parse_cors_origins(cls, v: object) -> list[str]:
        """Accept JSON array, comma-separated string, or a single origin."""
        ...

    # ── Sentry ─────────────────────────────────────
    sentry_dsn: str = ""
    environment: str = "development"

    # ── Server ─────────────────────────────────────
    debug: bool = False

# Singleton
settings = Settings()
```

## Rules

### 1. Never Use `os.environ` / `os.getenv`

```python
# ❌ NEVER
import os
secret = os.environ["JWT_SECRET"]
debug = os.getenv("DEBUG", "false") == "true"

# ✅ ALWAYS
from app.config import settings
secret = settings.jwt_secret_key
debug = settings.debug
```

### 2. Type-Safe Defaults

```python
# ❌ Stringly-typed
debug: str = "false"  # is it "false", "0", "no"?

# ✅ Boolean-typed
debug: bool = False  # pydantic handles "true"/"1"/"yes" automatically
```

### 3. Sensitive Values

```python
# ❌ Default secrets in code
jwt_secret_key: str = "my-actual-secret"

# ✅ Safe defaults that force override
jwt_secret_key: str = "change-me-in-production"
moku_admin_password: str = ""        # empty = feature disabled
r2_secret_access_key: str = ""       # NEVER expose
```

### 4. `.env.example`

Maintain a `.env.example` with ALL variables (no real values):

```env
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/dbname

# Auth
JWT_SECRET_KEY=generate-a-random-string
MOKU_ADMIN_PASSWORD=set-admin-password

# Cloudflare R2 Storage
R2_ACCESS_KEY_ID=your-r2-access-key
R2_SECRET_ACCESS_KEY=your-r2-secret-key
R2_ENDPOINT_URL=https://account-id.r2.cloudflarestorage.com
R2_BUCKET_NAME=moku-archive
R2_PUBLIC_URL=https://pub-xxx.r2.dev

# Analytics & Verification
GA_MEASUREMENT_ID=G-XXXXXXXXXX
GOOGLE_SITE_VERIFICATION=verification-code
NAVER_SITE_VERIFICATION=verification-code

# CORS
CORS_ORIGINS=["http://localhost:3000","https://your-domain.vercel.app"]

# Sentry
SENTRY_DSN=https://xxx@xxx.ingest.us.sentry.io/xxx
ENVIRONMENT=production

# Server
DEBUG=false
```

### 5. CORS_ORIGINS Parsing

The `cors_origins` field supports multiple input formats:

```python
# JSON array string
CORS_ORIGINS=["http://localhost:3000","https://moku.com"]

# Comma-separated string
CORS_ORIGINS=http://localhost:3000,https://moku.com

# Single origin
CORS_ORIGINS=http://localhost:3000
```

### 6. Never Commit `.env`

```gitignore
# .gitignore
.env
.env.local
.env.production
```

## Complete Settings Reference

| Setting | Env Var | Type | Default | Description |
|---------|---------|------|---------|-------------|
| `database_url` | `DATABASE_URL` | `str` | `postgresql+asyncpg://localhost:5432/moku` | PostgreSQL connection string |
| `r2_access_key_id` | `R2_ACCESS_KEY_ID` | `str` | `""` | Cloudflare R2 access key |
| `r2_secret_access_key` | `R2_SECRET_ACCESS_KEY` | `str` | `""` | R2 secret (never expose) |
| `r2_endpoint_url` | `R2_ENDPOINT_URL` | `str` | `""` | R2 endpoint URL |
| `r2_bucket_name` | `R2_BUCKET_NAME` | `str` | `moku-archive` | R2 bucket name |
| `r2_public_url` | `R2_PUBLIC_URL` | `str` | `""` | R2 public dev URL |
| `jwt_secret_key` | `JWT_SECRET_KEY` | `str` | `change-me-in-production` | JWT signing key |
| `jwt_algorithm` | `JWT_ALGORITHM` | `str` | `HS256` | JWT algorithm |
| `jwt_expire_hours` | `JWT_EXPIRE_HOURS` | `int` | `24` | Token lifetime |
| `moku_admin_password` | `MOKU_ADMIN_PASSWORD` | `str` | `""` | Admin login password |
| `ga_measurement_id` | `GA_MEASUREMENT_ID` | `str` | `G-M0EESK8HQK` | Google Analytics ID |
| `google_site_verification` | `GOOGLE_SITE_VERIFICATION` | `str` | `""` | Google verification |
| `naver_site_verification` | `NAVER_SITE_VERIFICATION` | `str` | `""` | Naver verification |
| `cors_origins` | `CORS_ORIGINS` | `list[str]` | `[localhost:3000, vercel]` | Allowed CORS origins |
| `sentry_dsn` | `SENTRY_DSN` | `str` | `""` | Sentry DSN (empty = disabled) |
| `environment` | `ENVIRONMENT` | `str` | `development` | Sentry environment tag |
| `debug` | `DEBUG` | `bool` | `False` | Debug mode (enables API docs) |
