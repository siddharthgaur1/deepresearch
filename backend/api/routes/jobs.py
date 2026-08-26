import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import StreamingResponse

from backend.api.routes.auth import require_api_key
from backend.core.database import get_db
from backend.core.redis import get_redis, rate_limit_key
from backend.core.config import get_settings
from backend.schemas.job import JobCreateRequest, JobCreateResponse, JobStatusResponse
from backend.services import job_service
from backend.services.streaming import stream_job_events

router = APIRouter(prefix="/jobs", tags=["jobs"], dependencies=[Depends(require_api_key)])


@router.post("", response_model=JobCreateResponse, status_code=202)
async def submit_job(
    payload: JobCreateRequest,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(require_api_key),
) -> JobCreateResponse:
    await _enforce_rate_limit(api_key)
    job = await job_service.create_job(db, payload.query)
    return JobCreateResponse(job_id=job.id, status=job.status)


@router.get("/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> JobStatusResponse:
    job = await job_service.get_job(db, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobStatusResponse(
        job_id=job.id,
        query=job.query,
        status=job.status,
        error=job.error,
        total_cost_usd=job.total_cost_usd,
        total_tokens=job.total_tokens,
        created_at=job.created_at,
        updated_at=job.updated_at,
    )


@router.post("/{job_id}/cancel", response_model=JobStatusResponse)
async def cancel_job(job_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> JobStatusResponse:
    job = await job_service.cancel_job(db, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobStatusResponse(
        job_id=job.id,
        query=job.query,
        status=job.status,
        error=job.error,
        total_cost_usd=job.total_cost_usd,
        total_tokens=job.total_tokens,
        created_at=job.created_at,
        updated_at=job.updated_at,
    )


@router.get("/{job_id}/events")
async def job_events(job_id: uuid.UUID) -> StreamingResponse:
    return StreamingResponse(stream_job_events(str(job_id)), media_type="text/event-stream")


async def _enforce_rate_limit(api_key: str) -> None:
    settings = get_settings()
    redis = get_redis()
    key = rate_limit_key(api_key)
    count = await redis.incr(key)
    if count == 1:
        await redis.expire(key, 60)
    if count > settings.rate_limit_per_minute:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
