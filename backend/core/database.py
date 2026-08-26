from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from backend.core.config import get_settings

settings = get_settings()

engine = create_async_engine(settings.database_url, pool_pre_ping=True)
async_session_factory = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


# Import after Base is defined so every model registers on Base.metadata
# regardless of which module imports Base first — otherwise SQLAlchemy can't
# resolve cross-model foreign keys (e.g. Job.user_id -> users.id) unless the
# request happens to have already imported models/user.py.
import backend.models  # noqa: E402, F401


async def get_db() -> AsyncIterator[AsyncSession]:
    async with async_session_factory() as session:
        yield session
