"""Health & readiness probe tests."""

from httpx import AsyncClient


async def test_health_returns_ok(client: AsyncClient):
    resp = await client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"


async def test_config_returns_ga_id(client: AsyncClient):
    resp = await client.get("/api/config")
    assert resp.status_code == 200
    data = resp.json()
    assert "gaMeasurementId" in data
    assert "verification" in data
