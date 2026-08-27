import json
import uuid

from backend.agents.base import BaseAgent
from backend.graph.state import Claim, ResearchState

SUMMARIZER_PROMPT = """You are summarizing research sources for the sub-question: \
"{question}"

Sources:
{sources}

Write a concise structured summary (3-6 sentences), then list the distinct \
factual claims it supports. For each claim, name which of the source URLs \
above actually support it — not every source in this batch, only the ones \
that specifically back that claim. Respond as JSON:
{{"summary": "...", "claims": [{{"text": "claim text", "source_urls": ["url1", "url2"]}}]}}
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
            raw_claims = parsed.get("claims", [])
        except Exception:
            summary = result.content
            raw_claims = []

        # Per-claim source_urls must come from the model, not from blanket-
        # attaching every source in the batch to every claim: that would let
        # a single-source claim silently pass fact_checker's "supported by
        # >=2 independent sources" gate just because the sub-question had 2+
        # search results overall, regardless of which of them actually back
        # that specific claim. Only fall back to the old blanket behavior
        # for a claim the model returned as a bare string (schema not
        # followed — small local models sometimes ignore it), since at that
        # point there's no per-claim attribution to recover.
        all_urls = [r["url"] for r in results]
        valid_urls = {r["url"] for r in results}
        claims: list[Claim] = []
        for c in raw_claims:
            if isinstance(c, dict):
                text = str(c.get("text", "")).strip()
                source_urls = [u for u in c.get("source_urls", []) if u in valid_urls]
            else:
                text = str(c).strip()
                source_urls = all_urls
            if not text:
                continue
            claims.append(
                Claim(
                    id=str(uuid.uuid4()),
                    text=text,
                    sub_question_id=sub_question["id"],
                    source_urls=source_urls,
                    confidence="unverified",
                )
            )

        return {
            "summaries": {sub_question["id"]: summary},
            "claims": claims,
            "_tokens_in": result.tokens_in,
            "_tokens_out": result.tokens_out,
            "_cost_usd": result.cost_usd,
        }
