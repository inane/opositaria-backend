"""Unit tests for InMemory document processing job repository."""

import uuid

import pytest

from src.document_processing.domain.entities import DocumentProcessingJob
from src.document_processing.domain.repositories import (
    InMemoryDocumentProcessingJobRepository,
)


class TestInMemoryDocumentProcessingJobRepository:
    """Tests for InMemoryDocumentProcessingJobRepository."""

    @pytest.mark.asyncio
    async def test_saves_and_finds_job_by_id(self) -> None:
        """A saved job is retrievable by its identifier."""
        repo = InMemoryDocumentProcessingJobRepository()
        job = DocumentProcessingJob.create(id=uuid.uuid4(), document_id=uuid.uuid4())

        await repo.save(job)
        found = await repo.find_by_id(job.id)

        assert found is not None
        assert found.id == job.id
        assert found.document_id == job.document_id
        assert found.status == "PENDING"

    @pytest.mark.asyncio
    async def test_returns_none_for_missing_job(self) -> None:
        """Finding a non-existent job returns None."""
        repo = InMemoryDocumentProcessingJobRepository()

        found = await repo.find_by_id(uuid.uuid4())

        assert found is None
