"""Repository protocol and InMemory implementation for document processing jobs."""

import uuid
from abc import abstractmethod
from typing import Protocol

from src.document_processing.domain.entities import DocumentProcessingJob


class DocumentProcessingJobRepository(Protocol):
    """Repository protocol for DocumentProcessingJob persistence."""

    @abstractmethod
    async def save(self, job: DocumentProcessingJob) -> None:
        """Persist a processing job."""
        ...

    @abstractmethod
    async def find_by_id(self, job_id: uuid.UUID) -> DocumentProcessingJob | None:
        """Find a processing job by its identifier."""
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


class InMemoryDocumentProcessingJobRepository:
    """InMemory implementation of DocumentProcessingJobRepository for testing."""

    def __init__(self) -> None:
        self._jobs: dict[uuid.UUID, DocumentProcessingJob] = {}

    async def save(self, job: DocumentProcessingJob) -> None:
        """Persist a processing job in memory."""
        self._jobs[job.id] = job

    async def find_by_id(self, job_id: uuid.UUID) -> DocumentProcessingJob | None:
        """Find a processing job by its identifier."""
        return self._jobs.get(job_id)

    async def flush(self) -> None:
        """No-op for in-memory storage."""
        return None

    async def commit(self) -> None:
        """No-op for in-memory storage."""
        return None
