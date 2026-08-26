from contextlib import asynccontextmanager

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from backend.core.config import get_settings


@asynccontextmanager
async def get_checkpointer():
    """Yields a ready-to-use AsyncPostgresSaver, running its one-time setup()
    on first use so a fresh Postgres instance gets its checkpoint tables
    without a separate migration step."""
    settings = get_settings()
    async with AsyncPostgresSaver.from_conn_string(settings.database_url_sync.replace("+psycopg", "")) as saver:
        await saver.setup()
        yield saver
