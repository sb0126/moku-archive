"""Admin domain service — login, stats, image management business logic.

Framework-agnostic: receives AsyncSession as a parameter, raises domain exceptions.
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
from app.services.auth import create_admin_token
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


async def get_stats(session: AsyncSession) -> AdminStatsResponse:
    """Aggregate dashboard statistics."""
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
    logger.info("Admin stats retrieved: %s", stats.model_dump())
    return AdminStatsResponse(stats=stats)


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
