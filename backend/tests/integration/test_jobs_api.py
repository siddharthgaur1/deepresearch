"""Integration test against a live stack (Postgres + Redis + RabbitMQ via
docker compose). Skipped by default in CI's unit-test job; run with
`pytest backend/tests/integration -m integration` once `docker compose up -d`
has the dependencies ready.
"""

import pytest
from httpx import ASGITransport, AsyncClient

from backend.api.main import app
from backend.core.config import get_settings

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_submit_job_returns_job_id():
    settings = get_settings()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/jobs",
            json={"query": "What are the health effects of intermittent fasting?"},
            headers={"x-api-key": settings.api_key},
        )
    assert resp.status_code == 202
    body = resp.json()
    assert body["status"] == "queued"
    assert "job_id" in body


@pytest.mark.asyncio
async def test_submit_job_rejects_bad_api_key():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/jobs", json={"query": "test"}, headers={"x-api-key": "wrong"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_job_events_authenticates_via_query_param_not_header():
    """EventSource (the browser's SSE client) can't set request headers, so
    /events must accept the key as a query param — regression test for the
    422 that made the live agent-activity feed silently never populate."""
    settings = get_settings()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        create = await client.post(
            "/jobs", json={"query": "test"}, headers={"x-api-key": settings.api_key}
        )
        job_id = create.json()["job_id"]

        rejected = await client.get(f"/jobs/{job_id}/events")
        assert rejected.status_code == 422

        async with client.stream(
            "GET", f"/jobs/{job_id}/events", params={"api_key": settings.api_key}
        ) as resp:
            assert resp.status_code == 200
