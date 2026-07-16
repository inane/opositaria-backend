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
from src.study_documents.domain.entities import (
    MAX_UPLOAD_SIZE_BYTES,
    StudyDocument,
    StudyDocumentError,
)
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

        owner_id = uuid.uuid4()
        response = await use_case.execute(
            filename="test.pdf",
            content_type="application/pdf",
            content=b"%PDF-1.4 test content",
            owner_user_id=owner_id,
        )

        assert isinstance(response, UploadDocumentResponse)
        assert response.status == "PENDING_PROCESSING"

        # Document was persisted with owner
        doc = await doc_repo.find_by_id(response.document_id)
        assert doc is not None
        assert doc.filename == "test.pdf"
        assert doc.status == "PENDING_PROCESSING"
        assert doc.owner_user_id == owner_id

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
        """A non-PDF upload is rejected with code invalid_file_type without storing file, creating document, or publishing."""
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

        with pytest.raises(
            StudyDocumentError, match="Only PDF files are accepted"
        ) as exc:
            await use_case.execute(
                filename="notes.txt",
                content_type="text/plain",
                content=b"not a pdf",
                owner_user_id=uuid.uuid4(),
            )

        assert exc.value.code == "invalid_file_type"
        assert len(storage.saved) == 0
        assert len(publisher.published) == 0

    @pytest.mark.asyncio
    async def test_rejects_invalid_filename_upload_without_storing_or_publishing(
        self,
    ) -> None:
        """An upload with an invalid filename is rejected without storing file, creating document, or publishing."""
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

        with pytest.raises(StudyDocumentError, match="Invalid filename") as exc:
            await use_case.execute(
                filename="../test.pdf",
                content_type="application/pdf",
                content=b"%PDF-1.4 some content",
                owner_user_id=uuid.uuid4(),
            )

        assert exc.value.code == "invalid_filename"
        assert len(storage.saved) == 0
        assert len(publisher.published) == 0

    @pytest.mark.asyncio
    async def test_rejects_empty_upload(self) -> None:
        """An empty upload is rejected with code empty_upload."""
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

        with pytest.raises(StudyDocumentError, match="content is empty") as exc:
            await use_case.execute(
                filename="empty.pdf",
                content_type="application/pdf",
                content=b"",
                owner_user_id=uuid.uuid4(),
            )

        assert exc.value.code == "empty_upload"
        assert len(storage.saved) == 0
        assert len(publisher.published) == 0

    @pytest.mark.asyncio
    async def test_rejects_oversized_upload(self) -> None:
        """An upload larger than 50 MB is rejected with code file_too_large."""
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

        oversized_content = b"x" * (MAX_UPLOAD_SIZE_BYTES + 1)

        with pytest.raises(StudyDocumentError, match="size limit") as exc:
            await use_case.execute(
                filename="large.pdf",
                content_type="application/pdf",
                content=oversized_content,
                owner_user_id=uuid.uuid4(),
            )

        assert exc.value.code == "file_too_large"
        assert len(storage.saved) == 0
        assert len(publisher.published) == 0

    @pytest.mark.asyncio
    async def test_accepts_upload_at_maximum_size(self) -> None:
        """An upload exactly at the 50 MB limit is accepted when PDF validation passes."""
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

        max_content = b"x" * MAX_UPLOAD_SIZE_BYTES

        response = await use_case.execute(
            filename="max-size.pdf",
            content_type="application/pdf",
            content=max_content,
            owner_user_id=uuid.uuid4(),
        )

        assert response.status == "PENDING_PROCESSING"
        assert len(storage.saved) == 1
        assert len(publisher.published) == 1

    @pytest.mark.asyncio
    async def test_keeps_document_and_job_recoverable_on_publisher_failure(
        self,
    ) -> None:
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
                owner_user_id=uuid.uuid4(),
            )

        # File was stored before publish attempt
        assert len(storage.saved) == 1

        # Document was persisted before publish attempt
        doc = await doc_repo.find_by_id(storage.saved[0][0])
        assert doc is not None
        assert doc.status == "PENDING_PROCESSING"


