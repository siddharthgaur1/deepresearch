"""Regression test: a weak/small LLM (e.g. qwen2.5:0.5b) can fail to emit a
stop token and generate thousands of tokens for what should be a short JSON
reply. BaseAgent.complete() must cap generation via max_tokens rather than
relying on the model to behave."""

import pytest

from backend.agents.base import BaseAgent


class _DummyAgent(BaseAgent):
    name = "dummy"

    async def run(self, state):
        return {}


@pytest.mark.asyncio
async def test_complete_passes_max_tokens(monkeypatch):
    captured = {}

    async def fake_acompletion(**kwargs):
        captured.update(kwargs)
        return {
            "choices": [{"message": {"content": "ok"}}],
            "usage": {"prompt_tokens": 1, "completion_tokens": 1},
        }

    monkeypatch.setattr("litellm.acompletion", fake_acompletion)

    agent = _DummyAgent()
    await agent.complete("hello")

    assert captured["max_tokens"] == agent.settings.llm_max_tokens
    assert captured["max_tokens"] > 0


@pytest.mark.asyncio
async def test_agent_failure_does_not_leak_exception_details():
    """__call__'s except path must not put the raw exception (which can
    embed prompt/query content or a provider error echoing request details)
    into the state update -- that value flows into the DB, the SSE feed, and
    the final report itself (writer.py surfaces state["error"])."""

    class _FailingAgent(BaseAgent):
        name = "dummy"

        async def run(self, state):
            raise ValueError("sk-super-secret-leaked-api-key-and-full-prompt-text")

    agent = _FailingAgent()
    update = await agent(
        {"job_id": "job-1", "metadata": {"total_cost_usd": 0.0, "total_tokens": 0, "agent_calls": []}}
    )

    assert "sk-super-secret-leaked-api-key-and-full-prompt-text" not in update["error"]
    assert "dummy" in update["error"]


if __name__ == "__main__":
    import asyncio

    asyncio.run(test_complete_passes_max_tokens(pytest.MonkeyPatch()))
    asyncio.run(test_agent_failure_does_not_leak_exception_details())
    print("ok")
