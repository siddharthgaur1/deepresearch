from backend.agents.base import BaseAgent
from backend.graph.state import Claim, ResearchState

FACT_CHECK_PROMPT = """Claim: "{claim}"

Sources:
{sources}

Does the evidence across these sources support the claim? Reply with exactly \
one word: SUPPORTED, PARTIAL, or CONTRADICTED.
"""


class FactCheckerAgent(BaseAgent):
    """Runs once per job after all branches join. Cross-references each claim
    against its source URLs; claims backed by fewer than
    settings.fact_check_min_sources are capped at "low" confidence regardless
    of what the LLM says, since a single source can't be cross-referenced."""

    name = "fact_checker"

    async def run(self, state: ResearchState) -> dict:
        verified: list[Claim] = []
        total_tokens_in = total_tokens_out = 0
        total_cost = 0.0

        for claim in state["claims"]:
            if len(set(claim["source_urls"])) < self.settings.fact_check_min_sources:
                verified.append({**claim, "confidence": "low"})
                continue

            results_by_sq = state["search_results"].get(claim["sub_question_id"], [])
            sources_text = "\n\n".join(
                f"[{r['url']}]\n{(r['raw_content'] or r['snippet'])[:1500]}"
                for r in results_by_sq
                if r["url"] in claim["source_urls"]
            )

            result = await self.complete(
                FACT_CHECK_PROMPT.format(claim=claim["text"], sources=sources_text)
            )
            total_tokens_in += result.tokens_in
            total_tokens_out += result.tokens_out
            total_cost += result.cost_usd

            verdict = result.content.strip().upper()
            confidence = {
                "SUPPORTED": "high",
                "PARTIAL": "medium",
            }.get(verdict, "unverified" if verdict != "CONTRADICTED" else "unverified")
            verified.append({**claim, "confidence": confidence})

        return {
            "verified_claims": verified,
            "status": "verifying",
            "_tokens_in": total_tokens_in,
            "_tokens_out": total_tokens_out,
            "_cost_usd": total_cost,
        }
