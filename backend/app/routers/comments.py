"""
Comments router — /api/comments

HTTP layer only: edit, delete, password-verify for individual comments.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.dependencies import get_admin_token_optional
from app.schemas import (
    CommentDeleteRequest,
    CommentUpdate,
    CommentUpdateResponse,
    PasswordVerifyRequest,
    PasswordVerifyResponse,
    SuccessResponse,
)
from app.services import limiter
from app.services.exceptions import DomainError
from app.services import comment_service

router = APIRouter(prefix="/api/comments", tags=["comments"])


# ── exception translator ──────────────────────────────────────


def _raise(exc: DomainError) -> None:
    raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


# ═══════════════════════════════════════════════════════════════
# PUT /{comment_id}  — edit comment
# ═══════════════════════════════════════════════════════════════


@router.put("/{comment_id}", response_model=CommentUpdateResponse)
@limiter.limit("10/minute")
async def update_comment(
    request: Request,
    comment_id: str,
    body: CommentUpdate,
    session: AsyncSession = Depends(get_session),
) -> CommentUpdateResponse:
    try:
        return await comment_service.update_comment(session, comment_id, body)
    except DomainError as exc:
        _raise(exc)
        raise


# ═══════════════════════════════════════════════════════════════
# DELETE /{comment_id}  — delete comment (password or admin)
# ═══════════════════════════════════════════════════════════════


@router.delete("/{comment_id}", response_model=SuccessResponse)
@limiter.limit("10/minute")
async def delete_comment(
    request: Request,
    comment_id: str,
    body: CommentDeleteRequest,
    session: AsyncSession = Depends(get_session),
    is_admin: bool = Depends(get_admin_token_optional),
) -> SuccessResponse:
    try:
        return await comment_service.delete_comment(
            session, comment_id, body.password, is_admin=is_admin
        )
    except DomainError as exc:
        _raise(exc)
        raise


# ═══════════════════════════════════════════════════════════════
# POST /{comment_id}/verify-password
# ═══════════════════════════════════════════════════════════════


@router.post("/{comment_id}/verify-password", response_model=PasswordVerifyResponse)
@limiter.limit("10/minute")
async def verify_comment_password(
    request: Request,
    comment_id: str,
    body: PasswordVerifyRequest,
    session: AsyncSession = Depends(get_session),
) -> PasswordVerifyResponse:
    try:
        return await comment_service.verify_comment_password(
            session, comment_id, body.password
        )
    except DomainError as exc:
        _raise(exc)
        raise
