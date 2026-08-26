from fastapi import Header, HTTPException

from backend.core.config import get_settings


async def require_api_key(x_api_key: str = Header(...)) -> str:
    """Static API-key auth. Good enough for a self-hosted deployment; swap
    for per-user keys (backend/models/user.py already has the column) once
    multi-tenant auth is actually needed."""
    settings = get_settings()
    if x_api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key
