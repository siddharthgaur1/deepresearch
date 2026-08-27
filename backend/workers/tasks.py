"""Celery entry point for running a research job.

The LangGraph StateGraph itself drives all nine agents in-process as async
node calls (that's what LangGraph is for); this task is what makes the
*job* distributable across N worker processes/machines via RabbitMQ. Per-run
concurrency comes from LangGraph's own Send() fan-out (async, within one
task), not from further splitting individual agent calls into their own
Celery tasks — that would mean round-tripping the whole ResearchState
through the broker per node call, which the checkpointer already gives us a
cheaper way to get resumability for. The nine per-agent queues in queues.py
are reserved for that finer-grained split if a given agent (e.g. browser,
which is I/O-heavy) ever needs to scale independently of the rest.
"""

import asyncio
import json
import logging
import time
import uuid

from sqlalchemy import select

from backend.core.database import async_session_factory
from backend.core.metrics import job_duration_seconds, jobs_active
from backend.core.redis import get_redis, job_channel
from backend.graph.checkpointer import get_checkpointer
from backend.graph.graph import build_graph
from backend.graph.state import ResearchStatus
from backend.models.job import Job
from backend.models.report import Report
from backend.workers.celery_app import celery_app

logger = logging.getLogger("deepresearch.workers")


@celery_app.task(name="deepresearch.run_research_job", bind=True, max_retries=0)
def run_research_job(self, job_id: str, query: str) -> str:
    return asyncio.run(_run_research_job_async(job_id, query))


async def _run_research_job_async(job_id: str, query: str) -> str:
    redis = get_redis()
    channel = job_channel(job_id)

    async def publish(event: str, message: str) -> None:
        await redis.publish(channel, json.dumps({"event": event, "message": message}))

    initial_state = {
        "job_id": job_id,
        "query": query,
        "sub_questions": [],
        "search_results": {},
        "summaries": {},
        "claims": [],
        "verified_claims": [],
        "gaps": [],
        "code_outputs": [],
        "report_sections": {},
        "citations": [],
        "final_report": None,
        "status": ResearchStatus.PLANNING,
        "error": None,
        "metadata": {"total_cost_usd": 0.0, "total_tokens": 0, "agent_calls": []},
        "retry_depth": 0,
    }

    await publish("status_changed", "planning")
    await _persist_status(job_id, ResearchStatus.PLANNING)

    jobs_active.inc()
    started_at = time.monotonic()
    try:
        async with get_checkpointer() as checkpointer:
            graph = build_graph(checkpointer=checkpointer)
            config = {"configurable": {"thread_id": job_id}}
            try:
                final_state = await graph.ainvoke(initial_state, config=config)
            except Exception as exc:
                logger.exception("job_failed", extra={"job_id": job_id})
                await publish("error", str(exc))
                await _persist_failure(job_id, str(exc))
                raise
    finally:
        jobs_active.dec()
        job_duration_seconds.observe(time.monotonic() - started_at)

    await _persist_result(job_id, final_state)
    await publish("status_changed", str(final_state.get("status")))
    return final_state.get("final_report") or ""


async def _persist_result(job_id: str, final_state: dict) -> None:
    metadata = final_state.get("metadata") or {"total_cost_usd": 0.0, "total_tokens": 0}
    async with async_session_factory() as session:
        job = await session.scalar(select(Job).where(Job.id == uuid.UUID(job_id)))
        if job is None:
            logger.error("job_row_missing_on_completion", extra={"job_id": job_id})
            return

        job.status = str(final_state.get("status") or ResearchStatus.DONE)
        job.error = final_state.get("error")
        job.total_cost_usd = metadata.get("total_cost_usd", 0.0)
        job.total_tokens = metadata.get("total_tokens", 0)

        if final_state.get("final_report"):
            session.add(
                Report(
                    job_id=job.id,
                    markdown=final_state["final_report"],
                    citations=final_state.get("citations", []),
                    sections=final_state.get("report_sections", {}),
                )
            )
        await session.commit()


# ponytail: DB status only moves queued -> planning -> [done|failed], not
# through every intermediate stage (researching/verifying/writing) — the SSE
# feed already carries that granularity for the live UI. Add per-node DB
# writes here (or a graph-level callback) if REST polling needs to reflect
# the same intermediate stages.
async def _persist_status(job_id: str, status: ResearchStatus) -> None:
    async with async_session_factory() as session:
        job = await session.scalar(select(Job).where(Job.id == uuid.UUID(job_id)))
        if job is None:
            return
        job.status = str(status)
        await session.commit()


async def _persist_failure(job_id: str, error: str) -> None:
    async with async_session_factory() as session:
        job = await session.scalar(select(Job).where(Job.id == uuid.UUID(job_id)))
        if job is None:
            return
        job.status = str(ResearchStatus.FAILED)
        job.error = error
        await session.commit()


def enqueue_job(query: str) -> str:
    job_id = str(uuid.uuid4())
    run_research_job.delay(job_id, query)
    return job_id
