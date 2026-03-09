# Testing Guide

## Stack

- **pytest** — Test runner
- **pytest-asyncio** — Async test support
- **httpx** — AsyncClient for API testing
- **aiosqlite** — SQLite async driver for tests
- **pytest-cov** — Coverage reporting

## Project Setup

```
# requirements-dev.txt
-r requirements.txt
pytest>=8.0
pytest-asyncio>=0.24
httpx>=0.28
aiosqlite>=0.20
pytest-cov>=5.0
```

```ini
# pytest.ini
[pytest]
asyncio_mode = auto
```

## Test Categories

| Category | Scope | Speed | Required |
|----------|-------|-------|----------|
| **Unit** | Service functions | Fast | ✅ Yes |
| **Integration** | API endpoints via httpx | Medium | ✅ Yes |
| **Database** | Complex queries | Medium | When applicable |

## Fixtures

```python
# tests/conftest.py
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlmodel import SQLModel

from app.main import app
from app.database import get_session


@pytest.fixture
async def test_session():
    """In-memory SQLite session for isolated tests."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest.fixture
async def client(test_session: AsyncSession):
    """httpx AsyncClient with test DB."""
    async def override_session():
        yield test_session

    app.dependency_overrides[get_session] = override_session

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client

    app.dependency_overrides.clear()
```

### JSONB/SQLite Compatibility

The `database.py` module registers a JSONB → JSON compiler for SQLite, so
Article models with JSONB columns work in test environments automatically.

## Unit Tests (Services)

```python
# tests/test_services.py
import pytest
from app.services.sanitize import sanitize_text
from app.services.spam import check_spam


def test_sanitize_removes_script_tags():
    result = sanitize_text('<script>alert("xss")</script>Hello')
    assert "script" not in result.lower()
    assert "Hello" in result


def test_sanitize_preserves_normal_text():
    result = sanitize_text("これは普通のテキストです")
    assert result == "これは普通のテキストです"


def test_spam_detection_urls():
    result = check_spam("http://a.com http://b.com http://c.com http://d.com")
    assert result.is_spam is True


def test_spam_clean_content():
    result = check_spam("日本のビザ取得について教えてください")
    assert result.is_spam is False
```

## Integration Tests (API)

```python
# tests/test_posts.py
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_post(client: AsyncClient):
    response = await client.post("/api/posts", json={
        "title": "テスト投稿",
        "author": "testuser",
        "content": "テスト内容です",
        "password": "test1234",
        "category": "chat",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["post"]["title"] == "テスト投稿"


@pytest.mark.asyncio
async def test_create_post_missing_fields(client: AsyncClient):
    response = await client.post("/api/posts", json={
        "title": "",
        "author": "test",
        "content": "content",
        "password": "test1234",
    })
    assert response.status_code == 422  # Pydantic validation


@pytest.mark.asyncio
async def test_list_posts_empty(client: AsyncClient):
    response = await client.get("/api/posts")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["posts"] == []


@pytest.mark.asyncio
async def test_delete_post_wrong_password(client: AsyncClient):
    # Create
    create_resp = await client.post("/api/posts", json={
        "title": "削除テスト",
        "author": "user",
        "content": "内容",
        "password": "correct123",
    })
    post_id = create_resp.json()["post"]["id"]

    # Delete with wrong password
    delete_resp = await client.request(
        "DELETE",
        f"/api/posts/{post_id}",
        json={"password": "wrong"},
    )
    assert delete_resp.status_code == 403
```

### CamelCase Response Testing

Response schemas use CamelModel, so JSON keys are camelCase:

```python
@pytest.mark.asyncio
async def test_response_uses_camel_case(client: AsyncClient):
    response = await client.post("/api/posts", json={...})
    data = response.json()
    # camelCase keys in response
    assert "numericId" in data["post"]
    assert "createdAt" in data["post"]
    assert "commentCount" in data["post"] or "comments" in data["post"]
```

## Test Naming Convention

```
test_{action}_{scenario}[_{expected_outcome}]
```

Examples:
- `test_create_post` — happy path
- `test_create_post_missing_fields` — validation error
- `test_delete_post_wrong_password` — auth failure
- `test_list_posts_with_search_filter` — specific feature

## Running Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=app --cov-report=term-missing

# Specific file
pytest tests/test_posts.py

# Verbose
pytest -v
```
