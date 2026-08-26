"""Regression test: each claim's source_urls must come from the model's
per-claim attribution, not a blanket copy of every source in the batch --
otherwise a single-source claim silently passes fact_checker's ">=2
independent sources" gate just because the sub-question had 2+ results
overall, regardless of which of them actually back that specific claim."""

import json

import pytest

from backend.agents.summarizer import SummarizerAgent
from backend.graph.state import ResearchStatus


def _state() -> dict:
    return {
        "job_id": "job-1",
        "query": "q",
        "sub_questions": [{"id": "sq1", "text": "q", "status": "done", "retry_count": 0}],
        "search_results": {
            "sq1": [
                {"url": "https://a.com", "title": "A", "snippet": "s", "raw_content": None, "source_type": "web"},
                {"url": "https://b.com", "title": "B", "snippet": "s", "raw_content": None, "source_type": "web"},
            ]
        },
        "summaries": {},
        "claims": [],
        "verified_claims": [],
        "gaps": [],
        "code_outputs": [],
        "report_sections": {},
        "citations": [],
        "final_report": None,
        "status": ResearchStatus.RESEARCHING,
        "error": None,
        "metadata": {"total_cost_usd": 0.0, "total_tokens": 0, "agent_calls": []},
        "retry_depth": 0,
        "current_sub_question": {"id": "sq1", "text": "q", "status": "researching", "retry_count": 0},
    }


@pytest.mark.asyncio
async def test_claim_source_urls_come_from_per_claim_attribution(monkeypatch):
    async def fake_acompletion(**kwargs):
        content = json.dumps(
            {
                "summary": "summary text",
                "claims": [
                    {"text": "only A supports this", "source_urls": ["https://a.com"]},
                    {"text": "both support this", "source_urls": ["https://a.com", "https://b.com"]},
                ],
            }
        )
        return {"choices": [{"message": {"content": content}}], "usage": {"prompt_tokens": 1, "completion_tokens": 1}}

    monkeypatch.setattr("litellm.acompletion", fake_acompletion)

    agent = SummarizerAgent()
    result = await agent.run(_state())
    claims = {c["text"]: c["source_urls"] for c in result["claims"]}

    assert claims["only A supports this"] == ["https://a.com"]
    assert set(claims["both support this"]) == {"https://a.com", "https://b.com"}


@pytest.mark.asyncio
async def test_claim_falls_back_to_all_sources_when_model_ignores_schema(monkeypatch):
    async def fake_acompletion(**kwargs):
        content = json.dumps({"summary": "summary text", "claims": ["a bare string claim"]})
        return {"choices": [{"message": {"content": content}}], "usage": {"prompt_tokens": 1, "completion_tokens": 1}}

    monkeypatch.setattr("litellm.acompletion", fake_acompletion)

    agent = SummarizerAgent()
    result = await agent.run(_state())

    assert set(result["claims"][0]["source_urls"]) == {"https://a.com", "https://b.com"}


if __name__ == "__main__":
    import asyncio

    asyncio.run(test_claim_source_urls_come_from_per_claim_attribution(pytest.MonkeyPatch()))
    asyncio.run(test_claim_falls_back_to_all_sources_when_model_ignores_schema(pytest.MonkeyPatch()))
    print("ok")
