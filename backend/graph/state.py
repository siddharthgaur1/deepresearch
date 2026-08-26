"""Core LangGraph state schema shared by every agent node."""

import operator
from enum import StrEnum
from typing import Annotated, NotRequired, TypedDict


class ResearchStatus(StrEnum):
    QUEUED = "queued"
    PLANNING = "planning"
    RESEARCHING = "researching"
    VERIFYING = "verifying"
    WRITING = "writing"
    DONE = "done"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SubQuestion(TypedDict):
    id: str
    text: str
    status: str  # pending | researching | done | failed
    retry_count: int


class SearchResult(TypedDict):
    url: str
    title: str
    snippet: str
    raw_content: str | None
    source_type: str  # web | pdf | browser


class Claim(TypedDict):
    id: str
    text: str
    sub_question_id: str
    source_urls: list[str]
    confidence: str  # high | medium | low | unverified


class Citation(TypedDict):
    id: int
    url: str
    title: str
    verified: bool


class CodeResult(TypedDict):
    sub_question_id: str
    code: str
    stdout: str
    stderr: str
    artifact_paths: list[str]


class AgentCallMetadata(TypedDict):
    agent: str
    duration_seconds: float
    tokens_in: int
    tokens_out: int
    cost_usd: float


class RunMetadata(TypedDict):
    total_cost_usd: float
    total_tokens: int
    agent_calls: list[AgentCallMetadata]


def _merge_dict(left: dict, right: dict) -> dict:
    merged = dict(left)
    merged.update(right)
    return merged


def _last_write_wins(left, right):
    """research_branch is a subgraph sharing this full schema, so each of the
    N parallel Send() branches echoes back every key unchanged, not just its
    delta. Fields with no reducer can't accept those concurrent (identical)
    writes at all -- LangGraph raises 'can receive only one value per step'
    even though the values agree. This reducer makes concurrent writes to an
    otherwise single-writer field legal; last write simply wins."""
    return right


class ResearchState(TypedDict):
    job_id: Annotated[str, _last_write_wins]
    query: Annotated[str, _last_write_wins]
    sub_questions: Annotated[list[SubQuestion], _last_write_wins]
    search_results: Annotated[dict[str, list[SearchResult]], _merge_dict]
    summaries: Annotated[dict[str, str], _merge_dict]
    claims: Annotated[list[Claim], operator.add]
    verified_claims: Annotated[list[Claim], operator.add]
    gaps: Annotated[list[str], _last_write_wins]
    code_outputs: Annotated[list[CodeResult], operator.add]
    report_sections: Annotated[dict[str, str], _merge_dict]
    citations: Annotated[list[Citation], _last_write_wins]
    final_report: Annotated[str | None, _last_write_wins]
    status: Annotated[ResearchStatus, _last_write_wins]
    error: Annotated[str | None, _last_write_wins]
    metadata: Annotated[RunMetadata, _last_write_wins]
    retry_depth: Annotated[int, _last_write_wins]
    # Set only on the per-branch state Send() dispatches into research_branch
    # (see supervisor.fan_out_research). Must be declared here, not just
    # injected ad hoc, or LangGraph's channel system drops it when passing
    # state into the compiled research_branch subgraph. Needs the same
    # last-write-wins reducer as every other plain field -- see its docstring.
    current_sub_question: Annotated[NotRequired[SubQuestion], _last_write_wins]
