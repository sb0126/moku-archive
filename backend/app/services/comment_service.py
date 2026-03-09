"""Comment domain service — all comment-related business logic.

Framework-agnostic: receives AsyncSession as a parameter, raises domain exceptions.
Mutations invalidate post and admin stats caches.
"""

import logging
import time
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col

from app.models import Comment, Post
from app.schemas import (
    CommentCreate,
    CommentCreateResponse,
    CommentListResponse,
    CommentResponse,
    CommentUpdate,
    CommentUpdateResponse,
    PasswordVerifyResponse,
    SuccessResponse,
)
from app.services.auth import hash_password, needs_rehash, verify_password
from app.services.exceptions import (
    ForbiddenError,
    NotFoundError,
    SpamDetectedError,
    ValidationError,
)
from app.services.sanitize import sanitize_text
from app.services.spam import check_spam

logger: logging.Logger = logging.getLogger(__name__)


# ── private helpers ────────────────────────────────────────────


def _generate_id() -> str:
    return f"comment_{int(time.time() * 1000)}"


def _to_response(comment: Comment) -> CommentResponse:
    return CommentResponse(
        id=comment.id,
        post_id=comment.post_id,
        parent_id=comment.parent_id,
        author=comment.author,
        content=comment.content,
        created_at=comment.created_at,
        updated_at=comment.updated_at,
    )


async def _get_or_404(session: AsyncSession, comment_id: str) -> Comment:
    result = await session.execute(select(Comment).where(col(Comment.id) == comment_id))
    comment: Comment | None = result.scalar_one_or_none()
    if comment is None:
        raise NotFoundError("コメントが見つかりません")
    return comment


async def _get_post_or_404(session: AsyncSession, post_id: str) -> Post:
    result = await session.execute(select(Post).where(col(Post.id) == post_id))
    post: Post | None = result.scalar_one_or_none()
    if post is None:
        raise NotFoundError("投稿が見つかりません")
    return post


# ── public API ─────────────────────────────────────────────────


async def list_comments(
    session: AsyncSession, post_id: str
) -> CommentListResponse:
    """List all comments for a post, ordered oldest-first."""
    await _get_post_or_404(session, post_id)

    result = await session.execute(
        select(Comment)
        .where(col(Comment.post_id) == post_id)
        .order_by(col(Comment.created_at).asc())
    )
    comments: list[Comment] = list(result.scalars().all())

    return CommentListResponse(
        comments=[_to_response(c) for c in comments],
        count=len(comments),
    )


async def create_comment(
    session: AsyncSession, post_id: str, body: CommentCreate
) -> CommentCreateResponse:
    """Create a comment on a post."""
    post = await _get_post_or_404(session, post_id)

    author = sanitize_text(body.author)
    content = sanitize_text(body.content)

    if not author or not content:
        raise ValidationError("入力内容が無効です")

    spam_result = check_spam(content)
    if spam_result.is_spam:
        logger.warning("Spam detected in comment by %s on post %s", author, post_id)
        raise SpamDetectedError(spam_result.reason or "スパムが検出されました")

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    comment = Comment(
        id=_generate_id(),
        post_id=post_id,
        parent_id=body.parent_id,
        author=author,
        content=content,
        password=hash_password(body.password),
        created_at=now,
        updated_at=now,
    )
    session.add(comment)

    # increment comment_count
    post.comment_count += 1
    post.updated_at = now
    session.add(post)

    await session.commit()
    await session.refresh(comment)
    await session.refresh(post)

    # Invalidate caches (comment count changed)
    from app.services.cache import invalidate_namespace
    from app.services.admin_service import invalidate_stats_cache
    await invalidate_namespace("posts")
    await invalidate_stats_cache()

    logger.info("Comment created: id=%s on post %s by %s", comment.id, post_id, author)
    return CommentCreateResponse(
        message="コメントが投稿されました",
        comment=_to_response(comment),
        commentCount=post.comment_count,
    )


async def update_comment(
    session: AsyncSession, comment_id: str, body: CommentUpdate
) -> CommentUpdateResponse:
    """Update a comment (password-verified)."""
    comment = await _get_or_404(session, comment_id)

    if not verify_password(body.password, comment.password):
        raise ForbiddenError("パスワードが正しくありません")

    # lazy rehash
    if needs_rehash(comment.password):
        comment.password = hash_password(body.password)

    sanitized_content = sanitize_text(body.content)
    if not sanitized_content:
        raise ValidationError("内容が無効です")

    spam_result = check_spam(sanitized_content)
    if spam_result.is_spam:
        logger.warning("Spam detected in comment update %s: %s", comment_id, spam_result.reason)
        raise SpamDetectedError(spam_result.reason or "スパムが検出されました")

    comment.content = sanitized_content
    comment.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)

    session.add(comment)
    await session.commit()
    await session.refresh(comment)

    logger.info("Comment updated: id=%s", comment_id)
    return CommentUpdateResponse(
        message="コメントが更新されました",
        comment=_to_response(comment),
    )


async def delete_comment(
    session: AsyncSession,
    comment_id: str,
    password: str | None,
    *,
    is_admin: bool,
) -> SuccessResponse:
    """Delete a comment (password or admin bypass). Decrements parent post comment_count."""
    comment = await _get_or_404(session, comment_id)

    if not is_admin:
        if password is None:
            raise ValidationError("パスワードが必要です")
        if not verify_password(password, comment.password):
            raise ForbiddenError("パスワードが正しくありません")

    # decrement parent post comment_count (floor at 0)
    result = await session.execute(select(Post).where(col(Post.id) == comment.post_id))
    post: Post | None = result.scalar_one_or_none()
    if post is not None:
        post.comment_count = max(0, post.comment_count - 1)
        post.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
        session.add(post)

    await session.delete(comment)
    await session.commit()

    # Invalidate caches (comment count changed)
    from app.services.cache import invalidate_namespace
    from app.services.admin_service import invalidate_stats_cache
    await invalidate_namespace("posts")
    await invalidate_stats_cache()

    logger.info("Comment deleted: id=%s, by_admin=%s", comment_id, is_admin)
    return SuccessResponse(message="コメントが削除されました")


async def verify_comment_password(
    session: AsyncSession, comment_id: str, password: str
) -> PasswordVerifyResponse:
    """Verify password for a comment."""
    comment = await _get_or_404(session, comment_id)
    verified = verify_password(password, comment.password)
    return PasswordVerifyResponse(verified=verified)
