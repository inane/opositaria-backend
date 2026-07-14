"""Shared fixtures for integration tests against real PostgreSQL."""

from collections.abc import AsyncGenerator

import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

DATABASE_URL = (
    "postgresql+asyncpg://opositaria:opositaria_dev@localhost:5433/opositaria"
)


@pytest_asyncio.fixture
async def session() -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh session per test with clean tables."""
    engine = create_async_engine(DATABASE_URL, echo=False)

    # Clean tables before each test
    async with engine.begin() as conn:
        await conn.execute(text("DELETE FROM study_document_chunks"))
        await conn.execute(text("DELETE FROM document_processing_jobs"))
        await conn.execute(text("DELETE FROM study_documents"))

    async_session_factory = async_sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session_factory() as session:
        yield session

    await engine.dispose()
