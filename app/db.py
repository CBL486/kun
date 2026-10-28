from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.settings import settings


engine = create_async_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=5,
)


async def database_ready() -> bool:
    """Return whether the configured authoritative database answers queries."""
    try:
        async with engine.connect() as connection:
            return await connection.scalar(text("SELECT 1")) == 1
    except Exception:
        return False
