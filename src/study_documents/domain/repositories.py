"""Domain repository protocols and InMemory implementations for study documents."""

import uuid
from abc import abstractmethod
from typing import Protocol

from src.study_documents.domain.entities import StudyDocument, StudyDocumentChunk


class StudyDocumentRepository(Protocol):
    """Repository protocol for StudyDocument persistence."""

    @abstractmethod
    async def save(self, document: StudyDocument) -> None:
        """Persist a study document."""
        ...

    @abstractmethod
    async def find_by_id(self, document_id: uuid.UUID) -> StudyDocument | None:
        """Find a study document by its identifier."""
        ...

    @abstractmethod
    async def find_by_id_and_owner(
        self, document_id: uuid.UUID, owner_id: uuid.UUID
    ) -> StudyDocument | None:
        """Find a study document by its identifier and owner."""
        ...

    @abstractmethod
    async def find_by_study_space_id_and_owner(
        self, study_space_id: uuid.UUID, owner_id: uuid.UUID
    ) -> list[StudyDocument]:
        """Find all documents in a study space owned by the given user."""
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


class StudyDocumentChunkRepository(Protocol):
    """Repository protocol for StudyDocumentChunk persistence."""

    @abstractmethod
    async def save(self, chunk: StudyDocumentChunk) -> None:
        """Persist a document chunk."""
        ...

    @abstractmethod
    async def find_by_document_id(
        self, document_id: uuid.UUID
    ) -> list[StudyDocumentChunk]:
        """Find all chunks for a document, ordered by sequence number."""
        ...

    @abstractmethod
    async def replace_by_document_id(
        self, document_id: uuid.UUID, chunks: list[StudyDocumentChunk]
    ) -> None:
        """Atomically replace all chunks for a document."""
        ...

    async def flush(self) -> None:
        """Flush pending writes to durable storage.

        Default no-op for InMemory; PostgreSQL adapter overrides to flush session.
        """
        return None


class InMemoryStudyDocumentRepository:
    """InMemory implementation of StudyDocumentRepository for testing."""

    def __init__(self) -> None:
        self._documents: dict[uuid.UUID, StudyDocument] = {}

    async def save(self, document: StudyDocument) -> None:
        """Persist a study document in memory."""
        self._documents[document.id] = document

    async def find_by_id(self, document_id: uuid.UUID) -> StudyDocument | None:
        """Find a study document by its identifier."""
        return self._documents.get(document_id)

    async def find_by_id_and_owner(
        self, document_id: uuid.UUID, owner_id: uuid.UUID
    ) -> StudyDocument | None:
        """Find a study document by its identifier and owner."""
        doc = self._documents.get(document_id)
        if doc is None:
            return None
        if doc.owner_user_id != owner_id:
            return None
        return doc

    async def find_by_study_space_id_and_owner(
        self, study_space_id: uuid.UUID, owner_id: uuid.UUID
    ) -> list[StudyDocument]:
        """Find all documents in a study space owned by the given user."""
        return [
            d
            for d in self._documents.values()
            if d.study_space_id == study_space_id and d.owner_user_id == owner_id
        ]

    async def flush(self) -> None:
        """No-op for in-memory storage."""
        return None

    async def commit(self) -> None:
        """No-op for in-memory storage."""
        return None


class InMemoryStudyDocumentChunkRepository:
    """InMemory implementation of StudyDocumentChunkRepository for testing."""

    def __init__(self) -> None:
        self._chunks: dict[uuid.UUID, StudyDocumentChunk] = {}

    async def save(self, chunk: StudyDocumentChunk) -> None:
        """Persist a document chunk in memory."""
        self._chunks[chunk.id] = chunk

    async def find_by_document_id(
        self, document_id: uuid.UUID
    ) -> list[StudyDocumentChunk]:
        """Find all chunks for a document, ordered by sequence number."""
        return sorted(
            [c for c in self._chunks.values() if c.document_id == document_id],
            key=lambda c: c.sequence_number,
        )

    async def replace_by_document_id(
        self, document_id: uuid.UUID, chunks: list[StudyDocumentChunk]
    ) -> None:
        """Atomically replace all chunks for a document."""
        existing_ids = [
            c.id for c in self._chunks.values() if c.document_id == document_id
        ]
        for cid in existing_ids:
            del self._chunks[cid]
        for chunk in chunks:
            self._chunks[chunk.id] = chunk

    async def flush(self) -> None:
        """No-op for in-memory storage."""
        return None

    async def commit(self) -> None:
        """No-op for in-memory storage."""
        return None
