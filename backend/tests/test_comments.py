"""Comment endpoint integration tests.

Covers: create, list, update, delete, password-verify for comments.
"""

from httpx import AsyncClient


# ── helpers ────────────────────────────────────────────────────


async def _create_post(client: AsyncClient, make_post_payload) -> str:
    """Create a post and return its ID."""
    resp = await client.post("/api/posts", json=make_post_payload())
    return resp.json()["post"]["id"]


# ── CREATE ─────────────────────────────────────────────────────


async def test_create_comment(
    client: AsyncClient, make_post_payload, make_comment_payload
):
    post_id = await _create_post(client, make_post_payload)

    resp = await client.post(
        f"/api/posts/{post_id}/comments",
        json=make_comment_payload(),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["success"] is True
    assert data["comment"]["post_id"] == post_id
    assert data["commentCount"] == 1


async def test_create_comment_increments_count(
    client: AsyncClient, make_post_payload, make_comment_payload
):
    post_id = await _create_post(client, make_post_payload)

    await client.post(
        f"/api/posts/{post_id}/comments", json=make_comment_payload()
    )
    await client.post(
        f"/api/posts/{post_id}/comments", json=make_comment_payload()
    )

    # Verify post's comment count
    list_resp = await client.get("/api/posts")
    post = list_resp.json()["posts"][0]
    assert post["comments"] == 2


async def test_create_comment_on_nonexistent_post(
    client: AsyncClient, make_comment_payload
):
    resp = await client.post(
        "/api/posts/nonexistent/comments",
        json=make_comment_payload(),
    )
    assert resp.status_code == 404


async def test_create_comment_missing_fields(client: AsyncClient, make_post_payload):
    post_id = await _create_post(client, make_post_payload)
    resp = await client.post(f"/api/posts/{post_id}/comments", json={})
    assert resp.status_code == 422


async def test_create_comment_spam_rejected(
    client: AsyncClient, make_post_payload, make_comment_payload
):
    post_id = await _create_post(client, make_post_payload)
    spam_content = "http://a.com http://b.com http://c.com http://d.com spam"
    resp = await client.post(
        f"/api/posts/{post_id}/comments",
        json=make_comment_payload(content=spam_content),
    )
    assert resp.status_code == 400


# ── LIST ───────────────────────────────────────────────────────


async def test_list_comments_empty(client: AsyncClient, make_post_payload):
    post_id = await _create_post(client, make_post_payload)
    resp = await client.get(f"/api/posts/{post_id}/comments")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 0
    assert data["comments"] == []


async def test_list_comments(
    client: AsyncClient, make_post_payload, make_comment_payload
):
    post_id = await _create_post(client, make_post_payload)

    for _ in range(3):
        await client.post(
            f"/api/posts/{post_id}/comments", json=make_comment_payload()
        )

    resp = await client.get(f"/api/posts/{post_id}/comments")
    data = resp.json()
    assert data["count"] == 3
    assert len(data["comments"]) == 3


# ── UPDATE ─────────────────────────────────────────────────────


async def test_update_comment(
    client: AsyncClient, make_post_payload, make_comment_payload
):
    post_id = await _create_post(client, make_post_payload)
    create_resp = await client.post(
        f"/api/posts/{post_id}/comments", json=make_comment_payload()
    )
    comment_id = create_resp.json()["comment"]["id"]

    update_resp = await client.put(
        f"/api/comments/{comment_id}",
        json={"content": "更新されたコメント", "password": "test1234"},
    )
    assert update_resp.status_code == 200
    data = update_resp.json()
    assert data["success"] is True
    assert data["comment"]["content"] == "更新されたコメント"


async def test_update_comment_wrong_password(
    client: AsyncClient, make_post_payload, make_comment_payload
):
    post_id = await _create_post(client, make_post_payload)
    create_resp = await client.post(
        f"/api/posts/{post_id}/comments", json=make_comment_payload()
    )
    comment_id = create_resp.json()["comment"]["id"]

    resp = await client.put(
        f"/api/comments/{comment_id}",
        json={"content": "変更", "password": "wrongpass"},
    )
    assert resp.status_code == 403


async def test_update_comment_not_found(client: AsyncClient):
    resp = await client.put(
        "/api/comments/nonexistent",
        json={"content": "変更", "password": "test1234"},
    )
    assert resp.status_code == 404


# ── DELETE ─────────────────────────────────────────────────────


async def test_delete_comment_with_password(
    client: AsyncClient, make_post_payload, make_comment_payload
):
    post_id = await _create_post(client, make_post_payload)
    create_resp = await client.post(
        f"/api/posts/{post_id}/comments", json=make_comment_payload()
    )
    comment_id = create_resp.json()["comment"]["id"]

    delete_resp = await client.request(
        "DELETE",
        f"/api/comments/{comment_id}",
        json={"password": "test1234"},
    )
    assert delete_resp.status_code == 200
    assert delete_resp.json()["success"] is True


async def test_delete_comment_decrements_post_count(
    client: AsyncClient, make_post_payload, make_comment_payload
):
    post_id = await _create_post(client, make_post_payload)
    create_resp = await client.post(
        f"/api/posts/{post_id}/comments", json=make_comment_payload()
    )
    comment_id = create_resp.json()["comment"]["id"]

    # Delete the comment
    await client.request(
        "DELETE",
        f"/api/comments/{comment_id}",
        json={"password": "test1234"},
    )

    # Post comment count should be 0
    list_resp = await client.get("/api/posts")
    post = list_resp.json()["posts"][0]
    assert post["comments"] == 0


async def test_delete_comment_admin_bypass(
    client: AsyncClient, make_post_payload, make_comment_payload, admin_headers
):
    post_id = await _create_post(client, make_post_payload)
    create_resp = await client.post(
        f"/api/posts/{post_id}/comments", json=make_comment_payload()
    )
    comment_id = create_resp.json()["comment"]["id"]

    resp = await client.request(
        "DELETE",
        f"/api/comments/{comment_id}",
        headers=admin_headers,
        json={},
    )
    assert resp.status_code == 200


async def test_delete_comment_wrong_password(
    client: AsyncClient, make_post_payload, make_comment_payload
):
    post_id = await _create_post(client, make_post_payload)
    create_resp = await client.post(
        f"/api/posts/{post_id}/comments", json=make_comment_payload()
    )
    comment_id = create_resp.json()["comment"]["id"]

    resp = await client.request(
        "DELETE",
        f"/api/comments/{comment_id}",
        json={"password": "wrongpass"},
    )
    assert resp.status_code == 403


# ── VERIFY PASSWORD ────────────────────────────────────────────


async def test_verify_comment_password_correct(
    client: AsyncClient, make_post_payload, make_comment_payload
):
    post_id = await _create_post(client, make_post_payload)
    create_resp = await client.post(
        f"/api/posts/{post_id}/comments", json=make_comment_payload()
    )
    comment_id = create_resp.json()["comment"]["id"]

    resp = await client.post(
        f"/api/comments/{comment_id}/verify-password",
        json={"password": "test1234"},
    )
    assert resp.status_code == 200
    assert resp.json()["verified"] is True


async def test_verify_comment_password_incorrect(
    client: AsyncClient, make_post_payload, make_comment_payload
):
    post_id = await _create_post(client, make_post_payload)
    create_resp = await client.post(
        f"/api/posts/{post_id}/comments", json=make_comment_payload()
    )
    comment_id = create_resp.json()["comment"]["id"]

    resp = await client.post(
        f"/api/comments/{comment_id}/verify-password",
        json={"password": "wrongpass"},
    )
    assert resp.status_code == 200
    assert resp.json()["verified"] is False
