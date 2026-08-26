"""Importing this package registers every model on Base.metadata, which
SQLAlchemy needs to resolve cross-model foreign keys (e.g. Job.user_id ->
users.id) regardless of which module happens to import first."""

from backend.models.job import AgentRun, Job, SourceCache  # noqa: F401
from backend.models.report import Report, SourceDocument  # noqa: F401
from backend.models.user import User  # noqa: F401
