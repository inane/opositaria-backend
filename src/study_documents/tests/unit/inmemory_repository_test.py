"""Unit tests for InMemory study document and chunk repositories."""

import uuid

import pytest

from src.study_documents.domain.entities import StudyDocument, StudyDocumentChunk
from src.study_documents.domain.repositories import (
    InMemoryStudyDocumentChunkRepository,
    InMemoryStudyDocumentRepository,
)


class TestInMemoryStudyDocumentRepository:
    """Tests for InMemoryStudyDocumentRepository."""

    @pytest.mark.asyncio
    async def test_saves_and_finds_document_by_id(self) -> None:
        """A saved document is retrievable by its identifier."""
        repo = InMemoryStudyDocumentRepository()
        doc = StudyDocument.create(
            id=uuid.uuid4(),
            filename="test.pdf",
            content_type="application/pdf",
            storage_path="study_documents/test.pdf",
            owner_user_id=uuid.uuid4(),
            study_space_id=uuid.uuid4(),
        )

        await repo.save(doc)
        found = await repo.find_by_id(doc.id)

        assert found is not None
        assert found.id == doc.id
        assert found.filename == "test.pdf"

    @pytest.mark.asyncio
    async def test_returns_none_for_missing_document(self) -> None:
        """Finding a non-existent document returns None."""
        repo = InMemoryStudyDocumentRepository()

        found = await repo.find_by_id(uuid.uuid4())

        assert found is None

    @pytest.mark.asyncio
    async def test_finds_document_by_id_and_owner(self) -> None:
        """A saved document is retrievable by its identifier and owner."""
        repo = InMemoryStudyDocumentRepository()
        owner_id = uuid.uuid4()
        doc = StudyDocument.create(
            id=uuid.uuid4(),
            filename="test.pdf",
            content_type="application/pdf",
            storage_path="study_documents/test.pdf",
            owner_user_id=owner_id,
            study_space_id=uuid.uuid4(),
        )

        await repo.save(doc)
        found = await repo.find_by_id_and_owner(doc.id, owner_id)

        assert found is not None
        assert found.id == doc.id

    @pytest.mark.asyncio
    async def test_does_not_return_document_for_different_owner(self) -> None:
        """Finding a document with a different owner returns None."""
        repo = InMemoryStudyDocumentRepository()
        owner_id = uuid.uuid4()
        other_owner_id = uuid.uuid4()
        doc = StudyDocument.create(
            id=uuid.uuid4(),
            filename="test.pdf",
            content_type="application/pdf",
            storage_path="study_documents/test.pdf",
            owner_user_id=owner_id,
            study_space_id=uuid.uuid4(),
        )

        await repo.save(doc)
        found = await repo.find_by_id_and_owner(doc.id, other_owner_id)

        assert found is None


class TestInMemoryStudyDocumentChunkRepository:
    """Tests for InMemoryStudyDocumentChunkRepository."""

    @pytest.mark.asyncio
    async def test_saves_and_finds_chunks_by_document_id(self) -> None:
        """Saved chunks are retrievable by document id in sequence order."""
        repo = InMemoryStudyDocumentChunkRepository()
        document_id = uuid.uuid4()
        chunks = [
            StudyDocumentChunk.create(
                id=uuid.uuid4(),
                document_id=document_id,
                text="First",
                sequence_number=1,
                embedding=[0.1] * 384,
                embedding_model="test",
            ),
            StudyDocumentChunk.create(
                id=uuid.uuid4(),
                document_id=document_id,
                text="Second",
                sequence_number=2,
                embedding=[0.2] * 384,
                embedding_model="test",
            ),
        ]

        for chunk in chunks:
            await repo.save(chunk)

        found = await repo.find_by_document_id(document_id)

        assert len(found) == 2
        assert found[0].sequence_number == 1
        assert found[0].text == "First"
        assert found[1].sequence_number == 2
        assert found[1].text == "Second"

    @pytest.mark.asyncio
    async def test_replaces_chunks_by_document_id(self) -> None:
        """Replacing chunks for a document removes old chunks and persists new ones."""
        repo = InMemoryStudyDocumentChunkRepository()
        document_id = uuid.uuid4()
        old_chunk = StudyDocumentChunk.create(
            id=uuid.uuid4(),
            document_id=document_id,
            text="Old",
            sequence_number=1,
            embedding=[0.1] * 384,
            embedding_model="test",
        )
        await repo.save(old_chunk)

        new_chunks = [
            StudyDocumentChunk.create(
                id=uuid.uuid4(),
                document_id=document_id,
                text="New",
                sequence_number=1,
                embedding=[0.3] * 384,
                embedding_model="test",
            ),
        ]
        await repo.replace_by_document_id(document_id, new_chunks)

        found = await repo.find_by_document_id(document_id)
        assert len(found) == 1
        assert found[0].text == "New"

    @pytest.mark.asyncio
    async def test_returns_empty_list_for_missing_document_chunks(self) -> None:
        """Finding chunks for a document with no chunks returns an empty list."""
        repo = InMemoryStudyDocumentChunkRepository()

        found = await repo.find_by_document_id(uuid.uuid4())

        assert found == []
