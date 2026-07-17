"""Integration tests for PostgreSQL study document and chunk repositories."""

import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.study_documents.domain.entities import StudyDocument, StudyDocumentChunk
from src.study_documents.infrastructure.repositories import (
    PostgresSemanticChunkSearchRepository,
    PostgresStudyDocumentChunkRepository,
    PostgresStudyDocumentRepository,
)


async def _create_user(session: AsyncSession) -> uuid.UUID:
    """Insert a minimal user row and return its id."""
    user_id = uuid.uuid4()
    await session.execute(
        text("""
            INSERT INTO users (id, email, password_hash, created_at)
            VALUES (:id, :email, :hash, :now)
        """),
        {
            "id": user_id,
            "email": f"{user_id}@test.com",
            "hash": "dummy_hash",
            "now": datetime.now(timezone.utc),
        },
    )
    return user_id


async def _create_study_space(session: AsyncSession, owner_id: uuid.UUID) -> uuid.UUID:
    """Insert a minimal study space row and return its id."""
    space_id = uuid.uuid4()
    await session.execute(
        text("""
            INSERT INTO study_spaces (id, owner_id, name, document_count, created_at)
            VALUES (:id, :owner_id, :name, :count, :now)
        """),
        {
            "id": space_id,
            "owner_id": owner_id,
            "name": "Test Space",
            "count": 1,
            "now": datetime.now(timezone.utc),
        },
    )
    return space_id


