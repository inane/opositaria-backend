"""Unit tests for study document use cases."""

import uuid
from dataclasses import dataclass, field

import pytest

from src.document_processing.domain.repositories import (
    InMemoryDocumentProcessingJobRepository,
)
from src.study_documents.application.dtos import (
    UploadDocumentResponse,
)
from src.study_documents.application.use_cases import (
    GetStudyDocumentStatusUseCase,
    UploadStudyDocumentUseCase,
)
from src.study_documents.domain.entities import StudyDocument, StudyDocumentError
from src.study_documents.domain.repositories import InMemoryStudyDocumentRepository


@dataclass
class DocumentStorageSpy:
    """Spy that records storage calls and returns a fixed path."""

    saved: list[tuple[uuid.UUID, str, bytes]] = field(default_factory=list)
    storage_path: str = "study_documents/test.pdf"

    async def save(self, document_id: uuid.UUID, filename: str, content: bytes) -> str:
        self.saved.append((document_id, filename, content))
        return self.storage_path


@dataclass
class PublisherSpy:
    """Spy that records publish calls."""

    published: list[tuple[uuid.UUID, uuid.UUID]] = field(default_factory=list)
    should_fail: bool = False

    async def publish(self, document_id: uuid.UUID, job_id: uuid.UUID) -> None:
        if self.should_fail:
            raise RuntimeError("RabbitMQ connection failed")
        self.published.append((document_id, job_id))


class TestUploadStudyDocumentUseCase:
    """Tests for UploadStudyDocumentUseCase."""

    @pytest.mark.asyncio
    async def test_uploads_pdf_creates_pending_document_and_publishes_job(self) -> None:
        """Uploading a valid PDF creates a pending document, stores file, persists job, publishes message, and returns status."""
        doc_repo = InMemoryStudyDocumentRepository()
        job_repo = InMemoryDocumentProcessingJobRepository()
        storage = DocumentStorageSpy()
        publisher = PublisherSpy()
        use_case = UploadStudyDocumentUseCase(
            document_repository=doc_repo,
            document_storage=storage,
            publisher=publisher,
            job_repository=job_repo,
        )

        response = await use_case.execute(
            filename="test.pdf",
            content_type="application/pdf",
            content=b"%PDF-1.4 test content",
        )

        assert isinstance(response, UploadDocumentResponse)
        assert response.status == "PENDING_PROCESSING"

        # Document was persisted
        doc = await doc_repo.find_by_id(response.document_id)
        assert doc is not None
        assert doc.filename == "test.pdf"
        assert doc.status == "PENDING_PROCESSING"

        # File was stored
        assert len(storage.saved) == 1
        assert storage.saved[0][1] == "test.pdf"

        # Processing job was persisted in PENDING state
        assert len(publisher.published) == 1
        published_job_id = publisher.published[0][1]
        job = await job_repo.find_by_id(published_job_id)
        assert job is not None
        assert job.document_id == response.document_id
        assert job.status == "PENDING"

        # Message was published
        assert len(publisher.published) == 1

    @pytest.mark.asyncio
    async def test_rejects_non_pdf_upload_without_storing_or_publishing(self) -> None:
        """A non-PDF upload is rejected without storing file, creating document, or publishing."""
        doc_repo = InMemoryStudyDocumentRepository()
        job_repo = InMemoryDocumentProcessingJobRepository()
        storage = DocumentStorageSpy()
        publisher = PublisherSpy()
        use_case = UploadStudyDocumentUseCase(
            document_repository=doc_repo,
            document_storage=storage,
            publisher=publisher,
            job_repository=job_repo,
        )

        with pytest.raises(StudyDocumentError, match="Only PDF files are accepted"):
            await use_case.execute(
                filename="notes.txt",
                content_type="text/plain",
                content=b"not a pdf",
            )

        assert len(storage.saved) == 0
        assert len(publisher.published) == 0

    @pytest.mark.asyncio
    async def test_rejects_empty_upload(self) -> None:
        """An empty upload is rejected."""
        doc_repo = InMemoryStudyDocumentRepository()
        job_repo = InMemoryDocumentProcessingJobRepository()
        storage = DocumentStorageSpy()
        publisher = PublisherSpy()
        use_case = UploadStudyDocumentUseCase(
            document_repository=doc_repo,
            document_storage=storage,
            publisher=publisher,
            job_repository=job_repo,
        )

        with pytest.raises(StudyDocumentError, match="content is empty"):
            await use_case.execute(
                filename="empty.pdf",
                content_type="application/pdf",
                content=b"",
            )

        assert len(storage.saved) == 0
        assert len(publisher.published) == 0

    @pytest.mark.asyncio
    async def test_keeps_document_and_job_recoverable_on_publisher_failure(self) -> None:
        """When publishing fails, the document and job remain persisted in a recoverable state."""
        doc_repo = InMemoryStudyDocumentRepository()
        job_repo = InMemoryDocumentProcessingJobRepository()
        storage = DocumentStorageSpy()
        publisher = PublisherSpy(should_fail=True)
        use_case = UploadStudyDocumentUseCase(
            document_repository=doc_repo,
            document_storage=storage,
            publisher=publisher,
            job_repository=job_repo,
        )

        with pytest.raises(RuntimeError, match="RabbitMQ connection failed"):
            await use_case.execute(
                filename="test.pdf",
                content_type="application/pdf",
                content=b"%PDF-1.4 valid content",
            )

        # File was stored before publish attempt
        assert len(storage.saved) == 1

        # Document was persisted before publish attempt
        doc = await doc_repo.find_by_id(storage.saved[0][0])
        assert doc is not None
        assert doc.status == "PENDING_PROCESSING"


