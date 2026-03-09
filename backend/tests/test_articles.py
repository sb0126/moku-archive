"""Article endpoint integration tests.

Covers: list (public), get (public), create (admin), update (admin),
        delete (admin — storage mock).

Article service depends on `storage.resolve_storage_url` and `storage.remove_files`
which are mocked here since R2 is unavailable in test.
"""

from unittest.mock import AsyncMock, patch

from httpx import AsyncClient


# ── LIST (public) ──────────────────────────────────────────────


async def test_list_articles_empty(client: AsyncClient):
    resp = await client.get("/api/articles")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 0
    assert data["articles"] == []


async def test_list_articles(
    client: AsyncClient, make_article_payload, admin_headers
):
    await client.post(
        "/api/articles", json=make_article_payload(), headers=admin_headers
    )
    await client.post(
        "/api/articles", json=make_article_payload(), headers=admin_headers
    )

    resp = await client.get("/api/articles")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 2
    assert len(data["articles"]) == 2


# ── GET (public) ───────────────────────────────────────────────


async def test_get_article(
    client: AsyncClient, make_article_payload, admin_headers
):
    payload = make_article_payload()
    await client.post("/api/articles", json=payload, headers=admin_headers)

    resp = await client.get(f"/api/articles/{payload['id']}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == payload["id"]
    assert data["ja"]["title"] == payload["ja"]["title"]


async def test_get_article_not_found(client: AsyncClient):
    resp = await client.get("/api/articles/nonexistent")
    assert resp.status_code == 404


# ── CREATE (admin) ─────────────────────────────────────────────


async def test_create_article(
    client: AsyncClient, make_article_payload, admin_headers
):
    payload = make_article_payload()
    resp = await client.post(
        "/api/articles", json=payload, headers=admin_headers
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["success"] is True
    assert data["article"]["id"] == payload["id"]
    assert data["article"]["ja"]["title"] == payload["ja"]["title"]


async def test_create_article_with_ko(
    client: AsyncClient, make_article_payload, admin_headers
):
    payload = make_article_payload(
        ko={
            "title": "테스트 기사",
            "category": "생활",
            "excerpt": "테스트 요약",
            "content": "기사 본문입니다",
            "imageAlt": "테스트 이미지",
            "author": "테스트 저자",
            "readTime": "5분",
            "tags": ["테스트"],
        }
    )
    resp = await client.post(
        "/api/articles", json=payload, headers=admin_headers
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["article"]["ko"] is not None
    assert data["article"]["ko"]["title"] == "테스트 기사"


async def test_create_article_duplicate_slug(
    client: AsyncClient, make_article_payload, admin_headers
):
    payload = make_article_payload()
    await client.post("/api/articles", json=payload, headers=admin_headers)

    # Same ID again → 409
    resp = await client.post(
        "/api/articles", json=payload, headers=admin_headers
    )
    assert resp.status_code == 409


async def test_create_article_requires_admin(
    client: AsyncClient, make_article_payload
):
    resp = await client.post("/api/articles", json=make_article_payload())
    assert resp.status_code in (401, 422)


async def test_create_article_invalid_slug(
    client: AsyncClient, make_article_payload, admin_headers
):
    resp = await client.post(
        "/api/articles",
        json=make_article_payload(id="INVALID SLUG!"),
        headers=admin_headers,
    )
    assert resp.status_code == 422


# ── UPDATE (admin) ─────────────────────────────────────────────


async def test_update_article(
    client: AsyncClient, make_article_payload, admin_headers
):
    payload = make_article_payload()
    await client.post("/api/articles", json=payload, headers=admin_headers)

    update_resp = await client.put(
        f"/api/articles/{payload['id']}",
        headers=admin_headers,
        json={
            "ja": {
                "title": "更新タイトル",
                "category": "生活",
            },
        },
    )
    assert update_resp.status_code == 200
    data = update_resp.json()
    assert data["article"]["ja"]["title"] == "更新タイトル"


async def test_update_article_not_found(client: AsyncClient, admin_headers):
    resp = await client.put(
        "/api/articles/nonexistent",
        headers=admin_headers,
        json={"ja": {"title": "変更", "category": "生活"}},
    )
    assert resp.status_code == 404


async def test_update_article_requires_admin(
    client: AsyncClient, make_article_payload
):
    resp = await client.put(
        "/api/articles/test-article-1",
        json={"ja": {"title": "変更", "category": "生活"}},
    )
    assert resp.status_code in (401, 422)


# ── DELETE (admin) ─────────────────────────────────────────────


@patch(
    "app.services.article_service.remove_files",
    new_callable=AsyncMock,
)
async def test_delete_article(
    mock_remove: AsyncMock,
    client: AsyncClient,
    make_article_payload,
    admin_headers,
):
    payload = make_article_payload()
    await client.post("/api/articles", json=payload, headers=admin_headers)

    resp = await client.delete(
        f"/api/articles/{payload['id']}", headers=admin_headers
    )
    assert resp.status_code == 200
    assert resp.json()["success"] is True

    # Verify gone
    get_resp = await client.get(f"/api/articles/{payload['id']}")
    assert get_resp.status_code == 404


@patch(
    "app.services.article_service.remove_files",
    new_callable=AsyncMock,
)
async def test_delete_article_with_storage_image(
    mock_remove: AsyncMock,
    client: AsyncClient,
    make_article_payload,
    admin_headers,
):
    """Deleting an article with 'storage:' prefix triggers storage cleanup."""
    payload = make_article_payload(imageUrl="storage:articles/test.jpg")
    await client.post("/api/articles", json=payload, headers=admin_headers)

    await client.delete(
        f"/api/articles/{payload['id']}", headers=admin_headers
    )

    mock_remove.assert_called_once_with(["articles/test.jpg"])


async def test_delete_article_not_found(client: AsyncClient, admin_headers):
    resp = await client.delete(
        "/api/articles/nonexistent", headers=admin_headers
    )
    assert resp.status_code == 404


async def test_delete_article_requires_admin(
    client: AsyncClient, make_article_payload
):
    resp = await client.delete("/api/articles/test-article-1")
    assert resp.status_code in (401, 422)