@pytest.mark.integration
class TestPostgresStudyDocumentRepository:
    """Integration tests for PostgresStudyDocumentRepository."""

    @pytest.mark.asyncio
    async def test_study_space_id_roundtrips_through_save_and_load(
        self, session: AsyncSession
    ) -> None:
        """Saving a document preserves its study_space_id on load."""
        owner_id = await _create_user(session)
        space_id = await _create_study_space(session, owner_id)
        await session.commit()

        repo = PostgresStudyDocumentRepository(session)
        doc = StudyDocument.create(
            id=uuid.uuid4(),
            filename="space-test.pdf",
            content_type="application/pdf",
            storage_path="study_documents/space-test.pdf",
            owner_user_id=owner_id,
            study_space_id=space_id,
        )

        await repo.save(doc)
        await session.commit()

        loaded = await repo.find_by_id(doc.id)

        assert loaded is not None
        assert loaded.study_space_id == space_id
        assert loaded.owner_user_id == owner_id

    @pytest.mark.asyncio
    async def test_saves_and_finds_document_by_id(self, session: AsyncSession) -> None:
        """A saved document is retrievable by its identifier."""
        owner_id = await _create_user(session)
        space_id = await _create_study_space(session, owner_id)
        await session.commit()

        repo = PostgresStudyDocumentRepository(session)
        doc = StudyDocument.create(
            id=uuid.uuid4(),
            filename="test.pdf",
            content_type="application/pdf",
            storage_path="study_documents/test.pdf",
            owner_user_id=owner_id,
            study_space_id=space_id,
        )

        await repo.save(doc)
        await session.commit()

        found = await repo.find_by_id(doc.id)

        assert found is not None
        assert found.filename == "test.pdf"
        assert found.status == "PENDING_PROCESSING"
        assert found.owner_user_id == owner_id
        assert found.study_space_id == space_id

    @pytest.mark.asyncio
    async def test_updates_document_status(self, session: AsyncSession) -> None:
        """A saved document status can be updated."""
        owner_id = await _create_user(session)
        space_id = await _create_study_space(session, owner_id)
        await session.commit()

        repo = PostgresStudyDocumentRepository(session)
        doc = StudyDocument.create(
            id=uuid.uuid4(),
            filename="test.pdf",
            content_type="application/pdf",
            storage_path="study_documents/test.pdf",
            owner_user_id=owner_id,
            study_space_id=space_id,
        )
        await repo.save(doc)
        doc.mark_as_processing()
        await repo.save(doc)
        await session.commit()

        found = await repo.find_by_id(doc.id)

        assert found is not None
        assert found.status == "PROCESSING"

    @pytest.mark.asyncio
    async def test_finds_document_by_id_and_owner(self, session: AsyncSession) -> None:
        """A document is found by its id and owner."""
        owner_id = await _create_user(session)
        space_id = await _create_study_space(session, owner_id)
        await session.commit()

        repo = PostgresStudyDocumentRepository(session)
        doc = StudyDocument.create(
            id=uuid.uuid4(),
            filename="test.pdf",
            content_type="application/pdf",
            storage_path="study_documents/test.pdf",
            owner_user_id=owner_id,
            study_space_id=space_id,
        )
        await repo.save(doc)
        await session.commit()

        found = await repo.find_by_id_and_owner(doc.id, owner_id)

        assert found is not None
        assert found.id == doc.id

    @pytest.mark.asyncio
    async def test_does_not_return_document_for_different_owner(
        self, session: AsyncSession
    ) -> None:
        """A document owned by another user is not found."""
        owner_id = await _create_user(session)
        other_owner = await _create_user(session)
        space_id = await _create_study_space(session, owner_id)
        await session.commit()

        repo = PostgresStudyDocumentRepository(session)
        doc = StudyDocument.create(
            id=uuid.uuid4(),
            filename="test.pdf",
            content_type="application/pdf",
            storage_path="study_documents/test.pdf",
            owner_user_id=owner_id,
            study_space_id=space_id,
        )
        await repo.save(doc)
        await session.commit()

        found = await repo.find_by_id_and_owner(doc.id, other_owner)

        assert found is None

    @pytest.mark.asyncio
    async def test_rejects_null_owner_user_id(self, session: AsyncSession) -> None:
        """Database rejects a document with null owner_user_id."""
        space_owner = await _create_user(session)
        space_id = await _create_study_space(session, space_owner)
        await session.commit()

        repo = PostgresStudyDocumentRepository(session)
        with pytest.raises(Exception):
            await repo.save(
                StudyDocument(
                    id=uuid.uuid4(),
                    filename="orphan.pdf",
                    content_type="application/pdf",
                    storage_path="study_documents/orphan.pdf",
                    owner_user_id=None,  # type: ignore[arg-type]
                    study_space_id=space_id,
                    status="PENDING_PROCESSING",
                    chunks_count=0,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                )
            )

    @pytest.mark.asyncio
    async def test_rejects_null_study_space_id(self, session: AsyncSession) -> None:
        """Database rejects a document with null study_space_id."""
        owner_id = await _create_user(session)
        await session.commit()

        repo = PostgresStudyDocumentRepository(session)
        with pytest.raises(Exception):
            await repo.save(
                StudyDocument(
                    id=uuid.uuid4(),
                    filename="spaceless.pdf",
                    content_type="application/pdf",
                    storage_path="study_documents/spaceless.pdf",
                    owner_user_id=owner_id,
                    study_space_id=None,  # type: ignore[arg-type]
                    status="PENDING_PROCESSING",
                    chunks_count=0,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                )
            )

    @pytest.mark.asyncio
    async def test_finds_documents_by_study_space_id_and_owner(
        self, session: AsyncSession
    ) -> None:
        """Documents are found by study space and owner."""
        owner_id = await _create_user(session)
        space_id = await _create_study_space(session, owner_id)
        other_space = await _create_study_space(session, owner_id)
        await session.commit()

        repo = PostgresStudyDocumentRepository(session)
        doc1 = StudyDocument.create(
            id=uuid.uuid4(),
            filename="doc1.pdf",
            content_type="application/pdf",
            storage_path="study_documents/doc1.pdf",
            owner_user_id=owner_id,
            study_space_id=space_id,
        )
        doc2 = StudyDocument.create(
            id=uuid.uuid4(),
            filename="doc2.pdf",
            content_type="application/pdf",
            storage_path="study_documents/doc2.pdf",
            owner_user_id=owner_id,
            study_space_id=space_id,
        )
        doc_other = StudyDocument.create(
            id=uuid.uuid4(),
            filename="other.pdf",
            content_type="application/pdf",
            storage_path="study_documents/other.pdf",
            owner_user_id=owner_id,
            study_space_id=other_space,
        )
        await repo.save(doc1)
        await repo.save(doc2)
        await repo.save(doc_other)
        await session.commit()

        found = await repo.find_by_study_space_id_and_owner(space_id, owner_id)

        assert len(found) == 2
        ids = {d.id for d in found}
        assert doc1.id in ids
        assert doc2.id in ids
        assert doc_other.id not in ids

    @pytest.mark.asyncio
    async def test_find_by_space_excludes_documents_from_other_owners(
        self, session: AsyncSession
    ) -> None:
        """Documents owned by another user in the same space are excluded."""
        owner1 = await _create_user(session)
        owner2 = await _create_user(session)
        space1 = await _create_study_space(session, owner1)
        await session.commit()

        repo = PostgresStudyDocumentRepository(session)
        doc_owner1 = StudyDocument.create(
            id=uuid.uuid4(),
            filename="mine.pdf",
            content_type="application/pdf",
            storage_path="study_documents/mine.pdf",
            owner_user_id=owner1,
            study_space_id=space1,
        )
        doc_owner2 = StudyDocument.create(
            id=uuid.uuid4(),
            filename="theirs.pdf",
            content_type="application/pdf",
            storage_path="study_documents/theirs.pdf",
            owner_user_id=owner2,
            study_space_id=space1,
        )
        await repo.save(doc_owner1)
        await repo.save(doc_owner2)
        await session.commit()

        found = await repo.find_by_study_space_id_and_owner(space1, owner1)

        assert len(found) == 1
        assert found[0].id == doc_owner1.id


