import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.metrics import jobs_total
from backend.models.job import Job
from backend.workers.tasks import run_research_job


async def create_job(db: AsyncSession, query: str) -> Job:
    job = Job(query=query, status="queued")
    db.add(job)
    await db.commit()
    await db.refresh(job)

    jobs_total.inc()
    run_research_job.delay(str(job.id), query)
    return job


async def get_job(db: AsyncSession, job_id: uuid.UUID) -> Job | None:
    result = await db.execute(select(Job).where(Job.id == job_id))
    return result.scalar_one_or_none()


async def cancel_job(db: AsyncSession, job_id: uuid.UUID) -> Job | None:
    """Marks the job cancelled in the DB. Does not force-kill the Celery task;
    the worker still finishes its current node, but job_service/report_service
    won't surface results for a cancelled job once it completes.
    ponytail: no mid-run preemption, add a state check in tasks.py between
    node executions if jobs need to stop immediately rather than at the next
    checkpoint."""
    job = await get_job(db, job_id)
    if job is None:
        return None
    job.status = "cancelled"
    await db.commit()
    await db.refresh(job)
    return job
