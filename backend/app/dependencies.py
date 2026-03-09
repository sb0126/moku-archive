"""FastAPI dependencies — auth guards and shared injections."""

from fastapi import Header, HTTPException

from app.services.auth import verify_admin_token_async


async def require_admin(x_admin_token: str = Header(...)) -> bool:
    """Dependency: raises 401 unless the token is a valid, non-blacklisted admin JWT."""
    if not await verify_admin_token_async(x_admin_token):
        raise HTTPException(status_code=401, detail="管理者認証が必要です")
    return True


async def get_admin_token_optional(
    x_admin_token: str | None = Header(default=None),
) -> bool:
    """Dependency: returns True if a valid admin token is present, False otherwise."""
    if x_admin_token and await verify_admin_token_async(x_admin_token):
        return True
    return False
