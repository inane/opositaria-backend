"""Integration tests for PostgresUserRepository."""

import uuid

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.users.domain.entities import User
from src.users.infrastructure.repositories import PostgresUserRepository


class TestPostgresUserRepository:
    """Integration tests for PostgresUserRepository."""

    @pytest.mark.asyncio
    async def test_saves_and_finds_user_by_id(self, session: AsyncSession) -> None:
        """A saved user is retrievable by identifier."""
        repo = PostgresUserRepository(session)
        user_id = uuid.uuid4()
        user = User.create(
            id=user_id,
            email="student@example.com",
            password_hash="$2b$12$hashedpassword123",
        )

        await repo.save(user)
        await repo.flush()
        found = await repo.find_by_id(user_id)

        assert found is not None
        assert found.id == user_id
        assert found.email == "student@example.com"
        assert found.password_hash == "$2b$12$hashedpassword123"

    @pytest.mark.asyncio
    async def test_returns_none_for_missing_id(self, session: AsyncSession) -> None:
        """Finding a non-existent user by id returns None."""
        repo = PostgresUserRepository(session)

        found = await repo.find_by_id(uuid.uuid4())

        assert found is None

    @pytest.mark.asyncio
    async def test_finds_user_by_email(self, session: AsyncSession) -> None:
        """A saved user is retrievable by email."""
        repo = PostgresUserRepository(session)
        user_id = uuid.uuid4()
        user = User.create(
            id=user_id,
            email="student@example.com",
            password_hash="$2b$12$hash",
        )

        await repo.save(user)
        await repo.flush()
        found = await repo.find_by_email("student@example.com")

        assert found is not None
        assert found.id == user_id

    @pytest.mark.asyncio
    async def test_returns_none_for_unknown_email(self, session: AsyncSession) -> None:
        """Finding a user by unknown email returns None."""
        repo = PostgresUserRepository(session)

        found = await repo.find_by_email("unknown@example.com")

        assert found is None

    @pytest.mark.asyncio
    async def test_rejects_duplicate_email(self, session: AsyncSession) -> None:
        """Saving a user with a duplicate email raises IntegrityError."""
        repo = PostgresUserRepository(session)
        user1 = User.create(
            id=uuid.uuid4(),
            email="student@example.com",
            password_hash="$2b$12$hash1",
        )
        user2 = User.create(
            id=uuid.uuid4(),
            email="student@example.com",
            password_hash="$2b$12$hash2",
        )

        await repo.save(user1)
        await repo.flush()

        with pytest.raises(IntegrityError):
            await repo.save(user2)
