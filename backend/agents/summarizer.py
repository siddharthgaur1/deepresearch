import json
import uuid

from backend.agents.base import BaseAgent
from backend.graph.state import Claim, ResearchState

SUMMARIZER_PROMPT = """You are summarizing research sources for the sub-question: \
"{question}"

Sources:
{sources}

Write a concise structured summary (3-6 sentences), then list the distinct \
factual claims it supports. Respond as JSON:
{{"summary": "...", "claims": ["claim 1", "claim 2"]}}
"""


class SummarizerAgent(BaseAgent):
    name = "summarizer"

    async def run(self, state: ResearchState) -> dict:
        sub_question = state["current_sub_question"]
        results = state["search_results"].get(sub_question["id"], [])

        sources_text = "\n\n".join(
            f"[{r['url']}]\n{(r['raw_content'] or r['snippet'])[:2000]}" for r in results
        ) or "No sources found."

        result = await self.complete(
            SUMMARIZER_PROMPT.format(question=sub_question["text"], sources=sources_text)
        )

        try:
            parsed = json.loads(result.content)
            summary = str(parsed.get("summary", ""))
            claim_texts = [str(c) for c in parsed.get("claims", [])]
        except Exception:
            summary = result.content
            claim_texts = []

        source_urls = [r["url"] for r in results]
        claims: list[Claim] = [
            Claim(
                id=str(uuid.uuid4()),
                text=text,
                sub_question_id=sub_question["id"],
                source_urls=source_urls,
                confidence="unverified",
            )
            for text in claim_texts
        ]

        return {
            "summaries": {sub_question["id"]: summary},
            "claims": claims,
            "_tokens_in": result.tokens_in,
            "_tokens_out": result.tokens_out,
            "_cost_usd": result.cost_usd,
        }
