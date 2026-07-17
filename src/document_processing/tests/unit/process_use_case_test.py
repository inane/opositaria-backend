"""Unit tests for ProcessStudyDocumentUseCase."""

import uuid
from dataclasses import dataclass, field

import pytest

from src.document_processing.application.use_cases import ProcessStudyDocumentUseCase
from src.document_processing.domain.entities import DocumentProcessingJob
from src.document_processing.domain.repositories import (
    InMemoryDocumentProcessingJobRepository,
)
from src.study_documents.domain.entities import (
    StudyDocument,
    StudyDocumentChunk,
    StudyDocumentError,
)
from src.study_documents.domain.repositories import (
    InMemoryStudyDocumentChunkRepository,
    InMemoryStudyDocumentRepository,
)


@dataclass
class PdfTextExtractorStub:
    """Stub that returns fixed extracted text or raises an error."""

    text: str | None = "Extracted PDF text content for testing."
    raise_error: Exception | None = None

    async def extract_text(self, storage_path: str) -> str | None:
        if self.raise_error:
            raise self.raise_error
        return self.text


@dataclass
class TextChunkerStub:
    """Stub that returns fixed chunks."""

    chunks: list[tuple[str, int | None]] = field(
        default_factory=lambda: [
            ("First chunk of text.", 1),
            ("Second chunk of text.", 1),
            ("Third chunk of text.", 2),
        ]
    )

    async def chunk_text(self, text: str) -> list[tuple[str, int | None]]:
        return self.chunks


@dataclass
class EmbeddingGeneratorStub:
    """Stub that returns a fixed-dimension embedding."""

    dimension: int = 384
    should_fail: bool = False

    async def generate(self, text: str) -> list[float]:
        if self.should_fail:
            raise RuntimeError("Embedding model failed to load")
        return [0.1] * self.dimension