@pytest.mark.integration
class TestPostgresStudyDocumentChunkRepository:
    """Integration tests for PostgresStudyDocumentChunkRepository."""

    @pytest.mark.asyncio
    async def test_saves_and_finds_chunks_by_document_id(
        self, session: AsyncSession
    ) -> None:
        """Saved chunks are retrievable by document id."""
        owner_id = await _create_user(session)
        space_id = await _create_study_space(session, owner_id)
        await session.commit()

        doc_repo = PostgresStudyDocumentRepository(session)
        doc = StudyDocument.create(
            id=uuid.uuid4(),
            filename="test.pdf",
            content_type="application/pdf",
            storage_path="study_documents/test.pdf",
            owner_user_id=owner_id,
            study_space_id=space_id,
        )
        await doc_repo.save(doc)
        await session.commit()

        chunk_repo = PostgresStudyDocumentChunkRepository(session)
        chunk = StudyDocumentChunk.create(
            id=uuid.uuid4(),
            document_id=doc.id,
            text="Derecho administrativo regula la administración pública.",
            sequence_number=1,
            page_number=1,
            embedding=[0.1] * 384,
            embedding_model="test-model",
        )
        await chunk_repo.save(chunk)
        await session.commit()

        found = await chunk_repo.find_by_document_id(doc.id)

        assert len(found) == 1
        assert found[0].text == chunk.text
        assert found[0].sequence_number == 1
        assert found[0].page_number == 1

    @pytest.mark.asyncio
    async def test_replaces_chunks_by_document_id(self, session: AsyncSession) -> None:
        """Saving chunks for a document replaces any existing chunks."""
        owner_id = await _create_user(session)
        space_id = await _create_study_space(session, owner_id)
        await session.commit()

        doc_repo = PostgresStudyDocumentRepository(session)
        doc = StudyDocument.create(
            id=uuid.uuid4(),
            filename="test.pdf",
            content_type="application/pdf",
            storage_path="study_documents/test.pdf",
            owner_user_id=owner_id,
            study_space_id=space_id,
        )
        await doc_repo.save(doc)
        await session.commit()

        chunk_repo = PostgresStudyDocumentChunkRepository(session)
        chunk1 = StudyDocumentChunk.create(
            id=uuid.uuid4(),
            document_id=doc.id,
            text="Old content.",
            sequence_number=1,
            page_number=1,
            embedding=[0.1] * 384,
            embedding_model="test-model",
        )
        await chunk_repo.save(chunk1)
        await session.commit()

        chunk2 = StudyDocumentChunk.create(
            id=uuid.uuid4(),
            document_id=doc.id,
            text="New content.",
            sequence_number=1,
            page_number=1,
            embedding=[0.4] * 384,
            embedding_model="test-model",
        )
        await chunk_repo.replace_by_document_id(doc.id, [chunk2])
        await session.commit()

        found = await chunk_repo.find_by_document_id(doc.id)

        assert len(found) == 1
        assert found[0].text == "New content."

    @pytest.mark.asyncio
    async def test_returns_empty_list_for_missing_document(
        self, session: AsyncSession
    ) -> None:
        """A document with no chunks returns an empty list."""
        chunk_repo = PostgresStudyDocumentChunkRepository(session)

        found = await chunk_repo.find_by_document_id(uuid.uuid4())

        assert found == []


