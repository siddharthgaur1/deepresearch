"""The SSE endpoint can't use the x-api-key header (EventSource can't set
headers), so it takes a short-lived, job-scoped token instead of the raw API
key in the URL -- see create_stream_token in api/routes/auth.py."""

import time

from fastapi.testclient import TestClient

from backend.api.main import app
from backend.api.routes import auth
from backend.core.config import get_settings

JOB = "00000000-0000-0000-0000-000000000001"
OTHER_JOB = "00000000-0000-0000-0000-000000000002"


def test_valid_token_verifies():
    assert auth.verify_stream_token(JOB, auth.create_stream_token(JOB))


def test_expired_token_rejected(monkeypatch):
    token = auth.create_stream_token(JOB)
    later = time.time() + auth.STREAM_TOKEN_TTL_SECONDS + 1
    monkeypatch.setattr(auth.time, "time", lambda: later)
    assert not auth.verify_stream_token(JOB, token)


def test_token_for_other_job_rejected():
    assert not auth.verify_stream_token(OTHER_JOB, auth.create_stream_token(JOB))


def test_tampered_token_rejected():
    expires_at, _, signature = auth.create_stream_token(JOB).partition(".")
    # Extending the expiry invalidates the signature.
    assert not auth.verify_stream_token(JOB, f"{int(expires_at) + 3600}.{signature}")
    assert not auth.verify_stream_token(JOB, f"{expires_at}.{'0' * len(signature)}")
    assert not auth.verify_stream_token(JOB, "garbage")


def test_stream_token_endpoint_requires_api_key():
    client = TestClient(app)
    assert client.post(f"/jobs/{JOB}/stream-token", headers={"x-api-key": "wrong"}).status_code == 401
    resp = client.post(f"/jobs/{JOB}/stream-token", headers={"x-api-key": get_settings().api_key})
    assert resp.status_code == 200
    assert auth.verify_stream_token(JOB, resp.json()["token"])


def test_events_endpoint_rejects_missing_or_bad_token():
    client = TestClient(app)
    assert client.get(f"/jobs/{JOB}/events").status_code == 422
    # The raw API key is not a valid token.
    assert client.get(f"/jobs/{JOB}/events", params={"token": get_settings().api_key}).status_code == 401
    token = auth.create_stream_token(OTHER_JOB)
    assert client.get(f"/jobs/{JOB}/events", params={"token": token}).status_code == 401
