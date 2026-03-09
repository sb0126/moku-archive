"""Inquiry endpoint integration tests.

Covers: create (public), list (admin), update-status (admin), delete (admin).
"""

from httpx import AsyncClient


# ── CREATE (public) ────────────────────────────────────────────


async def test_create_inquiry(client: AsyncClient, make_inquiry_payload):
    payload = make_inquiry_payload()
    resp = await client.post("/api/inquiries", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["success"] is True
    assert data["inquiry"]["name"] == payload["name"]
    assert data["inquiry"]["email"] == payload["email"]
    assert data["inquiry"]["status"] == "pending"
    assert data["inquiry"]["admin_note"] is None


async def test_create_inquiry_validation_errors(client: AsyncClient):
    resp = await client.post("/api/inquiries", json={})
    assert resp.status_code == 422


async def test_create_inquiry_invalid_phone(client: AsyncClient, make_inquiry_payload):
    resp = await client.post(
        "/api/inquiries",
        json=make_inquiry_payload(phone="1234567890"),  # invalid Japanese phone
    )
    assert resp.status_code == 422


async def test_create_inquiry_invalid_email(client: AsyncClient, make_inquiry_payload):
    resp = await client.post(
        "/api/inquiries",
        json=make_inquiry_payload(email="not-an-email"),
    )
    assert resp.status_code == 422


async def test_create_inquiry_age_out_of_range(
    client: AsyncClient, make_inquiry_payload
):
    resp = await client.post(
        "/api/inquiries",
        json=make_inquiry_payload(age=15),  # minimum is 18
    )
    assert resp.status_code == 422


async def test_create_inquiry_spam_rejected(
    client: AsyncClient, make_inquiry_payload
):
    spam_msg = "http://a.com http://b.com http://c.com http://d.com spam links"
    resp = await client.post(
        "/api/inquiries",
        json=make_inquiry_payload(message=spam_msg),
    )
    assert resp.status_code == 400


# ── LIST (admin only) ─────────────────────────────────────────


async def test_list_inquiries_admin(
    client: AsyncClient, make_inquiry_payload, admin_headers
):
    await client.post("/api/inquiries", json=make_inquiry_payload())
    await client.post("/api/inquiries", json=make_inquiry_payload())

    resp = await client.get("/api/inquiries", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 2
    assert len(data["inquiries"]) == 2


async def test_list_inquiries_requires_admin(client: AsyncClient):
    resp = await client.get("/api/inquiries")
    assert resp.status_code in (401, 422)


# ── UPDATE STATUS (admin only) ────────────────────────────────


async def test_update_inquiry_status(
    client: AsyncClient, make_inquiry_payload, admin_headers
):
    create_resp = await client.post(
        "/api/inquiries", json=make_inquiry_payload()
    )
    inquiry_id = create_resp.json()["inquiry"]["id"]

    update_resp = await client.put(
        f"/api/inquiries/{inquiry_id}/status",
        headers=admin_headers,
        json={"status": "contacted", "admin_note": "電話連絡済み"},
    )
    assert update_resp.status_code == 200
    data = update_resp.json()
    assert data["inquiry"]["status"] == "contacted"
    assert data["inquiry"]["admin_note"] == "電話連絡済み"


async def test_update_inquiry_status_invalid(
    client: AsyncClient, make_inquiry_payload, admin_headers
):
    create_resp = await client.post(
        "/api/inquiries", json=make_inquiry_payload()
    )
    inquiry_id = create_resp.json()["inquiry"]["id"]

    resp = await client.put(
        f"/api/inquiries/{inquiry_id}/status",
        headers=admin_headers,
        json={"status": "invalid_status"},
    )
    assert resp.status_code == 422


async def test_update_inquiry_status_not_found(
    client: AsyncClient, admin_headers
):
    resp = await client.put(
        "/api/inquiries/nonexistent/status",
        headers=admin_headers,
        json={"status": "contacted"},
    )
    assert resp.status_code == 404


async def test_update_inquiry_status_requires_admin(
    client: AsyncClient, make_inquiry_payload
):
    create_resp = await client.post(
        "/api/inquiries", json=make_inquiry_payload()
    )
    inquiry_id = create_resp.json()["inquiry"]["id"]

    resp = await client.put(
        f"/api/inquiries/{inquiry_id}/status",
        json={"status": "contacted"},
    )
    assert resp.status_code in (401, 422)


# ── DELETE (admin only) ───────────────────────────────────────


async def test_delete_inquiry(
    client: AsyncClient, make_inquiry_payload, admin_headers
):
    create_resp = await client.post(
        "/api/inquiries", json=make_inquiry_payload()
    )
    inquiry_id = create_resp.json()["inquiry"]["id"]

    delete_resp = await client.delete(
        f"/api/inquiries/{inquiry_id}", headers=admin_headers
    )
    assert delete_resp.status_code == 200
    assert delete_resp.json()["success"] is True

    # Verify gone
    list_resp = await client.get("/api/inquiries", headers=admin_headers)
    assert list_resp.json()["count"] == 0


async def test_delete_inquiry_not_found(client: AsyncClient, admin_headers):
    resp = await client.delete(
        "/api/inquiries/nonexistent", headers=admin_headers
    )
    assert resp.status_code == 404


async def test_delete_inquiry_requires_admin(
    client: AsyncClient, make_inquiry_payload
):
    create_resp = await client.post(
        "/api/inquiries", json=make_inquiry_payload()
    )
    inquiry_id = create_resp.json()["inquiry"]["id"]

    resp = await client.delete(f"/api/inquiries/{inquiry_id}")
    assert resp.status_code in (401, 422)
