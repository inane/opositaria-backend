"""Integration tests for PostgreSQL study document and chunk repositories."""

import uuid

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.document_processing.domain.entities import DocumentProcessingJob
from src.document_processing.infrastructure.repositories import (
    PostgresDocumentProcessingJobRepository,
)
from src.study_documents.domain.entities import StudyDocument, StudyDocumentChunk
from src.study_documents.infrastructure.repositories import (
    PostgresSemanticChunkSearchRepository,
    PostgresStudyDocumentChunkRepository,
    PostgresStudyDocumentRepository,
)


@pytest.mark.integration
class TestPostgresStudyDocumentRepository:
    """Integration tests for PostgresStudyDocumentRepository."""

    @pytest.mark.asyncio
    async def test_saves_and_finds_document_by_id(self, session: AsyncSession) -> None:
        """A saved document is retrievable by its identifier."""
        repo = PostgresStudyDocumentRepository(session)
        doc = StudyDocument.create(
            id=uuid.uuid4(),
            filename="test.pdf",
            content_type="application/pdf",
            storage_path="study_documents/test.pdf",
        )

        await repo.save(doc)
        await session.commit()

        found = await repo.find_by_id(doc.id)

        assert found is not None
        assert found.filename == "test.pdf"
        assert found.status == "PENDING_PROCESSING"

    @pytest.mark.asyncio
    async def test_updates_document_status(self, session: AsyncSession) -> None:
        """A saved document status can be updated."""
        repo = PostgresStudyDocumentRepository(session)
        doc = StudyDocument.create(
            id=uuid.uuid4(),
            filename="test.pdf",
            content_type="application/pdf",
            storage_path="study_documents/test.pdf",
        )
        await repo.save(doc)
        doc.mark_as_processing()
        await repo.save(doc)
        await session.commit()

        found = await repo.find_by_id(doc.id)

        assert found is not None
        assert found.status == "PROCESSING"


@pytest.mark.integration
class TestPostgresStudyDocumentChunkRepository:
    """Integration tests for PostgresStudyDocumentChunkRepository."""

    @pytest.mark.asyncio
    async def test_saves_and_finds_chunks_by_document_id(
        self, session: AsyncSession
    ) -> None:
        """Saved chunks are retrievable by document id in sequence order."""
        doc_repo = PostgresStudyDocumentRepository(session)
        chunk_repo = PostgresStudyDocumentChunkRepository(session)

        document_id = uuid.uuid4()
        doc = StudyDocument.create(
            id=document_id,
            filename="test.pdf",
            content_type="application/pdf",
            storage_path="study_documents/test.pdf",
        )
        await doc_repo.save(doc)

        chunks = [
            StudyDocumentChunk.create(
                id=uuid.uuid4(),
                document_id=document_id,
                text="Second",
                sequence_number=2,
                embedding=[0.2] * 384,
                embedding_model="test",
            ),
            StudyDocumentChunk.create(
                id=uuid.uuid4(),
                document_id=document_id,
                text="First",
                sequence_number=1,
                embedding=[0.1] * 384,
                embedding_model="test",
            ),
        ]
        for chunk in chunks:
            await chunk_repo.save(chunk)
        await session.commit()

        found = await chunk_repo.find_by_document_id(document_id)

        assert len(found) == 2
        assert found[0].text == "First"
        assert found[0].sequence_number == 1
        assert found[1].text == "Second"
        assert found[1].sequence_number == 2

    @pytest.mark.asyncio
    async def test_replaces_chunks_by_document_id(self, session: AsyncSession) -> None:
        """Replacing chunks for a document removes old chunks and persists new ones."""
        doc_repo = PostgresStudyDocumentRepository(session)
        chunk_repo = PostgresStudyDocumentChunkRepository(session)

        document_id = uuid.uuid4()
        doc = StudyDocument.create(
            id=document_id,
            filename="test.pdf",
            content_type="application/pdf",
            storage_path="study_documents/test.pdf",
        )
        await doc_repo.save(doc)

        old_chunk = StudyDocumentChunk.create(
            id=uuid.uuid4(),
            document_id=document_id,
            text="Old",
            sequence_number=1,
            embedding=[0.1] * 384,
            embedding_model="test",
        )
        await chunk_repo.save(old_chunk)
        await session.commit()

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
        await chunk_repo.replace_by_document_id(document_id, new_chunks)
        await session.commit()

        found = await chunk_repo.find_by_document_id(document_id)
        assert len(found) == 1
        assert found[0].text == "New"


