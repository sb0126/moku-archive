"""Inquiry domain service — all inquiry-related business logic.

Framework-agnostic: receives AsyncSession as a parameter, raises domain exceptions.
Mutations invalidate the admin stats cache.
"""

import logging
import time
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Inquiry
from app.schemas import (
    InquiryCreate,
    InquiryCreateResponse,
    InquiryListResponse,
    InquiryResponse,
    InquiryStatusUpdate,
    InquiryStatusUpdateResponse,
    SuccessResponse,
)
from app.services.exceptions import NotFoundError, SpamDetectedError, ValidationError
from app.services.sanitize import sanitize_text
from app.services.spam import check_spam

logger: logging.Logger = logging.getLogger(__name__)


# ── private helpers ────────────────────────────────────────────


def _generate_id() -> str:
    return f"inq_{int(time.time() * 1000)}"


def _to_response(inquiry: Inquiry) -> InquiryResponse:
    return InquiryResponse(
        id=inquiry.id,
        name=inquiry.name,
        email=inquiry.email,
        phone=inquiry.phone,
        age=inquiry.age,
        preferred_date=inquiry.preferred_date,
        plan=inquiry.plan,
        message=inquiry.message,
        status=inquiry.status,
        admin_note=inquiry.admin_note,
        created_at=inquiry.created_at,
        updated_at=inquiry.updated_at,
    )


async def _get_or_404(session: AsyncSession, inquiry_id: str) -> Inquiry:
    result = await session.execute(
        select(Inquiry).where(Inquiry.id == inquiry_id)  # type: ignore[arg-type]  # SQLModel column
    )
    inquiry: Inquiry | None = result.scalar_one_or_none()
    if inquiry is None:
        raise NotFoundError("お問い合わせが見つかりません")
    return inquiry


# ── public API ─────────────────────────────────────────────────


async def create_inquiry(
    session: AsyncSession, body: InquiryCreate
) -> InquiryCreateResponse:
    """Create a new inquiry with sanitization and spam checking."""
    name = sanitize_text(body.name)
    message = sanitize_text(body.message)

    if not name:
        raise ValidationError("入力内容が無効です")

    if message:
        spam_result = check_spam(message)
        if spam_result.is_spam:
            logger.warning("Spam detected in inquiry from %s: %s", name, spam_result.reason)
            raise SpamDetectedError(spam_result.reason or "スパムが検出されました")

    now = datetime.now(timezone.utc)
    inquiry = Inquiry(
        id=_generate_id(),
        name=name,
        email=body.email,
        phone=body.phone,
        age=body.age,
        preferred_date=body.preferred_date,
        plan=body.plan,
        message=message,
        status="pending",
        admin_note=None,
        created_at=now,
        updated_at=now,
    )
    session.add(inquiry)
    await session.commit()
    await session.refresh(inquiry)

    # Invalidate admin stats cache
    from app.services.admin_service import invalidate_stats_cache
    await invalidate_stats_cache()

    logger.info("Inquiry created: id=%s, name=%s", inquiry.id, name)
    return InquiryCreateResponse(
        message="お問い合わせが送信されました",
        inquiry=_to_response(inquiry),
    )


async def list_inquiries(session: AsyncSession) -> InquiryListResponse:
    """List all inquiries, newest first."""
    result = await session.execute(
        select(Inquiry).order_by(Inquiry.created_at.desc())  # type: ignore[attr-defined]  # SQLModel column
    )
    inquiries: list[Inquiry] = list(result.scalars().all())

    return InquiryListResponse(
        inquiries=[_to_response(i) for i in inquiries],
        count=len(inquiries),
    )


async def update_inquiry_status(
    session: AsyncSession, inquiry_id: str, body: InquiryStatusUpdate
) -> InquiryStatusUpdateResponse:
    """Update inquiry status and optional admin note."""
    inquiry = await _get_or_404(session, inquiry_id)

    inquiry.status = body.status
    if body.admin_note is not None:
        inquiry.admin_note = body.admin_note
    inquiry.updated_at = datetime.now(timezone.utc)

    session.add(inquiry)
    await session.commit()
    await session.refresh(inquiry)

    # Invalidate admin stats cache
    from app.services.admin_service import invalidate_stats_cache
    await invalidate_stats_cache()

    logger.info("Inquiry status updated: id=%s, status=%s", inquiry_id, body.status)
    return InquiryStatusUpdateResponse(
        message="ステータスが更新されました",
        inquiry=_to_response(inquiry),
    )


async def delete_inquiry(session: AsyncSession, inquiry_id: str) -> SuccessResponse:
    """Delete an inquiry."""
    inquiry = await _get_or_404(session, inquiry_id)

    await session.delete(inquiry)
    await session.commit()

    # Invalidate admin stats cache
    from app.services.admin_service import invalidate_stats_cache
    await invalidate_stats_cache()

    logger.info("Inquiry deleted: id=%s", inquiry_id)
    return SuccessResponse(message="お問い合わせが削除されました")
