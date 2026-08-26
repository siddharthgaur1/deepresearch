from backend.agents.writer import _build_citations, _render_markdown
from backend.graph.state import ResearchStatus


def _state_with_results():
    return {
        "job_id": "job-1",
        "query": "what is X",
        "sub_questions": [{"id": "sq1", "text": "what is X", "status": "done", "retry_count": 0}],
        "search_results": {
            "sq1": [
                {"url": "https://a.com", "title": "A", "snippet": "", "raw_content": None, "source_type": "web"},
                {"url": "https://b.com", "title": "B", "snippet": "", "raw_content": None, "source_type": "web"},
                {"url": "https://a.com", "title": "A dup", "snippet": "", "raw_content": None, "source_type": "web"},
            ]
        },
        "summaries": {"sq1": "X is a thing."},
        "claims": [],
        "verified_claims": [{"id": "c1", "text": "X exists", "sub_question_id": "sq1", "source_urls": ["https://a.com"], "confidence": "high"}],
        "gaps": [],
        "code_outputs": [],
        "report_sections": {},
        "citations": [],
        "final_report": None,
        "status": ResearchStatus.WRITING,
        "error": None,
        "metadata": {"total_cost_usd": 0.0, "total_tokens": 0, "agent_calls": [{"agent": "planner", "duration_seconds": 0.1, "tokens_in": 1, "tokens_out": 1, "cost_usd": 0.0}]},
        "retry_depth": 0,
    }


def test_build_citations_dedupes_urls():
    state = _state_with_results()
    citations, url_to_id = _build_citations(state)
    assert len(citations) == 2  # a.com and b.com, dup a.com collapsed
    assert url_to_id["https://a.com"] == 1
    assert url_to_id["https://b.com"] == 2


def test_render_markdown_includes_all_sections():
    state = _state_with_results()
    citations, _ = _build_citations(state)
    md = _render_markdown(state, "exec summary text", {"sq1": "section body"}, citations)
    assert "# Research Report: what is X" in md
    assert "exec summary text" in md
    assert "section body" in md
    assert "**[HIGH]** X exists" in md
    assert "[1] A" in md and "https://a.com" in md


def test_render_markdown_warns_when_no_citations():
    state = _state_with_results()
    md = _render_markdown(state, "exec summary text", {"sq1": "section body"}, [])
    assert "no sources were retrieved" in md
    assert "unverified" in md


def test_render_markdown_warns_when_agent_failed():
    state = _state_with_results()
    state["error"] = "fact_checker: connection reset"
    citations, _ = _build_citations(state)
    md = _render_markdown(state, "exec summary text", {"sq1": "section body"}, citations)
    assert "an agent failed mid-run" in md
    assert "fact_checker: connection reset" in md


if __name__ == "__main__":
    test_build_citations_dedupes_urls()
    test_render_markdown_includes_all_sections()
    test_render_markdown_warns_when_no_citations()
    test_render_markdown_warns_when_agent_failed()
    print("ok")
