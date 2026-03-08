"""
Posts router — /api/posts

HTTP layer only: parse request, delegate to post_service, translate exceptions.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.dependencies import get_admin_token_optional, require_admin
from app.schemas import (
    BulkLikesRequest,
    BulkLikesResponse,
    CommentCreate,
    CommentCreateResponse,
    CommentListResponse,
    LikeResponse,
    LikeStatusResponse,
    LikeToggleRequest,
    PasswordVerifyRequest,
    PasswordVerifyResponse,
    PinToggleResponse,
    PostCategoryFilter,
    PostCreate,
    PostCreateResponse,
    PostDeleteRequest,
    PostListResponse,
    PostSearchType,
    PostSortField,
    PostUpdate,
    PostUpdateResponse,
    SuccessResponse,
    ViewIncrementResponse,
)
from app.services import limiter
from app.services.exceptions import DomainError
from app.services import post_service, comment_service

router = APIRouter(prefix="/api/posts", tags=["posts"])


# ── exception translator ──────────────────────────────────────


def _raise(exc: DomainError) -> None:
    raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


# ═══════════════════════════════════════════════════════════════
# GET /  — list posts
# ═══════════════════════════════════════════════════════════════


@router.get("", response_model=PostListResponse)
@limiter.limit("30/minute")
async def list_posts(
    request: Request,
    session: AsyncSession = Depends(get_session),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=100),
    search: str = Query(default="", max_length=200),
    search_type: PostSearchType = Query(default=PostSearchType.TITLE, alias="searchType"),
    category: PostCategoryFilter | None = Query(default=None),
    sort: PostSortField = Query(default=PostSortField.NEWEST),
) -> PostListResponse:
    try:
        return await post_service.list_posts(
            session,
            page=page,
            limit=limit,
            search=search,
            search_type=search_type,
            category=category,
            sort=sort,
        )
    except DomainError as exc:
        _raise(exc)
        raise  # unreachable, satisfies mypy


# ═══════════════════════════════════════════════════════════════
# POST /  — create post
# ═══════════════════════════════════════════════════════════════


@router.post("", response_model=PostCreateResponse, status_code=201)
@limiter.limit("5/minute")
async def create_post(
    request: Request,
    body: PostCreate,
    session: AsyncSession = Depends(get_session),
) -> PostCreateResponse:
    try:
        return await post_service.create(session, body)
    except DomainError as exc:
        _raise(exc)
        raise


# ═══════════════════════════════════════════════════════════════
# PUT /{post_id}  — update post
# ═══════════════════════════════════════════════════════════════


@router.put("/{post_id}", response_model=PostUpdateResponse)
@limiter.limit("10/minute")
async def update_post(
    request: Request,
    post_id: str,
    body: PostUpdate,
    session: AsyncSession = Depends(get_session),
) -> PostUpdateResponse:
    try:
        return await post_service.update_post(session, post_id, body)
    except DomainError as exc:
        _raise(exc)
        raise


# ═══════════════════════════════════════════════════════════════
# DELETE /{post_id}  — delete post (password or admin)
# ═══════════════════════════════════════════════════════════════


@router.delete("/{post_id}", response_model=SuccessResponse)
@limiter.limit("10/minute")
async def delete_post(
    request: Request,
    post_id: str,
    body: PostDeleteRequest,
    session: AsyncSession = Depends(get_session),
    is_admin: bool = Depends(get_admin_token_optional),
) -> SuccessResponse:
    try:
        return await post_service.delete_post(
            session, post_id, body.password, is_admin=is_admin
        )
    except DomainError as exc:
        _raise(exc)
        raise


# ═══════════════════════════════════════════════════════════════
# POST /{post_id}/view  — increment view count
# ═══════════════════════════════════════════════════════════════


@router.post("/{post_id}/view", response_model=ViewIncrementResponse)
@limiter.limit("60/minute")
async def increment_view(
    request: Request,
    post_id: str,
    session: AsyncSession = Depends(get_session),
) -> ViewIncrementResponse:
    try:
        return await post_service.increment_view(session, post_id)
    except DomainError as exc:
        _raise(exc)
        raise


# ═══════════════════════════════════════════════════════════════
# POST /{post_id}/like  — toggle like
# ═══════════════════════════════════════════════════════════════


@router.post("/{post_id}/like", response_model=LikeResponse)
@limiter.limit("30/minute")
async def toggle_like(
    request: Request,
    post_id: str,
    body: LikeToggleRequest,
    session: AsyncSession = Depends(get_session),
) -> LikeResponse:
    try:
        return await post_service.toggle_like(session, post_id, body)
    except DomainError as exc:
        _raise(exc)
        raise


# ═══════════════════════════════════════════════════════════════
# GET /{post_id}/likes  — like status
# ═══════════════════════════════════════════════════════════════


@router.get("/{post_id}/likes", response_model=LikeStatusResponse)
@limiter.limit("60/minute")
async def get_like_status(
    request: Request,
    post_id: str,
    visitor_id: str | None = Query(default=None, alias="visitorId"),
    session: AsyncSession = Depends(get_session),
) -> LikeStatusResponse:
    try:
        return await post_service.get_like_status(session, post_id, visitor_id)
    except DomainError as exc:
        _raise(exc)
        raise


# ═══════════════════════════════════════════════════════════════
# POST /likes/bulk  — batch like counts
# ═══════════════════════════════════════════════════════════════


@router.post("/likes/bulk", response_model=BulkLikesResponse)
@limiter.limit("30/minute")
async def bulk_like_counts(
    request: Request,
    body: BulkLikesRequest,
    session: AsyncSession = Depends(get_session),
) -> BulkLikesResponse:
    try:
        return await post_service.bulk_like_counts(session, body)
    except DomainError as exc:
        _raise(exc)
        raise


# ═══════════════════════════════════════════════════════════════
# POST /{post_id}/verify-password
# ═══════════════════════════════════════════════════════════════


@router.post("/{post_id}/verify-password", response_model=PasswordVerifyResponse)
@limiter.limit("10/minute")
async def verify_post_password(
    request: Request,
    post_id: str,
    body: PasswordVerifyRequest,
    session: AsyncSession = Depends(get_session),
) -> PasswordVerifyResponse:
    try:
        return await post_service.verify_post_password(session, post_id, body.password)
    except DomainError as exc:
        _raise(exc)
        raise


# ═══════════════════════════════════════════════════════════════
# POST /{post_id}/pin  — admin only toggle pin
# ═══════════════════════════════════════════════════════════════


@router.post("/{post_id}/pin", response_model=PinToggleResponse)
@limiter.limit("10/minute")
async def toggle_pin(
    request: Request,
    post_id: str,
    session: AsyncSession = Depends(get_session),
    _admin: bool = Depends(require_admin),
) -> PinToggleResponse:
    try:
        return await post_service.toggle_pin(session, post_id)
    except DomainError as exc:
        _raise(exc)
        raise


# ═══════════════════════════════════════════════════════════════
# GET /{post_id}/comments  — list comments for post
# ═══════════════════════════════════════════════════════════════


@router.get("/{post_id}/comments", response_model=CommentListResponse)
@limiter.limit("30/minute")
async def list_comments(
    request: Request,
    post_id: str,
    session: AsyncSession = Depends(get_session),
) -> CommentListResponse:
    try:
        return await comment_service.list_comments(session, post_id)
    except DomainError as exc:
        _raise(exc)
        raise


# ═══════════════════════════════════════════════════════════════
# POST /{post_id}/comments  — create comment
# ═══════════════════════════════════════════════════════════════


@router.post("/{post_id}/comments", response_model=CommentCreateResponse, status_code=201)
@limiter.limit("5/minute")
async def create_comment(
    request: Request,
    post_id: str,
    body: CommentCreate,
    session: AsyncSession = Depends(get_session),
) -> CommentCreateResponse:
    try:
        return await comment_service.create_comment(session, post_id, body)
    except DomainError as exc:
        _raise(exc)
        raise
