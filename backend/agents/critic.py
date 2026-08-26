import json

from backend.agents.base import BaseAgent
from backend.graph.state import ResearchState

CRITIC_PROMPT = """Original query: {query}

Sub-questions researched: {questions}

Summaries:
{summaries}

Identify any gaps in coverage: sub-topics the query implies but that were not \
addressed, or claims that are contradicted/unverified and need re-research. \
Respond as a JSON array of short gap descriptions (empty array if coverage is \
adequate).
"""


class CriticAgent(BaseAgent):
    """Decides whether the graph should loop back into research. The actual
    routing (loop vs. proceed to writer) lives in graph/supervisor.py, which
    reads state["gaps"] and state["retry_depth"] against
    settings.max_retry_depth."""

    name = "critic"

    async def run(self, state: ResearchState) -> dict:
        questions_text = "\n".join(f"- {sq['text']}" for sq in state["sub_questions"])
        summaries_text = "\n\n".join(
            f"{sq['text']}: {state['summaries'].get(sq['id'], '(no summary)')}"
            for sq in state["sub_questions"]
        )

        low_confidence = [c["text"] for c in state["verified_claims"] if c["confidence"] in ("low", "unverified")]

        result = await self.complete(
            CRITIC_PROMPT.format(query=state["query"], questions=questions_text, summaries=summaries_text)
        )

        try:
            gaps = [str(g) for g in json.loads(result.content)]
        except Exception:
            gaps = []

        if low_confidence:
            gaps.append(f"{len(low_confidence)} claim(s) remain low-confidence or unverified")

        return {
            "gaps": gaps,
            "retry_depth": state.get("retry_depth", 0) + (1 if gaps else 0),
            "_tokens_in": result.tokens_in,
            "_tokens_out": result.tokens_out,
            "_cost_usd": result.cost_usd,
        }
