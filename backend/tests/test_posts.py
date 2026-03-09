"""Post endpoint integration tests.

Covers: create, list, update, delete, view-increment, like-toggle,
        like-status, bulk-likes, password-verify, pin-toggle.
"""

from httpx import AsyncClient


# ── CREATE ─────────────────────────────────────────────────────


async def test_create_post(client: AsyncClient, make_post_payload):
    payload = make_post_payload()
    resp = await client.post("/api/posts", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["success"] is True
    assert data["post"]["title"] == payload["title"]
    assert data["post"]["author"] == payload["author"]
    assert data["post"]["category"] == "chat"
    assert data["post"]["views"] == 0
    assert data["post"]["comments"] == 0
    assert data["post"]["pinned"] is False


async def test_create_post_missing_fields(client: AsyncClient):
    resp = await client.post("/api/posts", json={})
    assert resp.status_code == 422


async def test_create_post_empty_title(client: AsyncClient, make_post_payload):
    resp = await client.post(
        "/api/posts", json=make_post_payload(title="")
    )
    assert resp.status_code == 422


async def test_create_post_short_password(client: AsyncClient, make_post_payload):
    resp = await client.post(
        "/api/posts", json=make_post_payload(password="ab")
    )
    assert resp.status_code == 422


async def test_create_post_spam_rejected(client: AsyncClient, make_post_payload):
    """Posts with excessive URLs are flagged as spam."""
    spam_content = "Check out http://a.com http://b.com http://c.com http://d.com"
    resp = await client.post(
        "/api/posts", json=make_post_payload(content=spam_content)
    )
    assert resp.status_code == 400


async def test_create_post_xss_sanitized(client: AsyncClient, make_post_payload):
    """XSS script tags are stripped from content."""
    resp = await client.post(
        "/api/posts",
        json=make_post_payload(
            title='<script>alert("xss")</script>安全なタイトル',
            content="普通の内容",
        ),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert "<script>" not in data["post"]["title"]
    assert "安全なタイトル" in data["post"]["title"]


# ── LIST ───────────────────────────────────────────────────────


async def test_list_posts_empty(client: AsyncClient):
    resp = await client.get("/api/posts")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 0
    assert data["posts"] == []
    assert data["total_pages"] == 1
    assert data["current_page"] == 1


async def test_list_posts_returns_created_posts(client: AsyncClient, make_post_payload):
    # Create 3 posts
    for _ in range(3):
        await client.post("/api/posts", json=make_post_payload())

    resp = await client.get("/api/posts")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 3
    assert data["count"] == 3
    assert len(data["posts"]) == 3


async def test_list_posts_pagination(client: AsyncClient, make_post_payload):
    for _ in range(5):
        await client.post("/api/posts", json=make_post_payload())

    resp = await client.get("/api/posts", params={"page": 1, "limit": 2})
    data = resp.json()
    assert data["count"] == 2
    assert data["total"] == 5
    assert data["total_pages"] == 3
    assert data["current_page"] == 1


async def test_list_posts_search_by_title(client: AsyncClient, make_post_payload):
    await client.post("/api/posts", json=make_post_payload(title="ビザ申請ガイド"))
    await client.post("/api/posts", json=make_post_payload(title="別の投稿"))

    resp = await client.get(
        "/api/posts", params={"search": "ビザ", "searchType": "title"}
    )
    data = resp.json()
    assert data["total"] == 1
    assert "ビザ" in data["posts"][0]["title"]


async def test_list_posts_filter_by_category(client: AsyncClient, make_post_payload):
    await client.post("/api/posts", json=make_post_payload(category="question"))
    await client.post("/api/posts", json=make_post_payload(category="chat"))

    resp = await client.get("/api/posts", params={"category": "question"})
    data = resp.json()
    assert data["total"] == 1
    assert data["posts"][0]["category"] == "question"


async def test_list_posts_sort_oldest(client: AsyncClient, make_post_payload):
    """Oldest sort returns posts in ascending creation order."""
    for i in range(3):
        await client.post("/api/posts", json=make_post_payload(title=f"Post {i}"))

    resp = await client.get("/api/posts", params={"sort": "oldest"})
    data = resp.json()
    dates = [p["created_at"] for p in data["posts"]]
    assert dates == sorted(dates)


# ── UPDATE ─────────────────────────────────────────────────────


async def test_update_post(client: AsyncClient, make_post_payload):
    create_resp = await client.post("/api/posts", json=make_post_payload())
    post_id = create_resp.json()["post"]["id"]

    update_resp = await client.put(
        f"/api/posts/{post_id}",
        json={"title": "更新されたタイトル", "password": "test1234"},
    )
    assert update_resp.status_code == 200
    data = update_resp.json()
    assert data["success"] is True
    assert data["post"]["title"] == "更新されたタイトル"


async def test_update_post_wrong_password(client: AsyncClient, make_post_payload):
    create_resp = await client.post("/api/posts", json=make_post_payload())
    post_id = create_resp.json()["post"]["id"]

    update_resp = await client.put(
        f"/api/posts/{post_id}",
        json={"title": "変更", "password": "wrongpass"},
    )
    assert update_resp.status_code == 403


async def test_update_post_not_found(client: AsyncClient):
    resp = await client.put(
        "/api/posts/nonexistent",
        json={"title": "変更", "password": "test1234"},
    )
    assert resp.status_code == 404


# ── DELETE ─────────────────────────────────────────────────────


async def test_delete_post_with_password(client: AsyncClient, make_post_payload):
    create_resp = await client.post("/api/posts", json=make_post_payload())
    post_id = create_resp.json()["post"]["id"]

    delete_resp = await client.request(
        "DELETE",
        f"/api/posts/{post_id}",
        json={"password": "test1234"},
    )
    assert delete_resp.status_code == 200
    assert delete_resp.json()["success"] is True

    # Verify it's gone
    list_resp = await client.get("/api/posts")
    assert list_resp.json()["total"] == 0


async def test_delete_post_wrong_password(client: AsyncClient, make_post_payload):
    create_resp = await client.post("/api/posts", json=make_post_payload())
    post_id = create_resp.json()["post"]["id"]

    delete_resp = await client.request(
        "DELETE",
        f"/api/posts/{post_id}",
        json={"password": "wrongpass"},
    )
    assert delete_resp.status_code == 403


async def test_delete_post_admin_bypass(
    client: AsyncClient, make_post_payload, admin_headers
):
    """Admin can delete any post without knowing the password."""
    create_resp = await client.post("/api/posts", json=make_post_payload())
    post_id = create_resp.json()["post"]["id"]

    delete_resp = await client.request(
        "DELETE",
        f"/api/posts/{post_id}",
        headers=admin_headers,
        json={},
    )
    assert delete_resp.status_code == 200


async def test_delete_post_not_found(client: AsyncClient):
    resp = await client.request(
        "DELETE",
        "/api/posts/nonexistent",
        json={"password": "test1234"},
    )
    assert resp.status_code == 404


# ── VIEW INCREMENT ─────────────────────────────────────────────


async def test_increment_view(client: AsyncClient, make_post_payload):
    create_resp = await client.post("/api/posts", json=make_post_payload())
    post_id = create_resp.json()["post"]["id"]

    view_resp = await client.post(f"/api/posts/{post_id}/view")
    assert view_resp.status_code == 200
    assert view_resp.json()["views"] == 1

    # Increment again
    view_resp2 = await client.post(f"/api/posts/{post_id}/view")
    assert view_resp2.json()["views"] == 2


# ── LIKE ───────────────────────────────────────────────────────


async def test_toggle_like(client: AsyncClient, make_post_payload):
    create_resp = await client.post("/api/posts", json=make_post_payload())
    post_id = create_resp.json()["post"]["id"]
    visitor_id = "test-visitor-12345678"

    # Like
    like_resp = await client.post(
        f"/api/posts/{post_id}/like",
        json={"visitorId": visitor_id},
    )
    assert like_resp.status_code == 200
    data = like_resp.json()
    assert data["liked"] is True
    assert data["likes"] == 1

    # Unlike (toggle)
    unlike_resp = await client.post(
        f"/api/posts/{post_id}/like",
        json={"visitorId": visitor_id},
    )
    assert unlike_resp.json()["liked"] is False
    assert unlike_resp.json()["likes"] == 0


async def test_get_like_status(client: AsyncClient, make_post_payload):
    create_resp = await client.post("/api/posts", json=make_post_payload())
    post_id = create_resp.json()["post"]["id"]
    visitor_id = "status-check-12345678"

    # Before liking
    status_resp = await client.get(
        f"/api/posts/{post_id}/likes", params={"visitorId": visitor_id}
    )
    assert status_resp.json()["liked"] is False
    assert status_resp.json()["likes"] == 0

    # After liking
    await client.post(
        f"/api/posts/{post_id}/like",
        json={"visitorId": visitor_id},
    )
    status_resp2 = await client.get(
        f"/api/posts/{post_id}/likes", params={"visitorId": visitor_id}
    )
    assert status_resp2.json()["liked"] is True
    assert status_resp2.json()["likes"] == 1


async def test_bulk_like_counts(client: AsyncClient, make_post_payload):
    # Create 2 posts, like the first one
    r1 = await client.post("/api/posts", json=make_post_payload())
    r2 = await client.post("/api/posts", json=make_post_payload())
    pid1 = r1.json()["post"]["id"]
    pid2 = r2.json()["post"]["id"]

    await client.post(
        f"/api/posts/{pid1}/like", json={"visitorId": "bulk-test-12345678"}
    )

    resp = await client.post(
        "/api/posts/likes/bulk", json={"postIds": [pid1, pid2]}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["likes"][pid1] == 1
    assert data["likes"][pid2] == 0


async def test_bulk_like_counts_empty(client: AsyncClient):
    resp = await client.post("/api/posts/likes/bulk", json={"postIds": []})
    assert resp.status_code == 200
    assert resp.json()["likes"] == {}


# ── VERIFY PASSWORD ────────────────────────────────────────────


async def test_verify_post_password_correct(client: AsyncClient, make_post_payload):
    create_resp = await client.post("/api/posts", json=make_post_payload())
    post_id = create_resp.json()["post"]["id"]

    resp = await client.post(
        f"/api/posts/{post_id}/verify-password",
        json={"password": "test1234"},
    )
    assert resp.status_code == 200
    assert resp.json()["verified"] is True


async def test_verify_post_password_incorrect(client: AsyncClient, make_post_payload):
    create_resp = await client.post("/api/posts", json=make_post_payload())
    post_id = create_resp.json()["post"]["id"]

    resp = await client.post(
        f"/api/posts/{post_id}/verify-password",
        json={"password": "wrongpass"},
    )
    assert resp.status_code == 200
    assert resp.json()["verified"] is False


# ── PIN TOGGLE (admin) ────────────────────────────────────────


async def test_toggle_pin(client: AsyncClient, make_post_payload, admin_headers):
    create_resp = await client.post("/api/posts", json=make_post_payload())
    post_id = create_resp.json()["post"]["id"]

    # Pin
    pin_resp = await client.post(
        f"/api/posts/{post_id}/pin", headers=admin_headers
    )
    assert pin_resp.status_code == 200
    assert pin_resp.json()["post"]["pinned"] is True

    # Unpin
    unpin_resp = await client.post(
        f"/api/posts/{post_id}/pin", headers=admin_headers
    )
    assert unpin_resp.json()["post"]["pinned"] is False


async def test_toggle_pin_requires_admin(client: AsyncClient, make_post_payload):
    create_resp = await client.post("/api/posts", json=make_post_payload())
    post_id = create_resp.json()["post"]["id"]

    resp = await client.post(f"/api/posts/{post_id}/pin")
    # Missing admin header → 422 (validation) or 401
    assert resp.status_code in (401, 422)
