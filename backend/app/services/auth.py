"""Authentication utilities — JWT, password hashing, and token blacklisting.

All functions are framework-agnostic (no FastAPI imports).
"""

import hashlib
import uuid
from datetime import datetime, timedelta, timezone

import bcrypt
from jose import jwt, JWTError

from app.config import settings


# ── JWT ──────────────────────────────────────────────────────


def create_admin_token() -> str:
    """Create a signed JWT with a unique ``jti`` for blacklist support."""
    now = datetime.now(timezone.utc)
    exp = now + timedelta(hours=settings.jwt_expire_hours)
    payload: dict[str, str | datetime] = {
        "role": "admin",
        "jti": uuid.uuid4().hex,
        "iat": now,
        "exp": exp,
    }
    encoded: str = jwt.encode(
        payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
    )
    return encoded


def decode_admin_token(token: str) -> dict[str, str] | None:
    """Decode a JWT and return the payload, or ``None`` on failure."""
    try:
        payload: dict[str, str] = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
        return payload
    except JWTError:
        return None


def verify_admin_token(token: str) -> bool:
    """Verify that a token is a valid admin token (signature + role).

    Note: This performs *synchronous* validation only (signature, expiry, role).
    For blacklist checking, use ``verify_admin_token_async`` instead.
    """
    payload = decode_admin_token(token)
    if payload is None:
        return False
    return payload.get("role") == "admin"


async def verify_admin_token_async(token: str) -> bool:
    """Verify an admin token AND check the JWT blacklist in Redis.

    This is the preferred method for request-time token validation.
    Falls back to signature-only validation if Redis is unavailable.
    """
    payload = decode_admin_token(token)
    if payload is None:
        return False
    if payload.get("role") != "admin":
        return False

    jti = payload.get("jti")
    if jti:
        from app.services.cache import is_token_blacklisted

        if await is_token_blacklisted(jti):
            return False

    return True


def get_token_remaining_seconds(token: str) -> int:
    """Return the number of seconds until a JWT expires (0 if already expired)."""
    payload = decode_admin_token(token)
    if payload is None:
        return 0
    exp = payload.get("exp")
    if exp is None:
        return 0
    exp_dt = datetime.fromtimestamp(int(exp), tz=timezone.utc)
    remaining = (exp_dt - datetime.now(timezone.utc)).total_seconds()
    return max(0, int(remaining))


# ── Password ─────────────────────────────────────────────────


def hash_password(password: str) -> str:
    """Always hash new passwords with bcrypt."""
    salt: bytes = bcrypt.gensalt()
    hashed: bytes = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain: str, stored_hash: str) -> bool:
    """
    Supports THREE formats for backward compatibility:
    1. bcrypt ($2b$... or $2a$...)
    2. SHA-256 salted (saltHex:hashHex) — legacy from Hono/Deno era
    3. Plaintext — legacy from early development
    """
    if stored_hash.startswith(("$2b$", "$2a$")):
        return bcrypt.checkpw(plain.encode("utf-8"), stored_hash.encode("utf-8"))

    if ":" in stored_hash:
        parts: list[str] = stored_hash.split(":")
        if len(parts) == 2:
            salt_hex, expected_hash = parts
            computed: str = hashlib.sha256(
                (salt_hex + plain).encode("utf-8")
            ).hexdigest()
            return computed == expected_hash

    return plain == stored_hash


def needs_rehash(stored_hash: str) -> bool:
    """True if hash should be upgraded to bcrypt."""
    return not stored_hash.startswith(("$2b$", "$2a$"))