class TestGetStudyDocumentStatusUseCase:
    """Tests for GetStudyDocumentStatusUseCase."""

    @pytest.mark.asyncio
    async def test_returns_pending_status_for_existing_document(self) -> None:
        """A pending document returns PENDING_PROCESSING status."""
        doc_repo = InMemoryStudyDocumentRepository()
        use_case = GetStudyDocumentStatusUseCase(document_repository=doc_repo)
        doc = StudyDocument.create(
            id=uuid.uuid4(),
            filename="test.pdf",
            content_type="application/pdf",
            storage_path="study_documents/test.pdf",
        )
        await doc_repo.save(doc)

        response = await use_case.execute(doc.id)

        assert response.status == "PENDING_PROCESSING"
        assert response.filename == "test.pdf"

    @pytest.mark.asyncio
    async def test_returns_ready_status_with_chunk_count(self) -> None:
        """A ready document returns READY status with chunk count."""
        doc_repo = InMemoryStudyDocumentRepository()
        use_case = GetStudyDocumentStatusUseCase(document_repository=doc_repo)
        doc = StudyDocument.create(
            id=uuid.uuid4(),
            filename="test.pdf",
            content_type="application/pdf",
            storage_path="study_documents/test.pdf",
        )
        doc.mark_as_processing()
        doc.mark_as_ready(chunk_count=5)
        await doc_repo.save(doc)

        response = await use_case.execute(doc.id)

        assert response.status == "READY"
        assert response.chunks_count == 5

    @pytest.mark.asyncio
    async def test_returns_failed_status_with_failure_reason(self) -> None:
        """A failed document returns FAILED status with a safe failure reason."""
        doc_repo = InMemoryStudyDocumentRepository()
        use_case = GetStudyDocumentStatusUseCase(document_repository=doc_repo)
        doc = StudyDocument.create(
            id=uuid.uuid4(),
            filename="test.pdf",
            content_type="application/pdf",
            storage_path="study_documents/test.pdf",
        )
        doc.mark_as_failed(failure_reason="No extractable text found")
        await doc_repo.save(doc)

        response = await use_case.execute(doc.id)

        assert response.status == "FAILED"
        assert response.failure_reason == "No extractable text found"

    @pytest.mark.asyncio
    async def test_raises_not_found_for_missing_document(self) -> None:
        """A missing document raises a not found error."""
        doc_repo = InMemoryStudyDocumentRepository()
        use_case = GetStudyDocumentStatusUseCase(document_repository=doc_repo)

        with pytest.raises(StudyDocumentError, match="Document not found"):
            await use_case.execute(uuid.uuid4())
