"""Polls RabbitMQ's management API for per-queue message counts.

Runs once, in the backend API process only, so worker_queue_depth is a plain
Gauge with no multiprocess double-counting to worry about -- there's exactly
one writer regardless of how many Celery worker replicas are running.
"""

import asyncio
import logging
from urllib.parse import quote, urlparse

import httpx

from backend.core.metrics import worker_queue_depth
from backend.workers.queues import AGENT_QUEUES, GRAPH_QUEUE

logger = logging.getLogger("deepresearch.queue_depth")

POLL_INTERVAL_SECONDS = 15


async def poll_queue_depth(broker_url: str) -> None:
    parsed = urlparse(broker_url)
    mgmt_url = f"http://{parsed.hostname}:15672"
    auth = (parsed.username or "guest", parsed.password or "guest")
    vhost = quote((parsed.path or "/").lstrip("/") or "/", safe="")

    async with httpx.AsyncClient(auth=auth, timeout=5.0) as client:
        while True:
            for queue in [*AGENT_QUEUES, GRAPH_QUEUE]:
                try:
                    resp = await client.get(f"{mgmt_url}/api/queues/{vhost}/{queue}")
                    resp.raise_for_status()
                    worker_queue_depth.labels(queue=queue).set(resp.json().get("messages", 0))
                except httpx.HTTPError as exc:
                    logger.warning("queue_depth_poll_failed", extra={"queue": queue, "error": str(exc)})
            await asyncio.sleep(POLL_INTERVAL_SECONDS)
