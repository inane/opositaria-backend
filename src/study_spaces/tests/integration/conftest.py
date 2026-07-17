"""Shared fixtures for study_spaces integration tests against real PostgreSQL."""

from collections.abc import AsyncGenerator

import pytest_asyncio
from alembic.config import Config
from alembic.command import upgrade
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

DATABASE_URL = (
    "postgresql+asyncpg://opositaria:opositaria_dev@localhost:5433/opositaria"
)


@pytest_asyncio.fixture(scope="session")
def run_migrations() -> None:
    """Run Alembic migrations once per test session."""
    alembic_cfg = Config("alembic.ini")
    upgrade(alembic_cfg, "head")


@pytest_asyncio.fixture
async def session(run_migrations: None) -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh session per test with clean tables."""
    engine = create_async_engine(DATABASE_URL, echo=False)

    # Clean tables before each test
    async with engine.begin() as conn:
        await conn.execute(text("DELETE FROM study_document_chunks"))
        await conn.execute(text("DELETE FROM document_processing_jobs"))
        await conn.execute(text("DELETE FROM study_documents"))
        await conn.execute(text("DELETE FROM study_spaces"))
        await conn.execute(text("DELETE FROM users"))

    async_session_factory = async_sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session_factory() as session:
        yield session

    await engine.dispose()