@pytest.mark.integration
class TestPostgresDocumentProcessingJobRepository:
    """Integration tests for PostgresDocumentProcessingJobRepository."""

    @pytest.mark.asyncio
    async def test_saves_and_finds_job_by_id(self, session: AsyncSession) -> None:
        """A saved job is retrievable by its identifier."""
        doc_repo = PostgresStudyDocumentRepository(session)
        job_repo = PostgresDocumentProcessingJobRepository(session)

        document_id = uuid.uuid4()
        doc = StudyDocument.create(
            id=document_id,
            filename="test.pdf",
            content_type="application/pdf",
            storage_path="study_documents/test.pdf",
        )
        await doc_repo.save(doc)

        job = DocumentProcessingJob.create(id=uuid.uuid4(), document_id=document_id)
        await job_repo.save(job)
        await session.commit()

        found = await job_repo.find_by_id(job.id)

        assert found is not None
        assert found.status == "PENDING"
        assert found.document_id == document_id


@pytest.mark.integration
class TestPostgresSemanticChunkSearchRepository:
    """Integration tests for PostgresSemanticChunkSearchRepository."""

    @pytest.mark.asyncio
    async def test_returns_chunks_ordered_by_cosine_distance(
        self, session: AsyncSession
    ) -> None:
        """Semantic search returns chunks ordered by cosine distance, excluding non-ready docs."""
        doc_repo = PostgresStudyDocumentRepository(session)
        chunk_repo = PostgresStudyDocumentChunkRepository(session)
        search_repo = PostgresSemanticChunkSearchRepository(session)

        # Create a READY document with chunks
        ready_doc_id = uuid.uuid4()
        ready_doc = StudyDocument.create(
            id=ready_doc_id,
            filename="ready.pdf",
            content_type="application/pdf",
            storage_path="study_documents/ready.pdf",
        )
        ready_doc.mark_as_processing()
        ready_doc.mark_as_ready(chunk_count=1)
        await doc_repo.save(ready_doc)

        chunk = StudyDocumentChunk.create(
            id=uuid.uuid4(),
            document_id=ready_doc_id,
            text="Legal concepts",
            sequence_number=1,
            embedding=[0.1] * 384,
            embedding_model="test",
        )
        await chunk_repo.save(chunk)

        # Create a non-READY document (should be excluded)
        pending_doc_id = uuid.uuid4()
        pending_doc = StudyDocument.create(
            id=pending_doc_id,
            filename="pending.pdf",
            content_type="application/pdf",
            storage_path="study_documents/pending.pdf",
        )
        await doc_repo.save(pending_doc)

        pending_chunk = StudyDocumentChunk.create(
            id=uuid.uuid4(),
            document_id=pending_doc_id,
            text="Pending content",
            sequence_number=1,
            embedding=[0.5] * 384,
            embedding_model="test",
        )
        await chunk_repo.save(pending_chunk)
        await session.commit()

        query_embedding = [0.1] * 384
        results = await search_repo.find_nearest_by_embedding(query_embedding, limit=10)

        assert len(results) == 1
        assert results[0].document_filename == "ready.pdf"
        assert results[0].text == "Legal concepts"

    @pytest.mark.asyncio
    async def test_pgvector_extension_and_hnsw_index_exist(
        self, session: AsyncSession
    ) -> None:
        """The pgvector extension and HNSW index exist after migrations."""
        result = await session.execute(
            text("SELECT typname FROM pg_type WHERE typname = 'vector'")
        )
        assert result.scalar_one_or_none() == "vector"

        result = await session.execute(
            text(
                "SELECT indexname FROM pg_indexes WHERE indexname = 'ix_study_document_chunks_embedding'"
            )
        )
        assert result.scalar_one_or_none() == "ix_study_document_chunks_embedding"
