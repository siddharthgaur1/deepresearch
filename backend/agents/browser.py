from backend.agents.base import BaseAgent
from backend.graph.state import ResearchState
from backend.tools.browser import fetch_rendered_page


class BrowserAgent(BaseAgent):
    """Fills in raw_content for search results that came back without one
    (e.g. JS-rendered pages DuckDuckGo only returned a snippet for)."""

    name = "browser"

    async def run(self, state: ResearchState) -> dict:
        sub_question = state["current_sub_question"]
        results = state["search_results"].get(sub_question["id"], [])

        enriched = []
        for r in results:
            if r["raw_content"]:
                enriched.append(r)
                continue
            page = await fetch_rendered_page(r["url"])
            enriched.append({**r, "raw_content": page["text"] or r["snippet"]})

        return {"search_results": {sub_question["id"]: enriched}}
