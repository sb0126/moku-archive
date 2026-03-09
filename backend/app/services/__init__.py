from app.services.auth import (
    create_admin_token,
    decode_admin_token,
    get_token_remaining_seconds,
    hash_password,
    needs_rehash,
    verify_admin_token,
    verify_admin_token_async,
    verify_password,
)
from app.services.exceptions import (
    ConflictError,
    DomainError,
    ForbiddenError,
    NotFoundError,
    SpamDetectedError,
    ValidationError,
)
from app.services.rate_limit import limiter
from app.services.sanitize import sanitize_text
from app.services.spam import SpamCheckResult, check_spam

# Domain services — import as modules in routers:
#   from app.services import post_service
#   from app.services import comment_service
#   etc.
# storage imports are separate because `aioboto3` SDK may not be installed
# in all environments. Import directly: from app.services.storage import ...
# cache: in-memory LRU with TTL (Redis removed), JWT blacklist uses PostgreSQL

__all__ = [
    # auth
    "create_admin_token",
    "decode_admin_token",
    "get_token_remaining_seconds",
    "verify_admin_token",
    "verify_admin_token_async",
    "hash_password",
    "verify_password",
    "needs_rehash",
    # exceptions
    "DomainError",
    "NotFoundError",
    "ForbiddenError",
    "ConflictError",
    "ValidationError",
    "SpamDetectedError",
    # spam
    "SpamCheckResult",
    "check_spam",
    # sanitize
    "sanitize_text",
    # rate_limit
    "limiter",
]
