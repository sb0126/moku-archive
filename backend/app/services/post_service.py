"""Post domain service — all post-related business logic.

Framework-agnostic: receives AsyncSession as a parameter, raises domain exceptions.
"""

import logging
import time
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col

from app.models import Comment, Post, PostLike
from app.schemas import (
    BulkLikesRequest,
    BulkLikesResponse,
    LikeResponse,
    LikeStatusResponse,
    LikeToggleRequest,
    PasswordVerifyResponse,
    PinToggleResponse,
    PostCategoryFilter,
    PostCreate,
    PostCreateResponse,
    PostListResponse,
    PostResponse,
    PostSearchType,
    PostSortField,
    PostUpdate,
    PostUpdateResponse,
    SuccessResponse,
    ViewIncrementResponse,
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
    return f"post_{int(time.time() * 1000)}"


def _to_response(post: Post, *, like_count: int = 0) -> PostResponse:
    return PostResponse(
        id=post.id,
        numeric_id=post.numeric_id,
        title=post.title,
        author=post.author,
        content=post.content,
        views=post.views,
        comments=post.comment_count,
        pinned=post.pinned,
        pinned_at=post.pinned_at,
        experience=post.experience,
        category=post.category,
        created_at=post.created_at,
        updated_at=post.updated_at,
    )


async def _get_or_404(session: AsyncSession, post_id: str) -> Post:
    result = await session.execute(select(Post).where(col(Post.id) == post_id))
    post: Post | None = result.scalar_one_or_none()
    if post is None:
        raise NotFoundError("投稿が見つかりません")
    return post


async def _like_count(session: AsyncSession, post_id: str) -> int:
    result = await session.execute(
        select(func.count()).select_from(PostLike).where(col(PostLike.post_id) == post_id)
    )
    cnt: int = result.scalar_one()
    return cnt


# ── public API ─────────────────────────────────────────────────


async def list_posts(
    session: AsyncSession,
    *,
    page: int = 1,
    limit: int = 10,
    search: str = "",
    search_type: PostSearchType = PostSearchType.TITLE,
    category: PostCategoryFilter | None = None,
    sort: PostSortField = PostSortField.NEWEST,
) -> PostListResponse:
    """List posts with search, filtering, sorting, and pagination."""
    conditions: list[Any] = []

    if search:
        pattern = f"%{search}%"
        if search_type == PostSearchType.TITLE:
            conditions.append(col(Post.title).ilike(pattern))
        elif search_type == PostSearchType.AUTHOR:
            conditions.append(col(Post.author).ilike(pattern))
        elif search_type == PostSearchType.CONTENT:
            conditions.append(col(Post.content).ilike(pattern))

    if category is not None:
        conditions.append(col(Post.category) == category.value)

    # total count
    count_stmt = select(func.count()).select_from(Post)
    for cond in conditions:
        count_stmt = count_stmt.where(cond)
    total: int = (await session.execute(count_stmt)).scalar_one()

    total_pages = max(1, (total + limit - 1) // limit)

    # sort: likes requires LEFT JOIN
    if sort == PostSortField.LIKES:
        like_count_sub = (
            select(
                col(PostLike.post_id).label("post_id"),
                func.count().label("like_cnt"),
            )
            .group_by(col(PostLike.post_id))
            .subquery()
        )
        query = select(Post).outerjoin(
            like_count_sub, col(Post.id) == like_count_sub.c.post_id
        )
        for cond in conditions:
            query = query.where(cond)
        query = query.order_by(
            col(Post.pinned).desc(),
            func.coalesce(like_count_sub.c.like_cnt, 0).desc(),
            col(Post.created_at).desc(),
        )
    else:
        query = select(Post)
        for cond in conditions:
            query = query.where(cond)

        order_clauses: list[Any] = [col(Post.pinned).desc()]
        if sort == PostSortField.NEWEST:
            order_clauses.append(col(Post.numeric_id).desc())
        elif sort == PostSortField.OLDEST:
            order_clauses.append(col(Post.created_at).asc())
        elif sort == PostSortField.VIEWS:
            order_clauses.append(col(Post.views).desc())
            order_clauses.append(col(Post.created_at).desc())
        elif sort == PostSortField.COMMENTS:
            order_clauses.append(col(Post.comment_count).desc())
            order_clauses.append(col(Post.created_at).desc())

        query = query.order_by(*order_clauses)

    # pagination
    offset = (page - 1) * limit
    query = query.offset(offset).limit(limit)

    result = await session.execute(query)
    posts: list[Post] = list(result.scalars().all())

    return PostListResponse(
        posts=[_to_response(p) for p in posts],
        count=len(posts),
        total=total,
        total_pages=total_pages,
        current_page=page,
        limit=limit,
    )


async def create(session: AsyncSession, body: PostCreate) -> PostCreateResponse:
    """Create a new post with sanitization and spam checking."""
    author = sanitize_text(body.author)
    title = sanitize_text(body.title)
    content = sanitize_text(body.content)

    if not author or not title or not content:
        raise ValidationError("入力内容が無効です")

    spam_result = check_spam(f"{title} {content}")
    if spam_result.is_spam:
        logger.warning("Spam detected in post creation by %s: %s", author, spam_result.reason)
        raise SpamDetectedError(spam_result.reason or "スパムが検出されました")

    # generate numeric_id — max + 1
    max_id_result = await session.execute(select(func.max(col(Post.numeric_id))))
    max_numeric: int | None = max_id_result.scalar_one_or_none()
    numeric_id = (max_numeric or 0) + 1

    now = datetime.now(timezone.utc)
    post = Post(
        id=_generate_id(),
        numeric_id=numeric_id,
        title=title,
        author=author,
        content=content,
        password=hash_password(body.password),
        experience=body.experience,
        category=body.category,
        views=0,
        comment_count=0,
        pinned=False,
        pinned_at=None,
        created_at=now,
        updated_at=now,
    )
    session.add(post)
    await session.commit()
    await session.refresh(post)

    logger.info("Post created: id=%s, author=%s", post.id, author)
    return PostCreateResponse(
        message="投稿が作成されました",
        post=_to_response(post),
    )


async def update_post(
    session: AsyncSession, post_id: str, body: PostUpdate
) -> PostUpdateResponse:
    """Update an existing post (password-verified)."""
    post = await _get_or_404(session, post_id)

    if not verify_password(body.password, post.password):
        raise ForbiddenError("パスワードが正しくありません")

    # lazy rehash
    if needs_rehash(post.password):
        post.password = hash_password(body.password)

    if body.title is not None:
        sanitized_title = sanitize_text(body.title)
        if not sanitized_title:
            raise ValidationError("タイトルが無効です")
        post.title = sanitized_title

    if body.content is not None:
        sanitized_content = sanitize_text(body.content)
        if not sanitized_content:
            raise ValidationError("内容が無効です")
        spam_result = check_spam(f"{post.title} {sanitized_content}")
        if spam_result.is_spam:
            logger.warning("Spam detected in post update %s: %s", post_id, spam_result.reason)
            raise SpamDetectedError(spam_result.reason or "スパムが検出されました")
        post.content = sanitized_content

    post.updated_at = datetime.now(timezone.utc)
    session.add(post)
    await session.commit()
    await session.refresh(post)

    logger.info("Post updated: id=%s", post_id)
    return PostUpdateResponse(
        message="投稿が更新されました",
        post=_to_response(post),
    )


async def delete_post(
    session: AsyncSession,
    post_id: str,
    password: str | None,
    *,
    is_admin: bool,
) -> SuccessResponse:
    """Delete a post (password or admin bypass). Cascades comments + likes."""
    post = await _get_or_404(session, post_id)

    if not is_admin:
        if password is None:
            raise ValidationError("パスワードが必要です")
        if not verify_password(password, post.password):
            raise ForbiddenError("パスワードが正しくありません")

    # cascade: delete comments + likes
    await session.execute(delete(Comment).where(col(Comment.post_id) == post_id))
    await session.execute(delete(PostLike).where(col(PostLike.post_id) == post_id))
    await session.delete(post)
    await session.commit()

    logger.info("Post deleted: id=%s, by_admin=%s", post_id, is_admin)
    return SuccessResponse(message="投稿が削除されました")


async def increment_view(session: AsyncSession, post_id: str) -> ViewIncrementResponse:
    """Increment view count for a post."""
    post = await _get_or_404(session, post_id)

    await session.execute(
        update(Post)
        .where(col(Post.id) == post_id)
        .values(views=col(Post.views) + 1)
    )
    await session.commit()
    await session.refresh(post)

    return ViewIncrementResponse(views=post.views)


async def toggle_like(
    session: AsyncSession, post_id: str, body: LikeToggleRequest
) -> LikeResponse:
    """Toggle like status for a visitor on a post."""
    await _get_or_404(session, post_id)

    existing = await session.execute(
        select(PostLike).where(
            col(PostLike.post_id) == post_id,
            col(PostLike.visitor_id) == body.visitor_id,
        )
    )
    like_row: PostLike | None = existing.scalar_one_or_none()

    if like_row is not None:
        await session.delete(like_row)
        liked = False
    else:
        new_like = PostLike(
            post_id=post_id,
            visitor_id=body.visitor_id,
            created_at=datetime.now(timezone.utc),
        )
        session.add(new_like)
        liked = True

    await session.commit()
    count = await _like_count(session, post_id)

    return LikeResponse(liked=liked, likes=count)


async def get_like_status(
    session: AsyncSession, post_id: str, visitor_id: str | None
) -> LikeStatusResponse:
    """Get like count and visitor's like status for a post."""
    await _get_or_404(session, post_id)

    count = await _like_count(session, post_id)

    liked = False
    if visitor_id:
        existing = await session.execute(
            select(PostLike).where(
                col(PostLike.post_id) == post_id,
                col(PostLike.visitor_id) == visitor_id,
            )
        )
        liked = existing.scalar_one_or_none() is not None

    return LikeStatusResponse(likes=count, liked=liked)


async def bulk_like_counts(
    session: AsyncSession, body: BulkLikesRequest
) -> BulkLikesResponse:
    """Get like counts for multiple posts in one query."""
    if not body.post_ids:
        return BulkLikesResponse(likes={})

    from sqlalchemy.engine import Result as SAResult

    result: SAResult[Any] = await session.execute(
        select(
            col(PostLike.post_id).label("post_id"),
            func.count().label("cnt"),
        )
        .where(col(PostLike.post_id).in_(body.post_ids))
        .group_by(col(PostLike.post_id))
    )
    rows = result.all()
    likes_map: dict[str, int] = {str(row.post_id): int(row.cnt) for row in rows}

    for pid in body.post_ids:
        if pid not in likes_map:
            likes_map[pid] = 0

    return BulkLikesResponse(likes=likes_map)


async def verify_post_password(
    session: AsyncSession, post_id: str, password: str
) -> PasswordVerifyResponse:
    """Verify password for a post."""
    post = await _get_or_404(session, post_id)
    verified = verify_password(password, post.password)
    return PasswordVerifyResponse(verified=verified)


async def toggle_pin(session: AsyncSession, post_id: str) -> PinToggleResponse:
    """Toggle pin status for a post (admin action)."""
    post = await _get_or_404(session, post_id)

    if post.pinned:
        post.pinned = False
        post.pinned_at = None
        message = "投稿のピン留めが解除されました"
    else:
        post.pinned = True
        post.pinned_at = datetime.now(timezone.utc)
        message = "投稿がピン留めされました"

    post.updated_at = datetime.now(timezone.utc)
    session.add(post)
    await session.commit()
    await session.refresh(post)

    logger.info("Post pin toggled: id=%s, pinned=%s", post_id, post.pinned)
    return PinToggleResponse(message=message, post=_to_response(post))
