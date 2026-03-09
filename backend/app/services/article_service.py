"""Article domain service — all article-related business logic.

Framework-agnostic: receives AsyncSession as a parameter, raises domain exceptions.
Caches article list and detail responses in Redis.
"""

import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Article
from app.schemas import (
    ArticleCreate,
    ArticleCreateResponse,
    ArticleListResponse,
    ArticleResponse,
    ArticleUpdate,
    ArticleUpdateResponse,
    SuccessResponse,
)
from app.services.cache import (
    delete_cached,
    get_cached,
    invalidate_namespace,
    set_cached,
)
from app.services.exceptions import ConflictError, NotFoundError
from app.services.storage import remove_files, resolve_storage_url

logger: logging.Logger = logging.getLogger(__name__)

_CACHE_NS = "articles"
_LIST_KEY = "all"
_TTL_LIST = 300  # 5 minutes — articles change infrequently
_TTL_DETAIL = 600  # 10 minutes


# ── private helpers ────────────────────────────────────────────


def _to_response(
    article: Article, *, resolved_url: str | None = None
) -> ArticleResponse:
    return ArticleResponse(
        id=article.id,
        image_url=resolved_url if resolved_url is not None else article.image_url,
        image_url_raw=article.image_url if resolved_url is not None else None,
        date=article.date,
        ja=article.ja,
        ko=article.ko,
        created_at=article.created_at,
        updated_at=article.updated_at,
    )


async def _get_or_404(session: AsyncSession, article_id: str) -> Article:
    result = await session.execute(
        select(Article).where(Article.id == article_id)  # type: ignore[arg-type]  # SQLModel column
    )
    article: Article | None = result.scalar_one_or_none()
    if article is None:
        raise NotFoundError("記事が見つかりません")
    return article


def _resolve_url(image_url: str | None) -> str | None:
    """Resolve storage: prefix into a public R2 URL, or return as-is."""
    if not image_url:
        return image_url
    return resolve_storage_url(image_url)


# ── public API ─────────────────────────────────────────────────


async def list_articles(session: AsyncSession) -> ArticleListResponse:
    """List all articles with resolved storage URLs (cached)."""
    # Try cache first
    cached = await get_cached(_CACHE_NS, _LIST_KEY)
    if cached is not None:
        logger.debug("Cache HIT: %s:%s", _CACHE_NS, _LIST_KEY)
        return ArticleListResponse(**cached)

    # Cache miss — query DB
    result = await session.execute(
        select(Article).order_by(Article.created_at.desc())  # type: ignore[attr-defined]  # SQLModel column
    )
    articles: list[Article] = list(result.scalars().all())

    response_list: list[ArticleResponse] = []
    for a in articles:
        resolved = _resolve_url(a.image_url)
        response_list.append(_to_response(a, resolved_url=resolved))

    response = ArticleListResponse(
        articles=response_list,
        count=len(response_list),
    )

    # Populate cache
    await set_cached(_CACHE_NS, _LIST_KEY, response.model_dump(), ttl_seconds=_TTL_LIST)
    logger.debug("Cache SET: %s:%s", _CACHE_NS, _LIST_KEY)

    return response


async def get_article(session: AsyncSession, article_id: str) -> ArticleResponse:
    """Get a single article by ID with resolved storage URL (cached)."""
    cache_key = f"detail:{article_id}"
    cached = await get_cached(_CACHE_NS, cache_key)
    if cached is not None:
        logger.debug("Cache HIT: %s:%s", _CACHE_NS, cache_key)
        return ArticleResponse(**cached)

    article = await _get_or_404(session, article_id)
    resolved = _resolve_url(article.image_url)
    response = _to_response(article, resolved_url=resolved)

    await set_cached(_CACHE_NS, cache_key, response.model_dump(), ttl_seconds=_TTL_DETAIL)
    logger.debug("Cache SET: %s:%s", _CACHE_NS, cache_key)

    return response


async def create_article(
    session: AsyncSession, body: ArticleCreate
) -> ArticleCreateResponse:
    """Create a new article (slug uniqueness check)."""
    existing = await session.execute(
        select(Article).where(Article.id == body.id)  # type: ignore[arg-type]  # SQLModel column
    )
    if existing.scalar_one_or_none() is not None:
        raise ConflictError(f"スラッグ '{body.id}' は既に使用されています")

    ja_data: dict[str, Any] = body.ja.model_dump(by_alias=True)
    ko_data: dict[str, Any] | None = body.ko.model_dump(by_alias=True) if body.ko else None

    now = datetime.now(timezone.utc)
    article = Article(
        id=body.id,
        image_url=body.image_url,
        date=body.date,
        ja=ja_data,
        ko=ko_data,
        created_at=now,
        updated_at=now,
    )
    session.add(article)
    await session.commit()
    await session.refresh(article)

    # Invalidate article caches
    await invalidate_namespace(_CACHE_NS)

    logger.info("Article created: id=%s", article.id)
    return ArticleCreateResponse(
        message="記事が作成されました",
        article=_to_response(article),
    )


async def update_article(
    session: AsyncSession, article_id: str, body: ArticleUpdate
) -> ArticleUpdateResponse:
    """Partial update merge for an article."""
    article = await _get_or_404(session, article_id)

    if body.ja is not None:
        new_ja: dict[str, Any] = body.ja.model_dump(by_alias=True)
        merged_ja: dict[str, Any] = {**article.ja, **new_ja}
        article.ja = merged_ja

    if body.ko is not None:
        new_ko: dict[str, Any] = body.ko.model_dump(by_alias=True)
        if article.ko is not None:
            merged_ko: dict[str, Any] = {**article.ko, **new_ko}
            article.ko = merged_ko
        else:
            article.ko = new_ko

    if body.image_url is not None:
        article.image_url = body.image_url

    if body.date is not None:
        article.date = body.date

    article.updated_at = datetime.now(timezone.utc)

    session.add(article)
    await session.commit()
    await session.refresh(article)

    # Invalidate article caches (list + detail)
    await invalidate_namespace(_CACHE_NS)

    logger.info("Article updated: id=%s", article_id)
    return ArticleUpdateResponse(
        message="記事が更新されました",
        article=_to_response(article),
    )


async def delete_article(session: AsyncSession, article_id: str) -> SuccessResponse:
    """Delete an article + cleanup storage image."""
    article = await _get_or_404(session, article_id)

    if article.image_url and article.image_url.startswith("storage:"):
        path: str = article.image_url.removeprefix("storage:")
        try:
            await remove_files([path])
        except Exception:
            # Non-critical — log and continue with deletion
            logger.warning(
                "Failed to cleanup storage image for article %s: %s", article_id, path
            )

    await session.delete(article)
    await session.commit()

    # Invalidate article caches
    await invalidate_namespace(_CACHE_NS)

    logger.info("Article deleted: id=%s", article_id)
    return SuccessResponse(message="記事が削除されました")
