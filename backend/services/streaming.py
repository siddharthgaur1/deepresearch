"""SSE endpoint support: subscribes to the job's Redis pub/sub channel and
re-yields each message as an SSE frame. WebSocket isn't used here since SSE
is simpler for a one-directional server->client feed and needs no extra
frontend library beyond EventSource."""

from collections.abc import AsyncIterator

from backend.core.redis import get_redis, job_channel


async def stream_job_events(job_id: str) -> AsyncIterator[str]:
    redis = get_redis()
    pubsub = redis.pubsub()
    await pubsub.subscribe(job_channel(job_id))
    try:
        async for message in pubsub.listen():
            if message["type"] != "message":
                continue
            yield f"data: {message['data']}\n\n"
    finally:
        await pubsub.unsubscribe(job_channel(job_id))
        await pubsub.close()
