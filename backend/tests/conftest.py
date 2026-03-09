"""
Shared test fixtures — in-memory SQLite, httpx AsyncClient, admin tokens.

Handles the PostgreSQL → SQLite impedance mismatch (JSONB → JSON) so that
all models work in a fast, isolated test environment.
"""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import JSON, event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

# ── Patch JSONB → JSON for SQLite before any model is imported ──────────
from sqlalchemy.dialects.postgresql import JSONB  # noqa: E402

# Register a compilation rule so JSONB renders as plain JSON on SQLite.
from sqlalchemy.ext.compiler import compiles  # noqa: E402


@compiles(JSONB, "sqlite")
def _compile_jsonb_sqlite(type_: JSONB, compiler: object, **kw: object) -> str:
    return "JSON"


# Now import app / models (their JSONB columns will be compiled correctly).
from app.database import get_session  # noqa: E402
from app.main import app  # noqa: E402
from app.services.auth import create_admin_token  # noqa: E402


# ── Database fixtures ──────────────────────────────────────────────────


@pytest.fixture
async def test_engine():
    """Async in-memory SQLite engine — created/destroyed per test."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        # SQLite doesn't support JSON natively, but sqlalchemy handles
        # serialization via the JSON type when we compile JSONB → JSON.
        json_serializer=None,
    )
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
async def test_session(test_engine):
    """Async session bound to the in-memory engine — one per test."""
    session_factory = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with session_factory() as session:
        yield session


@pytest.fixture
async def client(test_session: AsyncSession):
    """httpx AsyncClient wired to the FastAPI app with the test DB override.

    Also disables the SlowAPI rate-limiter so tests don't hit 429s.
    """

    async def override_session():
        yield test_session

    app.dependency_overrides[get_session] = override_session

    # Disable rate-limiting during tests
    original_enabled = app.state.limiter.enabled
    app.state.limiter.enabled = False

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.state.limiter.enabled = original_enabled
    app.dependency_overrides.clear()


# ── Auth helpers ───────────────────────────────────────────────────────


@pytest.fixture
def admin_token() -> str:
    """Valid JWT admin token for protected endpoints."""
    return create_admin_token()


@pytest.fixture
def admin_headers(admin_token: str) -> dict[str, str]:
    """Headers dict with a valid admin JWT."""
    return {"x-admin-token": admin_token}


# ── Data factory helpers ───────────────────────────────────────────────


@pytest.fixture
def make_post_payload():
    """Factory: build a valid PostCreate JSON body."""

    _counter = 0

    def _make(**overrides: object) -> dict:
        nonlocal _counter
        _counter += 1
        defaults = {
            "author": f"テストユーザー{_counter}",
            "title": f"テスト投稿 #{_counter}",
            "content": f"これはテスト投稿の内容です #{_counter}",
            "password": "test1234",
            "category": "chat",
        }
        defaults.update(overrides)
        return defaults

    return _make


@pytest.fixture
def make_comment_payload():
    """Factory: build a valid CommentCreate JSON body."""

    _counter = 0

    def _make(**overrides: object) -> dict:
        nonlocal _counter
        _counter += 1
        defaults = {
            "author": f"コメントユーザー{_counter}",
            "content": f"テストコメント内容 #{_counter}",
            "password": "test1234",
        }
        defaults.update(overrides)
        return defaults

    return _make


@pytest.fixture
def make_inquiry_payload():
    """Factory: build a valid InquiryCreate JSON body."""

    _counter = 0

    def _make(**overrides: object) -> dict:
        nonlocal _counter
        _counter += 1
        defaults = {
            "name": f"テスト太郎{_counter}",
            "email": f"test{_counter}@example.com",
            "phone": "09012345678",
            "age": 25,
            "preferredDate": "2026-04-01",
            "plan": "basic",
            "message": "テストメッセージです",
        }
        defaults.update(overrides)
        return defaults

    return _make


@pytest.fixture
def make_article_payload():
    """Factory: build a valid ArticleCreate JSON body."""

    _counter = 0

    def _make(**overrides: object) -> dict:
        nonlocal _counter
        _counter += 1
        defaults = {
            "id": f"test-article-{_counter}",
            "ja": {
                "title": f"テスト記事 #{_counter}",
                "category": "生活",
                "excerpt": "テスト概要です",
                "content": "テスト記事の本文です",
                "imageAlt": "テスト画像",
                "author": "テスト著者",
                "readTime": "5分",
                "tags": ["テスト", "記事"],
            },
            "imageUrl": None,
            "date": "2026-01-15",
        }
        defaults.update(overrides)
        return defaults

    return _make
