# Configuration & Environment

## pydantic-settings Pattern

All configuration MUST flow through a single `Settings` class:

```python
# app/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ── Database ───────────────────────────────────
    database_url: str = "postgresql+asyncpg://localhost:5432/moku"

    # ── Supabase / Storage ─────────────────────────
    supabase_url: str = ""
    supabase_service_role_key: str = ""
    storage_bucket_name: str = "moku-images"

    # ── Auth / JWT ─────────────────────────────────
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_hours: int = 24
    moku_admin_password: str = ""

    # ── CORS ───────────────────────────────────────
    cors_origins: list[str] = [
        "http://localhost:3000",
        "https://moku.com",
    ]

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
moku_admin_password: str = ""  # empty = feature disabled
```

### 4. `.env.example`

Maintain a `.env.example` with ALL variables (no real values):

```env
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/dbname

# Auth
JWT_SECRET_KEY=generate-a-random-string
MOKU_ADMIN_PASSWORD=set-admin-password

# Storage
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# CORS
CORS_ORIGINS=["http://localhost:3000","https://moku.com"]

# Server
DEBUG=false
```

### 5. Never Commit `.env`

```gitignore
# .gitignore
.env
.env.local
.env.production
```
