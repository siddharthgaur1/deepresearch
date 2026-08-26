from langgraph.graph import END

from backend.graph.state import ResearchStatus
from backend.graph.supervisor import fan_out_research, route_after_critic


def _base_state(**overrides):
    state = {
        "job_id": "job-1",
        "query": "test query",
        "sub_questions": [],
        "search_results": {},
        "summaries": {},
        "claims": [],
        "verified_claims": [],
        "gaps": [],
        "code_outputs": [],
        "report_sections": {},
        "citations": [],
        "final_report": None,
        "status": ResearchStatus.PLANNING,
        "error": None,
        "metadata": {"total_cost_usd": 0.0, "total_tokens": 0, "agent_calls": []},
        "retry_depth": 0,
    }
    state.update(overrides)
    return state


def test_fan_out_research_creates_one_send_per_pending_question():
    state = _base_state(
        sub_questions=[
            {"id": "a", "text": "q1", "status": "pending", "retry_count": 0},
            {"id": "b", "text": "q2", "status": "done", "retry_count": 0},
            {"id": "c", "text": "q3", "status": "pending", "retry_count": 0},
        ]
    )
    sends = fan_out_research(state)
    assert len(sends) == 2
    assert {s.arg["current_sub_question"]["id"] for s in sends} == {"a", "c"}


def test_fan_out_research_ends_when_no_sub_questions():
    assert fan_out_research(_base_state()) == END


def test_route_after_critic_loops_when_gaps_and_under_retry_limit():
    state = _base_state(gaps=["missing coverage"], retry_depth=1)
    assert route_after_critic(state) == "research_branch"


def test_route_after_critic_proceeds_when_no_gaps():
    state = _base_state(gaps=[], retry_depth=0)
    assert route_after_critic(state) == "code_executor"


def test_route_after_critic_proceeds_when_retry_limit_hit():
    state = _base_state(gaps=["still missing something"], retry_depth=3)
    assert route_after_critic(state) == "code_executor"


if __name__ == "__main__":
    test_fan_out_research_creates_one_send_per_pending_question()
    test_fan_out_research_ends_when_no_sub_questions()
    test_route_after_critic_loops_when_gaps_and_under_retry_limit()
    test_route_after_critic_proceeds_when_no_gaps()
    test_route_after_critic_proceeds_when_retry_limit_hit()
    print("ok")
