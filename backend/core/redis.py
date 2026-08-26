from functools import lru_cache

from redis.asyncio import Redis, from_url

from backend.core.config import get_settings


@lru_cache
def get_redis() -> Redis:
    settings = get_settings()
    return from_url(settings.redis_url, decode_responses=True)


def job_channel(job_id: str) -> str:
    return f"deepresearch:job:{job_id}:events"


def rate_limit_key(user_key: str) -> str:
    return f"deepresearch:ratelimit:{user_key}"


def dedup_key(job_id: str) -> str:
    return f"deepresearch:job:{job_id}:seen"