class TestProcessStudyDocumentUseCase:
    """Tests for ProcessStudyDocumentUseCase."""

    @pytest.mark.asyncio
    async def test_processes_pending_job_to_ready_with_persisted_chunks(self) -> None:
        """A pending job is processed to READY with chunks persisted."""
        doc_repo = InMemoryStudyDocumentRepository()
        chunk_repo = InMemoryStudyDocumentChunkRepository()
        job_repo = InMemoryDocumentProcessingJobRepository()

        document_id = uuid.uuid4()
        job_id = uuid.uuid4()
        doc = StudyDocument.create(
            id=document_id,
            filename="test.pdf",
            content_type="application/pdf",
            storage_path="study_documents/test.pdf",
            owner_user_id=uuid.uuid4(),
            study_space_id=uuid.uuid4(),
        )
        job = DocumentProcessingJob.create(id=job_id, document_id=document_id)
        await doc_repo.save(doc)
        await job_repo.save(job)

        use_case = ProcessStudyDocumentUseCase(
            document_repository=doc_repo,
            chunk_repository=chunk_repo,
            job_repository=job_repo,
            pdf_extractor=PdfTextExtractorStub(),
            text_chunker=TextChunkerStub(),
            embedding_generator=EmbeddingGeneratorStub(),
        )

        await use_case.execute(job_id=job_id)

        # Document is READY
        processed_doc = await doc_repo.find_by_id(document_id)
        assert processed_doc is not None
        assert processed_doc.status == "READY"
        assert processed_doc.chunks_count == 3

        # Job is COMPLETED
        processed_job = await job_repo.find_by_id(job_id)
        assert processed_job is not None
        assert processed_job.status == "COMPLETED"

        # Chunks are persisted
        chunks = await chunk_repo.find_by_document_id(document_id)
        assert len(chunks) == 3
        assert chunks[0].sequence_number == 1
        assert chunks[0].text == "First chunk of text."
        assert chunks[0].page_number == 1

    @pytest.mark.asyncio
    async def test_completes_full_lifecycle_transition_from_pending_to_ready(
        self,
    ) -> None:
        """A document transitions fully through PENDING to READY without state errors."""
        doc_repo = InMemoryStudyDocumentRepository()
        chunk_repo = InMemoryStudyDocumentChunkRepository()
        job_repo = InMemoryDocumentProcessingJobRepository()

        document_id = uuid.uuid4()
        job_id = uuid.uuid4()
        doc = StudyDocument.create(
            id=document_id,
            filename="test.pdf",
            content_type="application/pdf",
            storage_path="study_documents/test.pdf",
            owner_user_id=uuid.uuid4(),
            study_space_id=uuid.uuid4(),
        )
        job = DocumentProcessingJob.create(id=job_id, document_id=document_id)
        await doc_repo.save(doc)
        await job_repo.save(job)

        use_case = ProcessStudyDocumentUseCase(
            document_repository=doc_repo,
            chunk_repository=chunk_repo,
            job_repository=job_repo,
            pdf_extractor=PdfTextExtractorStub(),
            text_chunker=TextChunkerStub(),
            embedding_generator=EmbeddingGeneratorStub(),
        )

        await use_case.execute(job_id=job_id)

        # Entities were modified in-place through the repo
        assert doc.status == "READY"
        assert job.status == "COMPLETED"

    @pytest.mark.asyncio
    async def test_fails_document_when_pdf_has_no_usable_text(self) -> None:
        """A PDF with no extractable text results in a failed document and job."""
        doc_repo = InMemoryStudyDocumentRepository()
        chunk_repo = InMemoryStudyDocumentChunkRepository()
        job_repo = InMemoryDocumentProcessingJobRepository()

        document_id = uuid.uuid4()
        job_id = uuid.uuid4()
        doc = StudyDocument.create(
            id=document_id,
            filename="test.pdf",
            content_type="application/pdf",
            storage_path="study_documents/test.pdf",
            owner_user_id=uuid.uuid4(),
            study_space_id=uuid.uuid4(),
        )
        job = DocumentProcessingJob.create(id=job_id, document_id=document_id)
        await doc_repo.save(doc)
        await job_repo.save(job)

        use_case = ProcessStudyDocumentUseCase(
            document_repository=doc_repo,
            chunk_repository=chunk_repo,
            job_repository=job_repo,
            pdf_extractor=PdfTextExtractorStub(text=None),
            text_chunker=TextChunkerStub(),
            embedding_generator=EmbeddingGeneratorStub(),
        )

        await use_case.execute(job_id=job_id)

        processed_doc = await doc_repo.find_by_id(document_id)
        assert processed_doc is not None
        assert processed_doc.status == "FAILED"
        assert processed_doc.failure_reason == "no_extractable_text"

        processed_job = await job_repo.find_by_id(job_id)
        assert processed_job is not None
        assert processed_job.status == "FAILED"

    @pytest.mark.asyncio
    async def test_fails_document_when_pdf_cannot_be_read(self) -> None:
        """An unreadable PDF file marks the document and job failed with code pdf_cannot_be_read and persists no chunks."""
        doc_repo = InMemoryStudyDocumentRepository()
        chunk_repo = InMemoryStudyDocumentChunkRepository()
        job_repo = InMemoryDocumentProcessingJobRepository()

        document_id = uuid.uuid4()
        job_id = uuid.uuid4()
        doc = StudyDocument.create(
            id=document_id,
            filename="test.pdf",
            content_type="application/pdf",
            storage_path="study_documents/test.pdf",
            owner_user_id=uuid.uuid4(),
            study_space_id=uuid.uuid4(),
        )
        job = DocumentProcessingJob.create(id=job_id, document_id=document_id)
        await doc_repo.save(doc)
        await job_repo.save(job)

        use_case = ProcessStudyDocumentUseCase(
            document_repository=doc_repo,
            chunk_repository=chunk_repo,
            job_repository=job_repo,
            pdf_extractor=PdfTextExtractorStub(
                raise_error=StudyDocumentError(
                    "The PDF file could not be read",
                    safe=True,
                    code="pdf_cannot_be_read",
                ),
            ),
            text_chunker=TextChunkerStub(),
            embedding_generator=EmbeddingGeneratorStub(),
        )

        await use_case.execute(job_id=job_id)

        processed_doc = await doc_repo.find_by_id(document_id)
        assert processed_doc is not None
        assert processed_doc.status == "FAILED"
        assert processed_doc.failure_reason == "pdf_cannot_be_read"

        processed_job = await job_repo.find_by_id(job_id)
        assert processed_job is not None
        assert processed_job.status == "FAILED"
        assert processed_job.failure_reason == "pdf_cannot_be_read"

        # No chunks were persisted
        chunks = await chunk_repo.find_by_document_id(document_id)
        assert len(chunks) == 0

    @pytest.mark.asyncio
    async def test_fails_document_when_pdf_is_encrypted(self) -> None:
        """An encrypted PDF marks the document and job failed with code encrypted_pdf and persists no chunks."""
        doc_repo = InMemoryStudyDocumentRepository()
        chunk_repo = InMemoryStudyDocumentChunkRepository()
        job_repo = InMemoryDocumentProcessingJobRepository()

        document_id = uuid.uuid4()
        job_id = uuid.uuid4()
        doc = StudyDocument.create(
            id=document_id,
            filename="test.pdf",
            content_type="application/pdf",
            storage_path="study_documents/test.pdf",
            owner_user_id=uuid.uuid4(),
            study_space_id=uuid.uuid4(),
        )
        job = DocumentProcessingJob.create(id=job_id, document_id=document_id)
        await doc_repo.save(doc)
        await job_repo.save(job)

        use_case = ProcessStudyDocumentUseCase(
            document_repository=doc_repo,
            chunk_repository=chunk_repo,
            job_repository=job_repo,
            pdf_extractor=PdfTextExtractorStub(
                raise_error=StudyDocumentError(
                    "The PDF is encrypted",
                    safe=True,
                    code="encrypted_pdf",
                ),
            ),
            text_chunker=TextChunkerStub(),
            embedding_generator=EmbeddingGeneratorStub(),
        )

        await use_case.execute(job_id=job_id)

        processed_doc = await doc_repo.find_by_id(document_id)
        assert processed_doc is not None
        assert processed_doc.status == "FAILED"
        assert processed_doc.failure_reason == "encrypted_pdf"

        processed_job = await job_repo.find_by_id(job_id)
        assert processed_job is not None
        assert processed_job.status == "FAILED"
        assert processed_job.failure_reason == "encrypted_pdf"

        # No chunks were persisted
        chunks = await chunk_repo.find_by_document_id(document_id)
        assert len(chunks) == 0

    @pytest.mark.asyncio
    async def test_fails_document_when_chunker_returns_no_chunks(self) -> None:
        """A text chunker returning no chunks results in a failed document and job."""
        doc_repo = InMemoryStudyDocumentRepository()
        chunk_repo = InMemoryStudyDocumentChunkRepository()
        job_repo = InMemoryDocumentProcessingJobRepository()

        document_id = uuid.uuid4()
        job_id = uuid.uuid4()
        doc = StudyDocument.create(
            id=document_id,
            filename="test.pdf",
            content_type="application/pdf",
            storage_path="study_documents/test.pdf",
            owner_user_id=uuid.uuid4(),
            study_space_id=uuid.uuid4(),
        )
        job = DocumentProcessingJob.create(id=job_id, document_id=document_id)
        await doc_repo.save(doc)
        await job_repo.save(job)

        chunker = TextChunkerStub()
        chunker.chunks = []

        use_case = ProcessStudyDocumentUseCase(
            document_repository=doc_repo,
            chunk_repository=chunk_repo,
            job_repository=job_repo,
            pdf_extractor=PdfTextExtractorStub(),
            text_chunker=chunker,
            embedding_generator=EmbeddingGeneratorStub(),
        )

        await use_case.execute(job_id=job_id)

        processed_doc = await doc_repo.find_by_id(document_id)
        assert processed_doc is not None
        assert processed_doc.status == "FAILED"

    @pytest.mark.asyncio
    async def test_fails_document_when_embedding_generation_fails(self) -> None:
        """An embedding generator failure results in a failed document and job with a sanitized reason."""
        doc_repo = InMemoryStudyDocumentRepository()
        chunk_repo = InMemoryStudyDocumentChunkRepository()
        job_repo = InMemoryDocumentProcessingJobRepository()

        document_id = uuid.uuid4()
        job_id = uuid.uuid4()
        doc = StudyDocument.create(
            id=document_id,
            filename="test.pdf",
            content_type="application/pdf",
            storage_path="study_documents/test.pdf",
            owner_user_id=uuid.uuid4(),
            study_space_id=uuid.uuid4(),
        )
        job = DocumentProcessingJob.create(id=job_id, document_id=document_id)
        await doc_repo.save(doc)
        await job_repo.save(job)

        use_case = ProcessStudyDocumentUseCase(
            document_repository=doc_repo,
            chunk_repository=chunk_repo,
            job_repository=job_repo,
            pdf_extractor=PdfTextExtractorStub(),
            text_chunker=TextChunkerStub(),
            embedding_generator=EmbeddingGeneratorStub(should_fail=True),
        )

        await use_case.execute(job_id=job_id)

        processed_doc = await doc_repo.find_by_id(document_id)
        assert processed_doc is not None
        assert processed_doc.status == "FAILED"
        # Failure reason is sanitized, not raw exception text
        assert (
            processed_doc.failure_reason
            == "Document processing failed due to an internal error"
        )

        processed_job = await job_repo.find_by_id(job_id)
        assert processed_job is not None
        assert processed_job.status == "FAILED"
        assert (
            processed_job.failure_reason
            == "Document processing failed due to an internal error"
        )

    @pytest.mark.asyncio
    async def test_fails_document_on_embedding_dimension_mismatch(self) -> None:
        """An embedding dimension mismatch fails the document without persisting chunks."""
        doc_repo = InMemoryStudyDocumentRepository()
        chunk_repo = InMemoryStudyDocumentChunkRepository()
        job_repo = InMemoryDocumentProcessingJobRepository()

        document_id = uuid.uuid4()
        job_id = uuid.uuid4()
        doc = StudyDocument.create(
            id=document_id,
            filename="test.pdf",
            content_type="application/pdf",
            storage_path="study_documents/test.pdf",
            owner_user_id=uuid.uuid4(),
            study_space_id=uuid.uuid4(),
        )
        job = DocumentProcessingJob.create(id=job_id, document_id=document_id)
        await doc_repo.save(doc)
        await job_repo.save(job)

        use_case = ProcessStudyDocumentUseCase(
            document_repository=doc_repo,
            chunk_repository=chunk_repo,
            job_repository=job_repo,
            pdf_extractor=PdfTextExtractorStub(),
            text_chunker=TextChunkerStub(),
            embedding_generator=EmbeddingGeneratorStub(dimension=128),
        )

        await use_case.execute(job_id=job_id)

        processed_doc = await doc_repo.find_by_id(document_id)
        assert processed_doc is not None
        assert processed_doc.status == "FAILED"
        # Failure reason is sanitized, not exposing dimension config details
        assert (
            processed_doc.failure_reason
            == "Document processing failed due to an internal error"
        )

        processed_job = await job_repo.find_by_id(job_id)
        assert processed_job is not None
        assert processed_job.status == "FAILED"
        assert (
            processed_job.failure_reason
            == "Document processing failed due to an internal error"
        )

        # No chunks should be persisted
        chunks = await chunk_repo.find_by_document_id(document_id)
        assert len(chunks) == 0

    @pytest.mark.asyncio
    async def test_ignores_duplicate_completed_job(self) -> None:
        """A duplicate completed job message is acknowledged without duplicating chunks."""
        doc_repo = InMemoryStudyDocumentRepository()
        chunk_repo = InMemoryStudyDocumentChunkRepository()
        job_repo = InMemoryDocumentProcessingJobRepository()

        document_id = uuid.uuid4()
        job_id = uuid.uuid4()
        doc = StudyDocument.create(
            id=document_id,
            filename="test.pdf",
            content_type="application/pdf",
            storage_path="study_documents/test.pdf",
            owner_user_id=uuid.uuid4(),
            study_space_id=uuid.uuid4(),
        )
        doc.mark_as_processing()
        doc.mark_as_ready(chunk_count=2)
        job = DocumentProcessingJob.create(id=job_id, document_id=document_id)
        job.mark_as_running()
        job.mark_as_completed()
        await doc_repo.save(doc)
        await job_repo.save(job)

        use_case = ProcessStudyDocumentUseCase(
            document_repository=doc_repo,
            chunk_repository=chunk_repo,
            job_repository=job_repo,
            pdf_extractor=PdfTextExtractorStub(),
            text_chunker=TextChunkerStub(),
            embedding_generator=EmbeddingGeneratorStub(),
        )

        await use_case.execute(job_id=job_id)

        processed_job = await job_repo.find_by_id(job_id)
        assert processed_job is not None
        assert processed_job.status == "COMPLETED"

    @pytest.mark.asyncio
    async def test_replaces_existing_chunks_during_reprocessing(self) -> None:
        """Existing chunks for a document are replaced during reprocessing."""
        doc_repo = InMemoryStudyDocumentRepository()
        chunk_repo = InMemoryStudyDocumentChunkRepository()
        job_repo = InMemoryDocumentProcessingJobRepository()

        document_id = uuid.uuid4()
        job_id = uuid.uuid4()
        doc = StudyDocument.create(
            id=document_id,
            filename="test.pdf",
            content_type="application/pdf",
            storage_path="study_documents/test.pdf",
            owner_user_id=uuid.uuid4(),
            study_space_id=uuid.uuid4(),
        )
        job = DocumentProcessingJob.create(id=job_id, document_id=document_id)
        await doc_repo.save(doc)
        await job_repo.save(job)

        # Add old chunk
        old_chunk = StudyDocumentChunk.create(
            id=uuid.uuid4(),
            document_id=document_id,
            text="Old chunk",
            sequence_number=1,
            embedding=[0.1] * 384,
            embedding_model="test",
        )
        await chunk_repo.save(old_chunk)

        use_case = ProcessStudyDocumentUseCase(
            document_repository=doc_repo,
            chunk_repository=chunk_repo,
            job_repository=job_repo,
            pdf_extractor=PdfTextExtractorStub(),
            text_chunker=TextChunkerStub(),
            embedding_generator=EmbeddingGeneratorStub(),
        )

        await use_case.execute(job_id=job_id)

        chunks = await chunk_repo.find_by_document_id(document_id)
        assert len(chunks) == 3
        assert all(c.text != "Old chunk" for c in chunks)

    @pytest.mark.asyncio
    async def test_preserves_chunk_sequence_and_page_metadata(self) -> None:
        """Chunk sequence and page metadata from extraction/chunking are preserved."""
        doc_repo = InMemoryStudyDocumentRepository()
        chunk_repo = InMemoryStudyDocumentChunkRepository()
        job_repo = InMemoryDocumentProcessingJobRepository()

        document_id = uuid.uuid4()
        job_id = uuid.uuid4()
        doc = StudyDocument.create(
            id=document_id,
            filename="test.pdf",
            content_type="application/pdf",
            storage_path="study_documents/test.pdf",
            owner_user_id=uuid.uuid4(),
            study_space_id=uuid.uuid4(),
        )
        job = DocumentProcessingJob.create(id=job_id, document_id=document_id)
        await doc_repo.save(doc)
        await job_repo.save(job)

        chunker = TextChunkerStub()
        chunker.chunks = [
            ("Page 1 text.", 1),
            ("Page 2 text.", 2),
        ]

        use_case = ProcessStudyDocumentUseCase(
            document_repository=doc_repo,
            chunk_repository=chunk_repo,
            job_repository=job_repo,
            pdf_extractor=PdfTextExtractorStub(),
            text_chunker=chunker,
            embedding_generator=EmbeddingGeneratorStub(),
        )

        await use_case.execute(job_id=job_id)

        chunks = await chunk_repo.find_by_document_id(document_id)
        assert len(chunks) == 2
        assert chunks[0].sequence_number == 1
        assert chunks[0].text == "Page 1 text."
        assert chunks[0].page_number == 1
        assert chunks[1].sequence_number == 2
        assert chunks[1].text == "Page 2 text."
        assert chunks[1].page_number == 2
