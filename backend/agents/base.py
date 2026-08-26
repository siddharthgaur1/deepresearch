import logging
import time
from abc import ABC, abstractmethod
from typing import Any

import litellm

from backend.core.config import get_settings
from backend.core.metrics import agent_calls_total, llm_cost_total, llm_tokens_total
from backend.graph.state import AgentCallMetadata, ResearchState
from backend.schemas.agent import AgentCallResult

logger = logging.getLogger("deepresearch.agents")


class BaseAgent(ABC):
    """Every LangGraph node wraps one of these. Subclasses implement `run`;
    `__call__` is what actually gets registered as the graph node so every
    agent gets uniform logging, timing, and cost tracking for free."""

    name: str = "base"

    def __init__(self) -> None:
        self.settings = get_settings()

    @abstractmethod
    async def run(self, state: ResearchState) -> dict[str, Any]:
        """Return a partial state update (LangGraph merges it via the reducers in state.py)."""

    async def __call__(self, state: ResearchState) -> dict[str, Any]:
        start = time.monotonic()
        agent_calls_total.labels(agent=self.name).inc()
        logger.info("agent_started", extra={"agent": self.name, "job_id": state["job_id"]})
        try:
            update = await self.run(state)
        except Exception as exc:  # agents must not crash the graph run
            logger.exception("agent_failed", extra={"agent": self.name, "job_id": state["job_id"]})
            return {"error": f"{self.name}: {exc}"}

        duration = time.monotonic() - start
        call_meta: AgentCallMetadata = {
            "agent": self.name,
            "duration_seconds": duration,
            "tokens_in": update.pop("_tokens_in", 0),
            "tokens_out": update.pop("_tokens_out", 0),
            "cost_usd": update.pop("_cost_usd", 0.0),
        }
        llm_tokens_total.labels(agent=self.name, direction="in").inc(call_meta["tokens_in"])
        llm_tokens_total.labels(agent=self.name, direction="out").inc(call_meta["tokens_out"])
        llm_cost_total.labels(agent=self.name).inc(call_meta["cost_usd"])

        prior = state.get("metadata") or {"total_cost_usd": 0.0, "total_tokens": 0, "agent_calls": []}
        update["metadata"] = {
            "total_cost_usd": prior["total_cost_usd"] + call_meta["cost_usd"],
            "total_tokens": prior["total_tokens"] + call_meta["tokens_in"] + call_meta["tokens_out"],
            "agent_calls": [*prior["agent_calls"], call_meta],
        }
        logger.info(
            "agent_finished",
            extra={"agent": self.name, "job_id": state["job_id"], "duration_seconds": duration},
        )
        return update

    async def complete(self, prompt: str, system: str | None = None) -> AgentCallResult:
        """Single-shot LLM call via LiteLLM, provider chosen by settings.llm_model
        (defaults to a local free Ollama model; set an API key + model to use a paid provider)."""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = await litellm.acompletion(
            model=self.settings.llm_model,
            messages=messages,
            max_tokens=self.settings.llm_max_tokens,
            api_base=self.settings.ollama_base_url if self.settings.llm_model.startswith("ollama/") else None,
        )
        usage = response.get("usage", {}) or {}
        tokens_in = usage.get("prompt_tokens", 0)
        tokens_out = usage.get("completion_tokens", 0)
        try:
            cost = litellm.completion_cost(completion_response=response)
        except Exception:
            cost = 0.0  # local/free models have no published cost table

        return AgentCallResult(
            content=response["choices"][0]["message"]["content"] or "",
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            cost_usd=cost,
        )
