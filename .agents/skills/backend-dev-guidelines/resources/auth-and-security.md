# Auth & Security

## JWT Authentication

### Token Creation

```python
from datetime import datetime, timedelta, timezone
from jose import jwt
from app.config import settings

def create_admin_token() -> str:
    payload: dict[str, str | datetime] = {
        "role": "admin",
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(hours=settings.jwt_expire_hours),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
```

### Token Verification

```python
from jose import jwt, JWTError

def verify_admin_token(token: str) -> bool:
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        return payload.get("role") == "admin"
    except JWTError:
        return False
```

## Admin Authentication Pattern

### Rules

1. **Admin auth MUST use `Depends()` only** — Never trust request body fields
2. **JWT token via `X-Admin-Token` header** — Not query params or body
3. **Optional admin check** — Use `get_admin_token_optional` for mixed endpoints

```python
# dependencies.py
from fastapi import Header, HTTPException
from app.services.auth import verify_admin_token

async def require_admin(x_admin_token: str = Header(...)) -> bool:
    """Strict admin guard — 401 if missing or invalid."""
    if not verify_admin_token(x_admin_token):
        raise HTTPException(status_code=401, detail="管理者認証が必要です")
    return True

async def get_admin_token_optional(
    x_admin_token: str | None = Header(default=None),
) -> bool:
    """Soft admin check — returns False if no token."""
    if x_admin_token and verify_admin_token(x_admin_token):
        return True
    return False
```

### ❌ Security Anti-Pattern: Body-based Admin Check

```python
# ❌ CRITICAL VULNERABILITY — client can bypass auth
class PostDeleteRequest(BaseModel):
    password: str | None = None
    is_admin: bool = False  # ← Anyone can set this to True!

@router.delete("/{post_id}")
async def delete_post(body: PostDeleteRequest, ...):
    if body.is_admin:  # ← No real verification!
        # Deletes without password check
        ...
```

### ✅ Correct Pattern

```python
class PostDeleteRequest(BaseModel):
    password: str | None = None
    # No is_admin field!

@router.delete("/{post_id}")
async def delete_post(
    body: PostDeleteRequest,
    is_admin: bool = Depends(get_admin_token_optional),  # ← real JWT check
    ...
):
    if not is_admin:
        # Must verify password
        if not body.password:
            raise HTTPException(400, "パスワードが必要です")
        if not verify_password(body.password, post.password):
            raise HTTPException(403, "パスワードが正しくありません")
```

## Password Hashing

```python
import bcrypt

def hash_password(password: str) -> str:
    salt: bytes = bcrypt.gensalt()
    hashed: bytes = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")

def verify_password(plain: str, stored_hash: str) -> bool:
    if stored_hash.startswith(("$2b$", "$2a$")):
        return bcrypt.checkpw(plain.encode("utf-8"), stored_hash.encode("utf-8"))
    # Legacy fallbacks...
    return False

def needs_rehash(stored_hash: str) -> bool:
    return not stored_hash.startswith(("$2b$", "$2a$"))
```

## CORS Configuration

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,  # ← from config, never *
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "Origin", "X-Requested-With"],
)
```

**Rules:**
- Never use `allow_origins=["*"]` in production
- Define origins in `settings.cors_origins` (env var)
- Include only methods actually used

## Rate Limiting

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
```

| Endpoint Type | Limit | Rationale |
|---------------|-------|-----------|
| Public mutation (create) | 3-5/min | Prevent spam |
| Authenticated mutation | 10/min | Reasonable use |
| Read endpoints | 30-60/min | Normal browsing |
| Admin login | 5/min | Brute-force prevention |
