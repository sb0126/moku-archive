"""
Articles router — /api/articles

HTTP layer only: delegate to article_service, translate exceptions.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.dependencies import require_admin
from app.schemas import (
    ArticleCreate,
    ArticleCreateResponse,
    ArticleListResponse,
    ArticleResponse,
    ArticleUpdate,
    ArticleUpdateResponse,
    SuccessResponse,
)
from app.services import limiter
from app.services.exceptions import DomainError
from app.services import article_service

router = APIRouter(prefix="/api/articles", tags=["articles"])


# ── exception translator ──────────────────────────────────────


def _raise(exc: DomainError) -> None:
    raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


# ═══════════════════════════════════════════════════════════════
# GET /  — list articles (public, resolve storage URLs)
# ═══════════════════════════════════════════════════════════════


@router.get("", response_model=ArticleListResponse)
@limiter.limit("30/minute")
async def list_articles(
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> ArticleListResponse:
    try:
        return await article_service.list_articles(session)
    except DomainError as exc:
        _raise(exc)
        raise


# ═══════════════════════════════════════════════════════════════
# GET /{article_id}  — article detail (public)
# ═══════════════════════════════════════════════════════════════


@router.get("/{article_id}", response_model=ArticleResponse)
@limiter.limit("60/minute")
async def get_article(
    request: Request,
    article_id: str,
    session: AsyncSession = Depends(get_session),
) -> ArticleResponse:
    try:
        return await article_service.get_article(session, article_id)
    except DomainError as exc:
        _raise(exc)
        raise


# ═══════════════════════════════════════════════════════════════
# POST /  — create article (admin, slug duplicate check)
# ═══════════════════════════════════════════════════════════════


@router.post("", response_model=ArticleCreateResponse, status_code=201)
@limiter.limit("10/minute")
async def create_article(
    request: Request,
    body: ArticleCreate,
    session: AsyncSession = Depends(get_session),
    _admin: bool = Depends(require_admin),
) -> ArticleCreateResponse:
    try:
        return await article_service.create_article(session, body)
    except DomainError as exc:
        _raise(exc)
        raise


# ═══════════════════════════════════════════════════════════════
# PUT /{article_id}  — partial update merge (admin)
# ═══════════════════════════════════════════════════════════════


@router.put("/{article_id}", response_model=ArticleUpdateResponse)
@limiter.limit("10/minute")
async def update_article(
    request: Request,
    article_id: str,
    body: ArticleUpdate,
    session: AsyncSession = Depends(get_session),
    _admin: bool = Depends(require_admin),
) -> ArticleUpdateResponse:
    try:
        return await article_service.update_article(session, article_id, body)
    except DomainError as exc:
        _raise(exc)
        raise


# ═══════════════════════════════════════════════════════════════
# DELETE /{article_id}  — delete article + storage cleanup (admin)
# ═══════════════════════════════════════════════════════════════


@router.delete("/{article_id}", response_model=SuccessResponse)
@limiter.limit("10/minute")
async def delete_article(
    request: Request,
    article_id: str,
    session: AsyncSession = Depends(get_session),
    _admin: bool = Depends(require_admin),
) -> SuccessResponse:
    try:
        return await article_service.delete_article(session, article_id)
    except DomainError as exc:
        _raise(exc)
        raise
