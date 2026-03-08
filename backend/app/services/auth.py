import hashlib
from datetime import datetime, timedelta, timezone

import bcrypt
from jose import jwt, JWTError

from app.config import settings


# ── JWT ──


def create_admin_token() -> str:
    payload: dict[str, str | datetime] = {
        "role": "admin",
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(hours=settings.jwt_expire_hours),
    }
    encoded: str = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return encoded


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
            computed: str = hashlib.sha256((salt_hex + plain).encode("utf-8")).hexdigest()
            return computed == expected_hash

    return plain == stored_hash


def needs_rehash(stored_hash: str) -> bool:
    """True if hash should be upgraded to bcrypt."""
    return not stored_hash.startswith(("$2b$", "$2a$"))
