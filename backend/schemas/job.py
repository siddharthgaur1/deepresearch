import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class JobCreateRequest(BaseModel):
    query: str = Field(min_length=3, max_length=2000)


class JobCreateResponse(BaseModel):
    job_id: uuid.UUID
    status: str


class SubQuestionOut(BaseModel):
    id: str
    text: str
    status: str


class JobStatusResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    job_id: uuid.UUID
    query: str
    status: str
    error: str | None = None
    total_cost_usd: float
    total_tokens: int
    created_at: datetime
    updated_at: datetime
    sub_questions: list[SubQuestionOut] = Field(default_factory=list)


class JobEvent(BaseModel):
    """One SSE/WebSocket frame published on the job's Redis pub/sub channel."""

    job_id: uuid.UUID
    event: str  # agent_started | agent_finished | sub_question_done | source_found | status_changed | error
    agent: str | None = None
    message: str
    data: dict = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
