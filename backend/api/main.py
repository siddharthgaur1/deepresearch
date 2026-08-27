import logging

from fastapi import FastAPI
from prometheus_client import CONTENT_TYPE_LATEST, CollectorRegistry, generate_latest, multiprocess
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import Response

from backend.api.routes import jobs, reports
from backend.core.config import get_settings
from backend.services.queue_depth import poll_queue_depth

logging.basicConfig(level=logging.INFO)

settings = get_settings()
_is_dev = settings.environment == "development"
app = FastAPI(
    title=settings.app_name,
    # Swagger/ReDoc/the raw OpenAPI schema expose every endpoint's request
    # and response shape with no auth of their own (they're FastAPI's own
    # routes, not under jobs.router's require_api_key dependency) -- fine
    # for local dev, real disclosure surface anywhere else.
    docs_url="/docs" if _is_dev else None,
    redoc_url="/redoc" if _is_dev else None,
    openapi_url="/openapi.json" if _is_dev else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if _is_dev else [],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(jobs.router)
app.include_router(reports.router)


@app.on_event("startup")
async def _start_queue_depth_poller() -> None:
    if settings.celery_broker_url.startswith("amqp://"):
        import asyncio

        asyncio.create_task(poll_queue_depth(settings.celery_broker_url))


@app.get("/healthz")
async def healthz() -> dict:
    return {"status": "ok"}


@app.get("/metrics")
async def metrics() -> Response:
    # Agents run inside separate Celery worker processes, so agent/token/cost
    # metrics live in per-process mmap files rather than this process's
    # default registry once PROMETHEUS_MULTIPROC_DIR is set — the collector
    # below is what merges them back into one scrape.
    if settings.prometheus_multiproc_dir:
        registry = CollectorRegistry()
        multiprocess.MultiProcessCollector(registry)
        return Response(generate_latest(registry), media_type=CONTENT_TYPE_LATEST)
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
