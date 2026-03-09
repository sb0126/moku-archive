"""Admin endpoint integration tests.

Covers: login, stats. Image upload/delete are mocked (R2 not available in test).
"""

from unittest.mock import AsyncMock, patch

from httpx import AsyncClient

from app.config import settings

_TEST_ADMIN_PASSWORD = "test-admin-secret-123"


# ── LOGIN ──────────────────────────────────────────────────────


async def test_admin_login_success(client: AsyncClient):
    with patch.object(settings, "moku_admin_password", _TEST_ADMIN_PASSWORD):
        resp = await client.post(
            "/api/admin/login",
            json={"password": _TEST_ADMIN_PASSWORD},
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["authenticated"] is True
    assert "token" in data
    assert len(data["token"]) > 10  # JWT should be reasonably long


async def test_admin_login_wrong_password(client: AsyncClient):
    with patch.object(settings, "moku_admin_password", _TEST_ADMIN_PASSWORD):
        resp = await client.post(
            "/api/admin/login",
            json={"password": "wrong-password"},
        )
    assert resp.status_code == 403


async def test_admin_login_empty_password(client: AsyncClient):
    resp = await client.post(
        "/api/admin/login",
        json={"password": ""},
    )
    assert resp.status_code == 422


# ── STATS ──────────────────────────────────────────────────────


async def test_admin_stats_empty(client: AsyncClient, admin_headers):
    resp = await client.get("/api/admin/stats", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    stats = data["stats"]
    assert stats["total_posts"] == 0
    assert stats["total_comments"] == 0
    assert stats["total_views"] == 0
    assert stats["total_inquiries"] == 0
    assert stats["pending_inquiries"] == 0


async def test_admin_stats_with_data(
    client: AsyncClient,
    admin_headers,
    make_post_payload,
    make_inquiry_payload,
    make_comment_payload,
):
    """Stats reflect actual data counts."""
    # Create 2 posts
    r1 = await client.post("/api/posts", json=make_post_payload())
    r2 = await client.post("/api/posts", json=make_post_payload())
    pid1 = r1.json()["post"]["id"]

    # Increment views on first post
    await client.post(f"/api/posts/{pid1}/view")
    await client.post(f"/api/posts/{pid1}/view")

    # Create a comment
    await client.post(
        f"/api/posts/{pid1}/comments", json=make_comment_payload()
    )

    # Create an inquiry
    await client.post("/api/inquiries", json=make_inquiry_payload())

    resp = await client.get("/api/admin/stats", headers=admin_headers)
    stats = resp.json()["stats"]
    assert stats["total_posts"] == 2
    assert stats["total_views"] == 2
    assert stats["total_comments"] == 1
    assert stats["total_inquiries"] == 1
    assert stats["pending_inquiries"] == 1


async def test_admin_stats_requires_admin(client: AsyncClient):
    resp = await client.get("/api/admin/stats")
    assert resp.status_code in (401, 422)


# ── UPLOAD IMAGE ───────────────────────────────────────────────


@patch("app.services.admin_service.ensure_bucket", new_callable=AsyncMock)
@patch("app.services.admin_service.upload_file", new_callable=AsyncMock)
async def test_upload_image(
    mock_upload: AsyncMock,
    mock_bucket: AsyncMock,
    client: AsyncClient,
    admin_headers,
):
    fake_image = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100  # minimal PNG header
    resp = await client.post(
        "/api/admin/upload-image",
        headers=admin_headers,
        files={"file": ("test.png", fake_image, "image/png")},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["url"].startswith("storage:")
    assert data["path"].startswith("articles/")
    mock_upload.assert_called_once()


@patch("app.services.admin_service.ensure_bucket", new_callable=AsyncMock)
@patch("app.services.admin_service.upload_file", new_callable=AsyncMock)
async def test_upload_image_invalid_type(
    mock_upload: AsyncMock,
    mock_bucket: AsyncMock,
    client: AsyncClient,
    admin_headers,
):
    resp = await client.post(
        "/api/admin/upload-image",
        headers=admin_headers,
        files={"file": ("test.exe", b"\x00" * 100, "application/octet-stream")},
    )
    assert resp.status_code == 400


async def test_upload_image_requires_admin(client: AsyncClient):
    resp = await client.post(
        "/api/admin/upload-image",
        files={"file": ("test.png", b"\x00" * 100, "image/png")},
    )
    assert resp.status_code in (401, 422)


# ── DELETE IMAGE ───────────────────────────────────────────────


@patch("app.services.admin_service.remove_files", new_callable=AsyncMock)
async def test_delete_image(
    mock_remove: AsyncMock,
    client: AsyncClient,
    admin_headers,
):
    resp = await client.post(
        "/api/admin/delete-image",
        headers=admin_headers,
        json={"path": "articles/test-image.png"},
    )
    assert resp.status_code == 200
    assert resp.json()["success"] is True
    mock_remove.assert_called_once_with(["articles/test-image.png"])


async def test_delete_image_requires_admin(client: AsyncClient):
    resp = await client.post(
        "/api/admin/delete-image",
        json={"path": "articles/test.png"},
    )
    assert resp.status_code in (401, 422)
