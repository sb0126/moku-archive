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
