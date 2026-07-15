"""Shared fixtures for user integration tests against real PostgreSQL."""

from collections.abc import AsyncGenerator

import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

DATABASE_URL = (
    "postgresql+asyncpg://opositaria:opositaria_dev@localhost:5433/opositaria"
)


@pytest_asyncio.fixture
async def session() -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh session per test with clean users table."""
    engine = create_async_engine(DATABASE_URL, echo=False)

    # Clean users table before each test
    async with engine.begin() as conn:
        await conn.execute(text("DELETE FROM users"))

    async_session_factory = async_sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session_factory() as session:
        yield session

    await engine.dispose()
