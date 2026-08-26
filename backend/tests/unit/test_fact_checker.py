"""Regression test: a CONTRADICTED verdict must not collapse into the same
"unverified" label as a garbled/unparseable LLM response — evidence actively
disagreeing with a claim is a stronger, distinct signal than "couldn't tell"."""

import pytest

from backend.agents.fact_checker import FactCheckerAgent
from backend.graph.state import ResearchStatus


def _state_with_claim(claim_confidence_input_sources: int) -> dict:
    urls = [f"https://s{i}.com" for i in range(claim_confidence_input_sources)]
    return {
        "job_id": "job-1",
        "query": "q",
        "sub_questions": [{"id": "sq1", "text": "q", "status": "done", "retry_count": 0}],
        "search_results": {
            "sq1": [
                {"url": u, "title": u, "snippet": "s", "raw_content": None, "source_type": "web"}
                for u in urls
            ]
        },
        "summaries": {},
        "claims": [
            {"id": "c1", "text": "claim text", "sub_question_id": "sq1", "source_urls": urls, "confidence": "unverified"}
        ],
        "verified_claims": [],
        "gaps": [],
        "code_outputs": [],
        "report_sections": {},
        "citations": [],
        "final_report": None,
        "status": ResearchStatus.VERIFYING,
        "error": None,
        "metadata": {"total_cost_usd": 0.0, "total_tokens": 0, "agent_calls": []},
        "retry_depth": 0,
    }


@pytest.mark.asyncio
async def test_contradicted_verdict_is_not_labeled_unverified(monkeypatch):
    async def fake_acompletion(**kwargs):
        return {
            "choices": [{"message": {"content": "CONTRADICTED"}}],
            "usage": {"prompt_tokens": 1, "completion_tokens": 1},
        }

    monkeypatch.setattr("litellm.acompletion", fake_acompletion)

    agent = FactCheckerAgent()
    state = _state_with_claim(claim_confidence_input_sources=2)
    result = await agent.run(state)

    assert result["verified_claims"][0]["confidence"] == "contradicted"


@pytest.mark.asyncio
async def test_garbled_verdict_falls_back_to_unverified(monkeypatch):
    async def fake_acompletion(**kwargs):
        return {
            "choices": [{"message": {"content": "not a real verdict"}}],
            "usage": {"prompt_tokens": 1, "completion_tokens": 1},
        }

    monkeypatch.setattr("litellm.acompletion", fake_acompletion)

    agent = FactCheckerAgent()
    state = _state_with_claim(claim_confidence_input_sources=2)
    result = await agent.run(state)

    assert result["verified_claims"][0]["confidence"] == "unverified"


if __name__ == "__main__":
    import asyncio

    asyncio.run(test_contradicted_verdict_is_not_labeled_unverified(pytest.MonkeyPatch()))
    asyncio.run(test_garbled_verdict_falls_back_to_unverified(pytest.MonkeyPatch()))
    print("ok")
