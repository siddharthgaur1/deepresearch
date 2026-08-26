from backend.agents.base import BaseAgent
from backend.graph.state import Citation, ResearchState

WRITER_PROMPT = """Write a research report section for the sub-question below, \
using the findings and citing sources inline as [n] using the numbers given.

Sub-question: {question}
Findings: {summary}
Available citation numbers for this section's sources: {citation_numbers}

Write 2-4 paragraphs of prose. Do not repeat the sub-question as a heading, \
the heading is added separately.
"""

EXEC_SUMMARY_PROMPT = """Write a 3-5 sentence executive summary of this research \
report for the query "{query}", based on these section summaries:

{sections}
"""


class WriterAgent(BaseAgent):
    """Runs once per job after verification. Assembles the final markdown:
    exec summary, methodology, one section per sub-question, then key
    findings with confidence scores."""

    name = "writer"

    async def run(self, state: ResearchState) -> dict:
        citations, url_to_citation_id = _build_citations(state)

        sections: dict[str, str] = {}
        total_tokens_in = total_tokens_out = 0
        total_cost = 0.0

        for sq in state["sub_questions"]:
            summary = state["summaries"].get(sq["id"], "")
            urls = [r["url"] for r in state["search_results"].get(sq["id"], [])]
            citation_numbers = sorted({url_to_citation_id[u] for u in urls if u in url_to_citation_id})

            result = await self.complete(
                WRITER_PROMPT.format(
                    question=sq["text"], summary=summary, citation_numbers=citation_numbers
                )
            )
            sections[sq["id"]] = result.content
            total_tokens_in += result.tokens_in
            total_tokens_out += result.tokens_out
            total_cost += result.cost_usd

        exec_result = await self.complete(
            EXEC_SUMMARY_PROMPT.format(
                query=state["query"],
                sections="\n".join(f"- {state['summaries'].get(sq['id'], '')}" for sq in state["sub_questions"]),
            )
        )
        total_tokens_in += exec_result.tokens_in
        total_tokens_out += exec_result.tokens_out
        total_cost += exec_result.cost_usd

        markdown = _render_markdown(state, exec_result.content, sections, citations)

        return {
            "report_sections": sections,
            "citations": citations,
            "final_report": markdown,
            "status": "done",
            "_tokens_in": total_tokens_in,
            "_tokens_out": total_tokens_out,
            "_cost_usd": total_cost,
        }


def _build_citations(state: ResearchState) -> tuple[list[Citation], dict[str, int]]:
    citations: list[Citation] = []
    url_to_id: dict[str, int] = {}
    next_id = 1
    for results in state["search_results"].values():
        for r in results:
            if r["url"] and r["url"] not in url_to_id:
                url_to_id[r["url"]] = next_id
                citations.append(Citation(id=next_id, url=r["url"], title=r["title"], verified=False))
                next_id += 1
    return citations, url_to_id


def _render_markdown(
    state: ResearchState, exec_summary: str, sections: dict[str, str], citations: list[Citation]
) -> str:
    lines = [f"# Research Report: {state['query']}", "", "## Executive Summary", exec_summary, ""]

    lines.append("## Findings")
    for sq in state["sub_questions"]:
        lines += [f"### {sq['text']}", sections.get(sq["id"], ""), ""]

    lines.append("## Key Findings & Confidence")
    for claim in state["verified_claims"]:
        lines.append(f"- **[{claim['confidence'].upper()}]** {claim['text']}")
    lines.append("")

    lines.append("## Methodology")
    agent_names = sorted({c["agent"] for c in state["metadata"]["agent_calls"]})
    lines.append(f"Agents involved: {', '.join(agent_names)}. Sources checked: {len(citations)}.")
    lines.append("")

    lines.append("## Sources")
    for c in citations:
        lines.append(f"[{c['id']}] {c['title']} — {c['url']}")

    return "\n".join(lines)
