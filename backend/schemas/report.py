import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CitationOut(BaseModel):
    id: int
    url: str
    title: str
    verified: bool


class ReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    job_id: uuid.UUID
    markdown: str
    citations: list[CitationOut]
    sections: dict[str, str]
    created_at: datetime
