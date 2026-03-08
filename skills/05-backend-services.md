# Skill: Backend Services (Auth, Spam, Sanitize, Storage, Rate Limit)

---

## 1. Auth Service — `app/services/auth.py`

```python
import hashlib
from datetime import datetime, timedelta, timezone

from jose import jwt, JWTError
from passlib.context import CryptContext

from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ── JWT ──

def create_admin_token() -> str:
    payload: dict[str, str | datetime] = {
        "role": "admin",
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(hours=settings.jwt_expire_hours),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def verify_admin_token(token: str) -> bool:
    try:
        payload: dict[str, str] = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
        return payload.get("role") == "admin"
    except JWTError:
        return False


# ── Password ──

def hash_password(password: str) -> str:
    """Always hash new passwords with bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain: str, stored_hash: str) -> bool:
    """
    Supports THREE formats for backward compatibility:
    1. bcrypt ($2b$... or $2a$...)
    2. SHA-256 salted (saltHex:hashHex) — legacy from Hono/Deno era
    3. Plaintext — legacy from early development
    """
    if stored_hash.startswith(("$2b$", "$2a$")):
        return pwd_context.verify(plain, stored_hash)

    if ":" in stored_hash:
        parts: list[str] = stored_hash.split(":")
        if len(parts) == 2:
            salt_hex, expected_hash = parts
            computed: str = hashlib.sha256((salt_hex + plain).encode("utf-8")).hexdigest()
            return computed == expected_hash

    return plain == stored_hash


def needs_rehash(stored_hash: str) -> bool:
    """True if hash should be upgraded to bcrypt."""
    return not stored_hash.startswith(("$2b$", "$2a$"))
```

**Lazy Rehash Pattern:** On successful password verification, if `needs_rehash()` returns True, re-hash with `hash_password()` and UPDATE the DB row. This gradually migrates all legacy hashes to bcrypt.

---

## 2. Spam Detection — `app/services/spam.py`

```python
import re
from pydantic import BaseModel

class SpamCheckResult(BaseModel):
    is_spam: bool
    reason: str | None = None

SPAM_URL_THRESHOLD: int = 3

SPAM_KEYWORDS: re.Pattern[str] = re.compile(
    r"\b(casino|gambling|viagra|cialis|forex|crypto\s*trading|click\s*here|free\s*money|"
    r"buy\s*now|limited\s*offer|カジノ|ギャンブル|出会い系|副業|簡単に稼|即金|アダルト)\b",
    re.IGNORECASE,
)

def check_spam(content: str) -> SpamCheckResult:
    if not content:
        return SpamCheckResult(is_spam=False)

    urls: list[str] = re.findall(r"https?://\S+", content, re.IGNORECASE)
    if len(urls) > SPAM_URL_THRESHOLD:
        return SpamCheckResult(is_spam=True, reason=f"URLが多すぎます ({len(urls)}個検出)")

    if re.search(r"(.)\1{10,}", content):
        return SpamCheckResult(is_spam=True, reason="同じ文字の過度な繰り返しが検出されました")

    keyword_matches: list[str] = SPAM_KEYWORDS.findall(content)
    if len(keyword_matches) >= 2:
        return SpamCheckResult(is_spam=True, reason="スパムの可能性があるコンテンツが検出されました")

    lines: list[str] = [line.strip().lower() for line in content.split("\n") if line.strip()]
    if len(lines) >= 5 and len(set(lines)) == 1:
        return SpamCheckResult(is_spam=True, reason="同じ内容の繰り返しが検出されました")

    return SpamCheckResult(is_spam=False)
```

---

## 3. Sanitization — `app/services/sanitize.py`

```python
import re

XSS_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"<script\b[^<]*(?:(?!</script>)<[^<]*)*</script>", re.IGNORECASE),
    re.compile(r"on\w+\s*=\s*[\"'][^\"']*[\"']", re.IGNORECASE),
    re.compile(r"javascript\s*:", re.IGNORECASE),
    re.compile(r"data\s*:\s*text/html", re.IGNORECASE),
    re.compile(r"<iframe\b[^>]*>", re.IGNORECASE),
    re.compile(r"<object\b[^>]*>", re.IGNORECASE),
    re.compile(r"<embed\b[^>]*>", re.IGNORECASE),
    re.compile(r"<form\b[^>]*>", re.IGNORECASE),
]

def sanitize_text(text: str) -> str:
    if not text or not isinstance(text, str):
        return ""
    result: str = text.strip()
    for pattern in XSS_PATTERNS:
        result = pattern.sub("", result)
    return result
```

---

## 4. Storage — `app/services/storage.py`

Uses Supabase Python client for Storage operations.

```python
from supabase import create_client, Client
from app.config import settings

def get_storage_client() -> Client:
    return create_client(settings.supabase_url, settings.supabase_service_role_key)

BUCKET_NAME: str = settings.storage_bucket_name  # "moku-images"

async def ensure_bucket() -> None:
    client: Client = get_storage_client()
    buckets = client.storage.list_buckets()
    if not any(b.name == BUCKET_NAME for b in buckets):
        client.storage.create_bucket(BUCKET_NAME, options={"public": False})

async def resolve_storage_url(image_url: str) -> str:
    """Convert 'storage:path/to/file' to a signed URL (1h)."""
    if not image_url or not image_url.startswith("storage:"):
        return image_url
    path: str = image_url.removeprefix("storage:")
    client: Client = get_storage_client()
    result = client.storage.from_(BUCKET_NAME).create_signed_url(path, 3600)
    return result.get("signedURL", "")

async def resolve_article_images(articles: list[dict]) -> list[dict]:
    """Batch resolve storage: URLs for a list of articles."""
    storage_articles = [a for a in articles if a.get("image_url", "").startswith("storage:")]
    if not storage_articles:
        return articles
    paths: list[str] = [a["image_url"].removeprefix("storage:") for a in storage_articles]
    client: Client = get_storage_client()
    signed = client.storage.from_(BUCKET_NAME).create_signed_urls(paths, 3600)
    signed_map: dict[str, str] = {}
    for item in signed:
        if item.get("signedURL") and item.get("path"):
            signed_map[item["path"]] = item["signedURL"]
    return [
        {**a, "image_url_raw": a["image_url"], "image_url": signed_map.get(a["image_url"].removeprefix("storage:"), "")}
        if a.get("image_url", "").startswith("storage:") else a
        for a in articles
    ]
```

---

## 5. Rate Limiting — `app/services/rate_limit.py`

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
```

Rate limits by endpoint:
- `POST /api/posts`: 5/minute
- `POST /api/posts/{id}/comments`: 5/minute
- `POST /api/inquiries`: 5/minute
- `POST /api/admin/login`: 5/5minutes
- `POST /api/admin/upload-image`: 20/minute

---

## 6. Admin Dependency — `app/dependencies.py`

```python
from fastapi import Header, HTTPException
from app.services.auth import verify_admin_token


async def require_admin(x_admin_token: str = Header(...)) -> bool:
    if not verify_admin_token(x_admin_token):
        raise HTTPException(status_code=401, detail="管理者認証が必要です")
    return True


async def get_admin_token_optional(
    x_admin_token: str | None = Header(default=None),
) -> bool:
    if x_admin_token and verify_admin_token(x_admin_token):
        return True
    return False
```
