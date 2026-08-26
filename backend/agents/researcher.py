from backend.agents.base import BaseAgent
from backend.core.redis import dedup_key, get_redis
from backend.graph.state import ResearchState
from backend.tools.search import search


class ResearcherAgent(BaseAgent):
    """Runs once per sub-question branch (fanned out via LangGraph Send()).
    Expects state to carry a single "current_sub_question" injected by the
    Send() payload, not the full sub_questions list."""

    name = "researcher"

    async def run(self, state: ResearchState) -> dict:
        sub_question = state["current_sub_question"]
        job_id = state["job_id"]

        redis = get_redis()
        seen_key = dedup_key(job_id)

        results = await search(sub_question["text"], max_results=5)

        # dedup: skip URLs already fetched anywhere in this job run
        fresh_results = []
        for r in results:
            if not r["url"]:
                continue
            added = await redis.sadd(seen_key, r["url"])
            if added:
                fresh_results.append(r)

        return {
            "search_results": {sub_question["id"]: fresh_results},
        }
