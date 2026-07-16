"""Domain repository port and InMemory implementation for study spaces."""

import uuid
from abc import abstractmethod
from datetime import datetime
from typing import Protocol

from src.study_spaces.domain.entities import StudySpace


class StudySpaceRepository(Protocol):
    """Repository protocol for StudySpace persistence."""

    @abstractmethod
    async def save(self, space: StudySpace) -> None:
        """Persist a study space."""
        ...

    @abstractmethod
    async def find_by_id(self, space_id: uuid.UUID) -> StudySpace | None:
        """Find a study space by its identifier."""
        ...

    @abstractmethod
    async def find_by_owner_id(
        self, owner_id: uuid.UUID
    ) -> list[StudySpace]:
        """Find all study spaces for an owner, newest first."""
        ...

    async def flush(self) -> None:
        """Default no-op for InMemory; PostgreSQL adapter overrides."""
        return None

    async def commit(self) -> None:
        """Default no-op for InMemory; PostgreSQL adapter overrides."""
        return None


class InMemoryStudySpaceRepository:
    """InMemory implementation of StudySpaceRepository for testing."""

    def __init__(self) -> None:
        self._spaces: dict[uuid.UUID, StudySpace] = {}

    async def save(self, space: StudySpace) -> None:
        """Persist a study space in memory."""
        self._spaces[space.id] = space

    async def find_by_id(self, space_id: uuid.UUID) -> StudySpace | None:
        """Find a study space by its identifier."""
        return self._spaces.get(space_id)

    async def find_by_owner_id(
        self, owner_id: uuid.UUID
    ) -> list[StudySpace]:
        """Find all study spaces for an owner, newest first."""
        spaces = [s for s in self._spaces.values() if s.owner_id == owner_id]
        spaces.sort(key=lambda s: s.created_at or datetime.min, reverse=True)
        return spaces

    async def flush(self) -> None:
        """No-op for in-memory storage."""
        return None

    async def commit(self) -> None:
        """No-op for in-memory storage."""
        return None