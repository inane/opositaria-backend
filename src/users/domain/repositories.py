"""Domain repository protocols and InMemory implementations for users."""

import uuid
from abc import abstractmethod
from typing import Protocol

from src.users.domain.entities import User


class UserRepository(Protocol):
    """Repository protocol for User persistence."""

    @abstractmethod
    async def save(self, user: User) -> None:
        """Persist a user."""
        ...

    @abstractmethod
    async def find_by_id(self, user_id: uuid.UUID) -> User | None:
        """Find a user by their identifier."""
        ...

    @abstractmethod
    async def find_by_email(self, email: str) -> User | None:
        """Find a user by their normalized email."""
        ...

    async def flush(self) -> None:
        """Flush pending writes to durable storage.

        Default no-op for InMemory; PostgreSQL adapter overrides to flush session.
        """
        return None

    async def commit(self) -> None:
        """Commit the current transaction durably.

        Default no-op for InMemory; PostgreSQL adapter overrides to commit session.
        """
        return None


class InMemoryUserRepository:
    """InMemory implementation of UserRepository for testing."""

    def __init__(self) -> None:
        self._users_by_id: dict[uuid.UUID, User] = {}
        self._users_by_email: dict[str, User] = {}

    async def save(self, user: User) -> None:
        """Persist a user in memory."""
        self._users_by_id[user.id] = user
        self._users_by_email[user.email] = user

    async def find_by_id(self, user_id: uuid.UUID) -> User | None:
        """Find a user by their identifier."""
        return self._users_by_id.get(user_id)

    async def find_by_email(self, email: str) -> User | None:
        """Find a user by their normalized email."""
        return self._users_by_email.get(email)

    async def flush(self) -> None:
        """No-op for in-memory storage."""
        return None

    async def commit(self) -> None:
        """No-op for in-memory storage."""
        return None
