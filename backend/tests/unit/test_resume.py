"""Crash recovery on the real graph topology (Send() fan-out, nested research
branch, critic), with the agents stubbed and an in-memory checkpointer. The crash
is an exception raised mid-run; run_or_resume is then called again with the same
thread, as a redelivered Celery task would."""

import asyncio
from collections import Counter

import pytest
from langgraph.checkpoint.memory import InMemorySaver

from backend.graph import graph as graph_module
from backend.graph.resume import run_or_resume
from backend.graph.state import ResearchStatus

AGENTS = [
    "PlannerAgent",
    "ResearcherAgent",
    "BrowserAgent",
    "SummarizerAgent",
    "FactCheckerAgent",
    "CriticAgent",
    "CodeExecutorAgent",
    "WriterAgent",
    "CitationValidatorAgent",
]
INITIAL = {
    "job_id": "job-1",
    "query": "q",
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
CONFIG = {"configurable": {"thread_id": "job-1"}}


@pytest.fixture
def calls(monkeypatch):
    counts = Counter()
    crash_in = set()

    def fake(name):
        class Agent:
            async def __call__(self, state):
                counts[name] += 1
                if name in crash_in:
                    crash_in.discard(name)
                    raise RuntimeError("worker died")
                if name == "PlannerAgent":
                    return {
                        "sub_questions": [
                            {"id": s, "text": s, "status": "pending", "retry_count": 0} for s in ("a", "b")
                        ]
                    }
                if name == "WriterAgent":
                    return {"final_report": "report", "status": ResearchStatus.DONE}
                return {"gaps": []}

        return Agent

    for name in AGENTS:
        monkeypatch.setattr(graph_module, name, fake(name))
    counts.crash_in = crash_in
    return counts


def run(graph):
    return asyncio.run(run_or_resume(graph, INITIAL, CONFIG))


def test_fresh_job_runs_every_agent(calls):
    state = run(graph_module.build_graph(InMemorySaver()))
    assert state["final_report"] == "report"
    assert calls["PlannerAgent"] == 1
    assert calls["ResearcherAgent"] == 2  # one per sub-question


def test_crash_resumes_at_the_failed_node_without_repeating_finished_work(calls):
    graph = graph_module.build_graph(InMemorySaver())
    calls.crash_in.add("WriterAgent")
    with pytest.raises(RuntimeError):
        run(graph)
    before = dict(calls)

    state = run(graph)

    assert state["final_report"] == "report"
    assert calls["WriterAgent"] == before["WriterAgent"] + 1
    for finished in ("PlannerAgent", "ResearcherAgent", "SummarizerAgent", "FactCheckerAgent", "CriticAgent"):
        assert calls[finished] == before[finished], finished


def test_crash_after_the_last_node_returns_the_result_without_rerunning(calls):
    graph = graph_module.build_graph(InMemorySaver())
    run(graph)
    before = dict(calls)

    state = run(graph)

    assert state["final_report"] == "report"
    assert dict(calls) == before
