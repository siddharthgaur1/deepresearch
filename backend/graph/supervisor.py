"""Conditional-edge routing logic. Kept separate from graph.py so the
retry/re-research decision (the one bit of real branching logic in this
graph) is unit-testable without spinning up a full StateGraph."""

from langgraph.graph import END
from langgraph.types import Send

from backend.core.config import get_settings
from backend.graph.state import ResearchState


def fan_out_research(state: ResearchState) -> list[Send] | str:
    """Dispatches one parallel research branch per pending sub-question via
    LangGraph's Send() API. Each branch gets the whole state plus
    `current_sub_question`, consumed by researcher/browser/summarizer.
    Falls back to END if the planner produced no sub-questions at all."""
    sends = [
        Send("research_branch", {**state, "current_sub_question": sq})
        for sq in state["sub_questions"]
        if sq["status"] == "pending"
    ]
    return sends or END


def route_after_critic(state: ResearchState) -> str:
    """Loop back into research if the Critic found gaps and we haven't hit
    the configured retry depth; otherwise proceed to report writing."""
    settings = get_settings()
    if state.get("gaps") and state.get("retry_depth", 0) < settings.max_retry_depth:
        return "research_branch"
    return "code_executor"