class TestUploadRegressionBehavior:
    """Regression tests for upload behavior."""

    @pytest.mark.asyncio
    async def test_invalid_uploads_do_not_create_documents_or_jobs(self) -> None:
        """Invalid upload requests do not create a study document or processing job."""
        for filename, content_type, content in [
            ("empty.pdf", "application/pdf", b""),
            ("../bad.pdf", "application/pdf", b"%PDF content"),
            ("notes.txt", "text/plain", b"content"),
        ]:
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

            with pytest.raises(StudyDocumentError):
                await use_case.execute(
                    filename=filename,
                    content_type=content_type,
                    content=content,
                    owner_user_id=uuid.uuid4(),
                )

            # No document was created
            all_docs = list(doc_repo._documents.values())
            assert len(all_docs) == 0, f"Expected no documents for {filename}"
            # No job was created
            all_jobs = list(job_repo._jobs.values())
            assert len(all_jobs) == 0, f"Expected no jobs for {filename}"
            # No storage or publishing
            assert len(storage.saved) == 0, f"Expected no storage for {filename}"
            assert len(publisher.published) == 0, (
                f"Expected no publishing for {filename}"
            )


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
            owner_user_id=uuid.uuid4(),
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
            owner_user_id=uuid.uuid4(),
        )
        doc.mark_as_processing()
        doc.mark_as_ready(chunk_count=5)
        await doc_repo.save(doc)

        response = await use_case.execute(doc.id)

        assert response.status == "READY"
        assert response.chunks_count == 5

    @pytest.mark.asyncio
    async def test_returns_failed_status_with_classified_failure_reason(
        self,
    ) -> None:
        """A failed document returns FAILED status with the classified failure code."""
        doc_repo = InMemoryStudyDocumentRepository()
        use_case = GetStudyDocumentStatusUseCase(document_repository=doc_repo)
        doc = StudyDocument.create(
            id=uuid.uuid4(),
            filename="test.pdf",
            content_type="application/pdf",
            storage_path="study_documents/test.pdf",
            owner_user_id=uuid.uuid4(),
        )
        doc.mark_as_failed(failure_reason="no_extractable_text")
        await doc_repo.save(doc)

        response = await use_case.execute(doc.id)

        assert response.status == "FAILED"
        assert response.failure_reason == "no_extractable_text"

    @pytest.mark.asyncio
    async def test_returns_failed_status_with_pdf_cannot_be_read_reason(self) -> None:
        """A failed document due to unreadable PDF returns the classified code."""
        doc_repo = InMemoryStudyDocumentRepository()
        use_case = GetStudyDocumentStatusUseCase(document_repository=doc_repo)
        doc = StudyDocument.create(
            id=uuid.uuid4(),
            filename="test.pdf",
            content_type="application/pdf",
            storage_path="study_documents/test.pdf",
            owner_user_id=uuid.uuid4(),
        )
        doc.mark_as_failed(failure_reason="pdf_cannot_be_read")
        await doc_repo.save(doc)

        response = await use_case.execute(doc.id)

        assert response.status == "FAILED"
        assert response.failure_reason == "pdf_cannot_be_read"

    @pytest.mark.asyncio
    async def test_returns_failed_status_with_encrypted_pdf_reason(self) -> None:
        """A failed document due to encrypted PDF returns the classified code."""
        doc_repo = InMemoryStudyDocumentRepository()
        use_case = GetStudyDocumentStatusUseCase(document_repository=doc_repo)
        doc = StudyDocument.create(
            id=uuid.uuid4(),
            filename="test.pdf",
            content_type="application/pdf",
            storage_path="study_documents/test.pdf",
            owner_user_id=uuid.uuid4(),
        )
        doc.mark_as_failed(failure_reason="encrypted_pdf")
        await doc_repo.save(doc)

        response = await use_case.execute(doc.id)

        assert response.status == "FAILED"
        assert response.failure_reason == "encrypted_pdf"

    @pytest.mark.asyncio
    async def test_raises_not_found_for_missing_document(self) -> None:
        """A missing document raises a not found error."""
        doc_repo = InMemoryStudyDocumentRepository()
        use_case = GetStudyDocumentStatusUseCase(document_repository=doc_repo)

        with pytest.raises(StudyDocumentError, match="Document not found"):
            await use_case.execute(uuid.uuid4())

    @pytest.mark.asyncio
    async def test_returns_status_for_owned_document(self) -> None:
        """An owner can read the status of their own document."""
        doc_repo = InMemoryStudyDocumentRepository()
        use_case = GetStudyDocumentStatusUseCase(document_repository=doc_repo)
        owner_id = uuid.uuid4()
        doc = StudyDocument.create(
            id=uuid.uuid4(),
            filename="test.pdf",
            content_type="application/pdf",
            storage_path="study_documents/test.pdf",
            owner_user_id=owner_id,
        )
        await doc_repo.save(doc)

        response = await use_case.execute(doc.id, owner_id=owner_id)

        assert response.status == "PENDING_PROCESSING"

    @pytest.mark.asyncio
    async def test_returns_not_found_for_foreign_document(self) -> None:
        """A different user cannot read the status of another user's document."""
        doc_repo = InMemoryStudyDocumentRepository()
        use_case = GetStudyDocumentStatusUseCase(document_repository=doc_repo)
        owner_id = uuid.uuid4()
        other_owner_id = uuid.uuid4()
        doc = StudyDocument.create(
            id=uuid.uuid4(),
            filename="test.pdf",
            content_type="application/pdf",
            storage_path="study_documents/test.pdf",
            owner_user_id=owner_id,
        )
        await doc_repo.save(doc)

        with pytest.raises(StudyDocumentError, match="Document not found"):
            await use_case.execute(doc.id, owner_id=other_owner_id)