@pytest.mark.integration
class TestPostgresSemanticChunkSearchRepository:
    """Integration tests for PostgresSemanticChunkSearchRepository."""

    @pytest.mark.asyncio
    async def test_filters_by_owner_id(self, session: AsyncSession) -> None:
        """Search results are filtered by owner_id."""
        owner1 = await _create_user(session)
        owner2 = await _create_user(session)
        space1 = await _create_study_space(session, owner1)
        space2 = await _create_study_space(session, owner2)
        await session.commit()

        doc_repo = PostgresStudyDocumentRepository(session)
        doc1 = StudyDocument.create(
            id=uuid.uuid4(),
            filename="doc1.pdf",
            content_type="application/pdf",
            storage_path="study_documents/doc1.pdf",
            owner_user_id=owner1,
            study_space_id=space1,
        )
        doc1.mark_as_processing()
        doc1.mark_as_ready(chunk_count=1)
        doc2 = StudyDocument.create(
            id=uuid.uuid4(),
            filename="doc2.pdf",
            content_type="application/pdf",
            storage_path="study_documents/doc2.pdf",
            owner_user_id=owner2,
            study_space_id=space2,
        )
        doc2.mark_as_processing()
        doc2.mark_as_ready(chunk_count=1)
        await doc_repo.save(doc1)
        await doc_repo.save(doc2)
        await session.commit()

        chunk_repo = PostgresStudyDocumentChunkRepository(session)
        chunk1 = StudyDocumentChunk.create(
            id=uuid.uuid4(),
            document_id=doc1.id,
            text="Owner1 text.",
            sequence_number=1,
            page_number=1,
            embedding=[0.1] * 384,
            embedding_model="test-model",
        )
        chunk2 = StudyDocumentChunk.create(
            id=uuid.uuid4(),
            document_id=doc2.id,
            text="Owner2 text.",
            sequence_number=1,
            page_number=1,
            embedding=[0.1] * 384,
            embedding_model="test-model",
        )
        await chunk_repo.save(chunk1)
        await chunk_repo.save(chunk2)
        await session.commit()

        search_repo = PostgresSemanticChunkSearchRepository(session)
        results = await search_repo.find_nearest_by_embedding(
            embedding=[0.1] * 384,
            limit=10,
            owner_id=owner1,
        )

        assert len(results) == 1
        assert results[0].document_id == doc1.id

    @pytest.mark.asyncio
    async def test_filters_by_study_space_id(self, session: AsyncSession) -> None:
        """Search results are filtered by study_space_id."""
        owner = await _create_user(session)
        space_a = await _create_study_space(session, owner)
        space_b = await _create_study_space(session, owner)
        await session.commit()

        doc_repo = PostgresStudyDocumentRepository(session)
        doc_a = StudyDocument.create(
            id=uuid.uuid4(),
            filename="a.pdf",
            content_type="application/pdf",
            storage_path="study_documents/a.pdf",
            owner_user_id=owner,
            study_space_id=space_a,
        )
        doc_a.mark_as_processing()
        doc_a.mark_as_ready(chunk_count=1)
        doc_b = StudyDocument.create(
            id=uuid.uuid4(),
            filename="b.pdf",
            content_type="application/pdf",
            storage_path="study_documents/b.pdf",
            owner_user_id=owner,
            study_space_id=space_b,
        )
        doc_b.mark_as_processing()
        doc_b.mark_as_ready(chunk_count=1)
        await doc_repo.save(doc_a)
        await doc_repo.save(doc_b)
        await session.commit()

        chunk_repo = PostgresStudyDocumentChunkRepository(session)
        chunk_a = StudyDocumentChunk.create(
            id=uuid.uuid4(),
            document_id=doc_a.id,
            text="Space A content.",
            sequence_number=1,
            page_number=1,
            embedding=[0.1] * 384,
            embedding_model="test-model",
        )
        chunk_b = StudyDocumentChunk.create(
            id=uuid.uuid4(),
            document_id=doc_b.id,
            text="Space B content.",
            sequence_number=1,
            page_number=1,
            embedding=[0.1] * 384,
            embedding_model="test-model",
        )
        await chunk_repo.save(chunk_a)
        await chunk_repo.save(chunk_b)
        await session.commit()

        search_repo = PostgresSemanticChunkSearchRepository(session)
        results = await search_repo.find_nearest_by_embedding(
            embedding=[0.1] * 384,
            limit=10,
            owner_id=owner,
            study_space_id=space_a,
        )

        assert len(results) == 1
        assert results[0].document_id == doc_a.id
