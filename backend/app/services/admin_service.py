"""Admin domain service — login, logout, stats, image management business logic.

Framework-agnostic: receives AsyncSession as a parameter, raises domain exceptions.
Stats are cached in Redis; logout blacklists the JWT.
"""

import logging
import uuid
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import Comment, Inquiry, Post
from app.schemas import (
    AdminLoginResponse,
    AdminStats,
    AdminStatsResponse,
    ImageUploadResponse,
    SuccessResponse,
)
from app.services.auth import (
    create_admin_token,
    decode_admin_token,
    get_token_remaining_seconds,
)
from app.services.cache import (
    blacklist_token,
    delete_cached,
    get_cached,
    invalidate_namespace,
    set_cached,
)
from app.services.exceptions import DomainError, ForbiddenError, ValidationError
from app.services.storage import ensure_bucket, remove_files, upload_file

logger: logging.Logger = logging.getLogger(__name__)

# 5 MB upload limit
MAX_UPLOAD_BYTES: int = 5 * 1024 * 1024

ALLOWED_CONTENT_TYPES: set[str] = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/gif",
    "image/svg+xml",
}

_EXTENSION_MAP: dict[str, str] = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
    "image/svg+xml": ".svg",
}

_CACHE_NS = "admin"
_STATS_KEY = "stats"
_TTL_STATS = 120  # 2 minutes — stats are relatively expensive


# ── public API ─────────────────────────────────────────────────


async def login(password: str) -> AdminLoginResponse:
    """Authenticate admin with password, return JWT."""
    if not settings.moku_admin_password:
        logger.error("Admin login attempted but MOKU_ADMIN_PASSWORD is not set")
        raise DomainError("管理者パスワードが設定されていません", status_code=500)

    if password != settings.moku_admin_password:
        raise ForbiddenError("管理者認証に失敗しました")

    token: str = create_admin_token()
    logger.info("Admin login successful")
    return AdminLoginResponse(token=token)


async def logout(token: str) -> SuccessResponse:
    """Invalidate an admin JWT by adding its jti to the Redis blacklist."""
    payload = decode_admin_token(token)
    if payload is None:
        raise ForbiddenError("無効なトークンです")

    jti = payload.get("jti")
    if not jti:
        # Legacy tokens without jti — can't blacklist, but still return success
        logger.warning("Logout attempted with token missing jti claim")
        return SuccessResponse(message="ログアウトしました")

    remaining = get_token_remaining_seconds(token)
    if remaining > 0:
        await blacklist_token(jti, ttl_seconds=remaining)

    logger.info("Admin logout successful (jti=%s)", jti)
    return SuccessResponse(message="ログアウトしました")


async def get_stats(session: AsyncSession) -> AdminStatsResponse:
    """Aggregate dashboard statistics (cached)."""
    # Try cache first
    cached = await get_cached(_CACHE_NS, _STATS_KEY)
    if cached is not None:
        logger.debug("Cache HIT: %s:%s", _CACHE_NS, _STATS_KEY)
        return AdminStatsResponse(**cached)

    # Cache miss — query DB
    total_inquiries: int = (
        await session.execute(select(func.count()).select_from(Inquiry))
    ).scalar_one()

    pending_inquiries: int = (
        await session.execute(
            select(func.count())
            .select_from(Inquiry)
            .where(Inquiry.status == "pending")  # type: ignore[arg-type]  # SQLModel column
        )
    ).scalar_one()

    contacted_inquiries: int = (
        await session.execute(
            select(func.count())
            .select_from(Inquiry)
            .where(Inquiry.status == "contacted")  # type: ignore[arg-type]  # SQLModel column
        )
    ).scalar_one()

    completed_inquiries: int = (
        await session.execute(
            select(func.count())
            .select_from(Inquiry)
            .where(Inquiry.status == "completed")  # type: ignore[arg-type]  # SQLModel column
        )
    ).scalar_one()

    total_posts: int = (
        await session.execute(select(func.count()).select_from(Post))
    ).scalar_one()

    total_views: int = (
        await session.execute(select(func.coalesce(func.sum(Post.views), 0)))
    ).scalar_one()

    total_comments: int = (
        await session.execute(select(func.count()).select_from(Comment))
    ).scalar_one()

    stats = AdminStats(
        total_inquiries=total_inquiries,
        pending_inquiries=pending_inquiries,
        contacted_inquiries=contacted_inquiries,
        completed_inquiries=completed_inquiries,
        total_posts=total_posts,
        total_views=total_views,
        total_comments=total_comments,
    )
    response = AdminStatsResponse(stats=stats)

    # Populate cache
    await set_cached(_CACHE_NS, _STATS_KEY, response.model_dump(), ttl_seconds=_TTL_STATS)
    logger.debug("Cache SET: %s:%s", _CACHE_NS, _STATS_KEY)

    return response


async def invalidate_stats_cache() -> None:
    """Invalidate the admin stats cache (call after data mutations)."""
    await delete_cached(_CACHE_NS, _STATS_KEY)


async def upload_image(
    data: bytes, content_type: str
) -> ImageUploadResponse:
    """Validate and upload an image to Cloudflare R2."""
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise ValidationError(f"許可されていないファイル形式です: {content_type}")

    if len(data) > MAX_UPLOAD_BYTES:
        raise ValidationError(
            f"ファイルサイズが上限({MAX_UPLOAD_BYTES // (1024 * 1024)}MB)を超えています"
        )

    ext: str = _EXTENSION_MAP.get(content_type, ".bin")
    unique_name: str = f"{uuid.uuid4().hex}{ext}"
    storage_path: str = f"articles/{unique_name}"

    await ensure_bucket()
    await upload_file(storage_path, data, content_type)

    logger.info("Image uploaded: %s (%d bytes)", storage_path, len(data))
    return ImageUploadResponse(
        message="画像がアップロードされました",
        url=f"storage:{storage_path}",
        path=storage_path,
    )


async def delete_image(path: str) -> SuccessResponse:
    """Remove an image from storage."""
    try:
        await remove_files([path])
    except Exception as exc:
        logger.error("Failed to delete image %s: %s", path, exc)
        raise DomainError(f"画像の削除に失敗しました: {exc}", status_code=500) from exc

    logger.info("Image deleted: %s", path)
    return SuccessResponse(message="画像が削除されました")
