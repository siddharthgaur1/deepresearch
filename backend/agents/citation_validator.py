import httpx

from backend.agents.base import BaseAgent
from backend.graph.state import ResearchState


class CitationValidatorAgent(BaseAgent):
    """Final node before the graph ends. HEAD-checks every citation URL
    (falling back to GET if HEAD is rejected) and flags unreachable ones
    directly in the rendered markdown rather than silently dropping them —
    the report should be honest about what it could and couldn't verify."""

    name = "citation_validator"

    async def run(self, state: ResearchState) -> dict:
        citations = state["citations"]
        async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
            verified = []
            for c in citations:
                ok = await self._check(client, c["url"])
                verified.append({**c, "verified": ok})

        markdown = state["final_report"] or ""
        unreachable = [c for c in verified if not c["verified"]]
        if unreachable:
            note = "\n\n## Citation Validation\n" + "\n".join(
                f"- ⚠️ [{c['id']}] unreachable at report generation time: {c['url']}" for c in unreachable
            )
            markdown += note

        return {"citations": verified, "final_report": markdown}

    @staticmethod
    async def _check(client: httpx.AsyncClient, url: str) -> bool:
        if not url:
            return False
        try:
            resp = await client.head(url)
            if resp.status_code >= 400:
                resp = await client.get(url)
            return resp.status_code < 400
        except Exception:
            return False
