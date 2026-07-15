"""Unit tests for in-memory user repository."""

import uuid

import pytest

from src.users.domain.entities import User
from src.users.domain.repositories import InMemoryUserRepository


class TestInMemoryUserRepository:
    """Tests for InMemoryUserRepository."""

    @pytest.mark.asyncio
    async def test_saves_and_finds_user_by_id(self) -> None:
        """A saved user is retrievable by identifier."""
        repo = InMemoryUserRepository()
        user = User.create(
            id=uuid.uuid4(),
            email="student@example.com",
            password_hash="$2b$12$hashedpassword123",
        )

        await repo.save(user)
        found = await repo.find_by_id(user.id)

        assert found is not None
        assert found.id == user.id
        assert found.email == "student@example.com"

    @pytest.mark.asyncio
    async def test_returns_none_for_missing_user(self) -> None:
        """Finding a non-existent user returns None."""
        repo = InMemoryUserRepository()

        found = await repo.find_by_id(uuid.uuid4())

        assert found is None

    @pytest.mark.asyncio
    async def test_finds_user_by_normalized_email(self) -> None:
        """A saved user is retrievable by their normalized email."""
        repo = InMemoryUserRepository()
        user = User.create(
            id=uuid.uuid4(),
            email="student@example.com",
            password_hash="$2b$12$hashedpassword123",
        )

        await repo.save(user)
        found = await repo.find_by_email("student@example.com")

        assert found is not None
        assert found.id == user.id

    @pytest.mark.asyncio
    async def test_returns_none_for_unknown_email(self) -> None:
        """Finding a user by an unregistered email returns None."""
        repo = InMemoryUserRepository()

        found = await repo.find_by_email("unknown@example.com")

        assert found is None

    @pytest.mark.asyncio
    async def test_save_overwrites_existing_email(self) -> None:
        """Saving a user with an existing email overwrites the previous user."""
        repo = InMemoryUserRepository()
        user_id = uuid.uuid4()
        user = User.create(
            id=user_id,
            email="student@example.com",
            password_hash="$2b$12$hash1",
        )
        await repo.save(user)

        different_user = User.create(
            id=uuid.uuid4(),
            email="student@example.com",
            password_hash="$2b$12$hash2",
        )
        await repo.save(different_user)

        found = await repo.find_by_email("student@example.com")
        assert found is not None
        assert found.id == different_user.id
