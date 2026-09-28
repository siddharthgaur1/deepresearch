import hashlib
import hmac
import time

from fastapi import Header, HTTPException

from backend.core.config import get_settings

STREAM_TOKEN_TTL_SECONDS = 60


async def require_api_key(x_api_key: str = Header(...)) -> str:
    """Static API-key auth. Good enough for a self-hosted deployment; swap
    for per-user keys (backend/models/user.py already has the column) once
    multi-tenant auth is actually needed."""
    settings = get_settings()
    if x_api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key


# EventSource can't set request headers, so the SSE endpoint can't use
# require_api_key. Instead of putting the long-lived API key in a URL (where
# it lands in access logs and browser history), the client trades it for a
# short-lived token signed with the API key and scoped to one job id.
def _sign(job_id: str, expires_at: int) -> str:
    key = get_settings().api_key.encode()
    return hmac.new(key, f"{job_id}.{expires_at}".encode(), hashlib.sha256).hexdigest()


def create_stream_token(job_id: str) -> str:
    expires_at = int(time.time()) + STREAM_TOKEN_TTL_SECONDS
    return f"{expires_at}.{_sign(job_id, expires_at)}"


def verify_stream_token(job_id: str, token: str) -> bool:
    expires_at, _, signature = token.partition(".")
    if not expires_at.isdigit() or int(expires_at) < time.time():
        return False
    return hmac.compare_digest(signature, _sign(job_id, int(expires_at)))
