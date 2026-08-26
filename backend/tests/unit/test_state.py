"""Regression test for the 'research_branch echoes the full ResearchState back
in parallel' crash: research_branch is a subgraph sharing the parent's full
schema, so N parallel Send()-dispatched branches each return every key
unchanged (not just their delta). Any field without a reducer fails with
"can receive only one value per step" even when the values agree -- see the
_last_write_wins reducer in graph/state.py."""

from langgraph.graph import END, START, StateGraph
from langgraph.types import Send

from backend.graph.state import ResearchState


def _base_state(**overrides):
    state = {
        "job_id": "job-1",
        "query": "test query",
        "sub_questions": [{"id": "sq1", "text": "q1", "status": "pending", "retry_count": 0}],
        "search_results": {},
        "summaries": {},
        "claims": [],
        "verified_claims": [],
        "gaps": [],
        "code_outputs": [],
        "report_sections": {},
        "citations": [],
        "final_report": None,
        "status": "planning",
        "error": None,
        "metadata": {"total_cost_usd": 0.0, "total_tokens": 0, "agent_calls": []},
        "retry_depth": 0,
    }
    state.update(overrides)
    return state


def test_parallel_branches_can_echo_full_state_without_conflict():
    def echo(state: ResearchState) -> dict:
        # Mimics a subgraph node returning the whole state unchanged, as
        # research_branch does, instead of a narrow delta.
        return dict(state)

    def fan_out(state: ResearchState):
        # current_sub_question differs per branch (unlike the other echoed
        # fields, which are identical) -- exercises the same reducer path.
        return [
            Send("branch", {**state, "current_sub_question": {"id": f"sq{i}", "text": "q", "status": "pending", "retry_count": 0}})
            for i in range(3)
        ]

    graph = StateGraph(ResearchState)
    graph.add_node("branch", echo)
    graph.add_conditional_edges(START, fan_out, ["branch"])
    graph.add_edge("branch", END)
    app = graph.compile()

    result = app.invoke(_base_state())
    assert result["job_id"] == "job-1"


if __name__ == "__main__":
    test_parallel_branches_can_echo_full_state_without_conflict()
    print("ok")
