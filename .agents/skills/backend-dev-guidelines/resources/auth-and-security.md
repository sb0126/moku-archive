# Auth & Security

## JWT Authentication (with PostgreSQL Blacklist)

### Token Creation (with `jti` for blacklist support)

```python
import uuid
from datetime import datetime, timedelta, timezone
from jose import jwt
from app.config import settings

def create_admin_token() -> str:
    """Create a signed JWT with a unique jti for blacklist support."""
    now = datetime.now(timezone.utc)
    exp = now + timedelta(hours=settings.jwt_expire_hours)
    payload: dict[str, str | datetime] = {
        "role": "admin",
        "jti": uuid.uuid4().hex,   # ← unique ID for revocation
        "iat": now,
        "exp": exp,
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
```

### Token Verification (Sync — signature only)

```python
from jose import jwt, JWTError

def verify_admin_token(token: str) -> bool:
    """Synchronous validation — signature, expiry, role only."""
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        return payload.get("role") == "admin"
    except JWTError:
        return False
```

### Token Verification (Async — with blacklist check)

```python
async def verify_admin_token_async(token: str) -> bool:
    """Preferred method — validates signature + checks PostgreSQL blacklist."""
    payload = decode_admin_token(token)
    if payload is None or payload.get("role") != "admin":
        return False

    jti = payload.get("jti")
    if jti:
        from app.services.cache import is_token_blacklisted
        if await is_token_blacklisted(jti):
            return False

    return True
```

**Rule:** Always use `verify_admin_token_async` in request-time validation (dependencies).

## Admin Authentication Pattern

### Rules

1. **Admin auth MUST use `Depends()` only** — Never trust request body fields
2. **JWT token via `X-Admin-Token` header** — Not query params or body
3. **Optional admin check** — Use `get_admin_token_optional` for mixed endpoints
4. **Dependencies use async verification** — `verify_admin_token_async` (includes blacklist)

```python
# dependencies.py
from fastapi import Header, HTTPException
from app.services.auth import verify_admin_token_async

async def require_admin(x_admin_token: str = Header(...)) -> bool:
    """Strict admin guard — 401 if missing or invalid."""
    if not await verify_admin_token_async(x_admin_token):
        raise HTTPException(status_code=401, detail="管理者認証が必要です")
    return True

async def get_admin_token_optional(
    x_admin_token: str | None = Header(default=None),
) -> bool:
    """Soft admin check — returns False if no token."""
    if x_admin_token and await verify_admin_token_async(x_admin_token):
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

## Password Hashing (with Legacy Support)

```python
import bcrypt
import hashlib

def hash_password(password: str) -> str:
    """Always hash new passwords with bcrypt."""
    salt: bytes = bcrypt.gensalt()
    hashed: bytes = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")

def verify_password(plain: str, stored_hash: str) -> bool:
    """Supports THREE formats for backward compatibility:
    1. bcrypt ($2b$... or $2a$...)
    2. SHA-256 salted (saltHex:hashHex) — legacy from Hono/Deno era
    3. Plaintext — legacy from early development
    """
    if stored_hash.startswith(("$2b$", "$2a$")):
        return bcrypt.checkpw(plain.encode("utf-8"), stored_hash.encode("utf-8"))
    if ":" in stored_hash:
        parts = stored_hash.split(":")
        if len(parts) == 2:
            salt_hex, expected_hash = parts
            computed = hashlib.sha256((salt_hex + plain).encode("utf-8")).hexdigest()
            return computed == expected_hash
    return plain == stored_hash

def needs_rehash(stored_hash: str) -> bool:
    """True if hash should be upgraded to bcrypt."""
    return not stored_hash.startswith(("$2b$", "$2a$"))
```

## CORS Configuration

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,  # ← from config, never *
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "Origin",
                   "X-Requested-With", "X-Admin-Token"],
)
```

**Rules:**
- Never use `allow_origins=["*"]` in production
- Define origins in `settings.cors_origins` (env var: `CORS_ORIGINS`)
- Include `X-Admin-Token` in `allow_headers`
- `cors_origins` accepts JSON array, comma-separated string, or single origin

## Rate Limiting

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(
    key_func=get_remote_address,
    # In-memory storage (default) — counters reset on server restart
)
```

| Endpoint Type | Limit | Rationale |
|---------------|-------|-----------|
| Public mutation (create) | 3-5/min | Prevent spam |
| Authenticated mutation | 10/min | Reasonable use |
| Read endpoints | 30-60/min | Normal browsing |
| Admin login | 5/min | Brute-force prevention |

## JWT Token Lifecycle

```
Login → create_admin_token() → JWT with jti claim
  ↓
Request → require_admin → verify_admin_token_async()
  ↓                         ↓ checks
  ↓                     PostgreSQL token_blacklist table
  ↓
Logout → blacklist_token(jti, ttl)
  ↓
Startup → cleanup_expired_tokens()
```
