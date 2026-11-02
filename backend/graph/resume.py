"""Start a job's graph, or continue it from its last checkpoint after a crash.

A redelivered task calls this with the same job_id. Passing the initial state
again would start a new run from the planner on that thread, so only a thread
with no checkpoint gets it; an unfinished thread is continued with None, and a
finished one (crash after the last node, before the result was saved) just
returns its state without re-running any agent.
"""

from typing import Any


async def run_or_resume(graph: Any, initial_state: dict, config: dict) -> dict:
    snapshot = await graph.aget_state(config)
    if snapshot.next:
        return await graph.ainvoke(None, config=config)
    if snapshot.values:
        return snapshot.values
    return await graph.ainvoke(initial_state, config=config)
