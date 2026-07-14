from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.shared.infrastructure.settings import DatabaseSettings


def create_async_engine_from_settings(
    settings: DatabaseSettings | None = None,
) -> AsyncEngine:
    """Create a shared async SQLAlchemy engine from settings.

    This function lives in infrastructure and MUST NOT be imported
    by domain or application layers.
    """
    if settings is None:
        settings = DatabaseSettings()
    return create_async_engine(
        settings.database_async_url, echo=False, pool_pre_ping=True
    )


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Create an async session factory from an engine."""
    return async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


async def get_db_session(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[AsyncSession, None]:
    """Yield an async session from the factory as a dependency."""
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
