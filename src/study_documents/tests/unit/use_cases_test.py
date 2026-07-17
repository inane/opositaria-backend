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
from src.study_spaces.domain.entities import StudySpaceError
from src.study_spaces.domain.repositories import InMemoryStudySpaceRepository


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
        space_repo = InMemoryStudySpaceRepository()
        storage = DocumentStorageSpy()
        publisher = PublisherSpy()
        use_case = UploadStudyDocumentUseCase(
            document_repository=doc_repo,
            document_storage=storage,
            publisher=publisher,
            job_repository=job_repo,
            space_repository=space_repo,
        )

        owner_id = uuid.uuid4()
        response = await use_case.execute(
            filename="test.pdf",
            content_type="application/pdf",
            content=b"%PDF-1.4 test content",
            owner_user_id=owner_id,
            study_space_name="Derecho Administrativo",
        )

        assert isinstance(response, UploadDocumentResponse)
        assert response.status == "PENDING_PROCESSING"

        # Document was persisted with owner and study space
        doc = await doc_repo.find_by_id(response.document_id)
        assert doc is not None
        assert doc.filename == "test.pdf"
        assert doc.status == "PENDING_PROCESSING"
        assert doc.owner_user_id == owner_id
        assert doc.study_space_id == response.study_space_id

        # Study space was created
        space = await space_repo.find_by_id(response.study_space_id)
        assert space is not None
        assert str(space.name) == "Derecho Administrativo"
        assert space.owner_id == owner_id
        assert space.document_count == 1

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
    async def test_rejects_empty_upload(self) -> None:
        """An empty upload raises a StudyDocumentError with code empty_upload."""
        doc_repo = InMemoryStudyDocumentRepository()
        job_repo = InMemoryDocumentProcessingJobRepository()
        space_repo = InMemoryStudySpaceRepository()
        storage = DocumentStorageSpy()
        publisher = PublisherSpy()
        use_case = UploadStudyDocumentUseCase(
            document_repository=doc_repo,
            document_storage=storage,
            publisher=publisher,
            job_repository=job_repo,
            space_repository=space_repo,
        )

        content = b""
        with pytest.raises(StudyDocumentError, match="Upload content is empty") as exc:
            await use_case.execute(
                filename="test.pdf",
                content_type="application/pdf",
                content=content,
                owner_user_id=uuid.uuid4(),
                study_space_name="Derecho Administrativo",
            )
        assert exc.value.code == "empty_upload"

    @pytest.mark.asyncio
    async def test_rejects_oversized_upload(self) -> None:
        """An oversized upload raises a StudyDocumentError with code file_too_large."""
        doc_repo = InMemoryStudyDocumentRepository()
        job_repo = InMemoryDocumentProcessingJobRepository()
        space_repo = InMemoryStudySpaceRepository()
        storage = DocumentStorageSpy()
        publisher = PublisherSpy()
        use_case = UploadStudyDocumentUseCase(
            document_repository=doc_repo,
            document_storage=storage,
            publisher=publisher,
            job_repository=job_repo,
            space_repository=space_repo,
        )

        oversized = b"x" * (MAX_UPLOAD_SIZE_BYTES + 1)
        with pytest.raises(StudyDocumentError, match="size limit") as exc:
            await use_case.execute(
                filename="test.pdf",
                content_type="application/pdf",
                content=oversized,
                owner_user_id=uuid.uuid4(),
                study_space_name="Derecho Administrativo",
            )
        assert exc.value.code == "file_too_large"

    @pytest.mark.asyncio
    async def test_rejects_non_pdf_content_type(self) -> None:
        """A non-PDF content type raises a StudyDocumentError with code invalid_file_type."""
        doc_repo = InMemoryStudyDocumentRepository()
        job_repo = InMemoryDocumentProcessingJobRepository()
        space_repo = InMemoryStudySpaceRepository()
        storage = DocumentStorageSpy()
        publisher = PublisherSpy()
        use_case = UploadStudyDocumentUseCase(
            document_repository=doc_repo,
            document_storage=storage,
            publisher=publisher,
            job_repository=job_repo,
            space_repository=space_repo,
        )

        with pytest.raises(StudyDocumentError, match="Only PDF files") as exc:
            await use_case.execute(
                filename="notas.txt",
                content_type="text/plain",
                content=b"some content",
                owner_user_id=uuid.uuid4(),
                study_space_name="Derecho Administrativo",
            )
        assert exc.value.code == "invalid_file_type"

    @pytest.mark.asyncio
    async def test_rejects_non_pdf_extension(self) -> None:
        """A file without .pdf extension raises a StudyDocumentError with code invalid_file_type."""
        doc_repo = InMemoryStudyDocumentRepository()
        job_repo = InMemoryDocumentProcessingJobRepository()
        space_repo = InMemoryStudySpaceRepository()
        storage = DocumentStorageSpy()
        publisher = PublisherSpy()
        use_case = UploadStudyDocumentUseCase(
            document_repository=doc_repo,
            document_storage=storage,
            publisher=publisher,
            job_repository=job_repo,
            space_repository=space_repo,
        )

        with pytest.raises(StudyDocumentError, match="Only PDF files") as exc:
            await use_case.execute(
                filename="notas.txt",
                content_type="application/pdf",
                content=b"some content",
                owner_user_id=uuid.uuid4(),
                study_space_name="Derecho Administrativo",
            )
        assert exc.value.code == "invalid_file_type"

    @pytest.mark.asyncio
    async def test_rejects_blank_space_name(self) -> None:
        """A blank study_space_name raises an error and persists nothing."""
        doc_repo = InMemoryStudyDocumentRepository()
        job_repo = InMemoryDocumentProcessingJobRepository()
        space_repo = InMemoryStudySpaceRepository()
        storage = DocumentStorageSpy()
        publisher = PublisherSpy()
        use_case = UploadStudyDocumentUseCase(
            document_repository=doc_repo,
            document_storage=storage,
            publisher=publisher,
            job_repository=job_repo,
            space_repository=space_repo,
        )

        space_count_before = len(space_repo._spaces)

        with pytest.raises(
            StudySpaceError, match="Study space name must not be blank"
        ) as exc:
            await use_case.execute(
                filename="test.pdf",
                content_type="application/pdf",
                content=b"%PDF-1.4 valid content",
                owner_user_id=uuid.uuid4(),
                study_space_name="",
            )
        assert exc.value.code == "invalid_name"

        # No space was persisted
        assert len(space_repo._spaces) == space_count_before
        # No document was persisted
        assert len(doc_repo._documents) == 0
        # No job was persisted
        assert len(job_repo._jobs) == 0

    @pytest.mark.asyncio
    async def test_preserves_filename_separate_from_space_name(self) -> None:
        """The original filename is preserved as the document filename, not the study space name."""
        doc_repo = InMemoryStudyDocumentRepository()
        job_repo = InMemoryDocumentProcessingJobRepository()
        space_repo = InMemoryStudySpaceRepository()
        storage = DocumentStorageSpy()
        publisher = PublisherSpy()
        use_case = UploadStudyDocumentUseCase(
            document_repository=doc_repo,
            document_storage=storage,
            publisher=publisher,
            job_repository=job_repo,
            space_repository=space_repo,
        )

        owner_id = uuid.uuid4()
        response = await use_case.execute(
            filename="tema-1.pdf",
            content_type="application/pdf",
            content=b"%PDF-1.4 content",
            owner_user_id=owner_id,
            study_space_name="Derecho Administrativo",
        )

        doc = await doc_repo.find_by_id(response.document_id)
        assert doc is not None
        assert doc.filename == "tema-1.pdf"

        space = await space_repo.find_by_id(response.study_space_id)
        assert space is not None
        assert str(space.name) == "Derecho Administrativo"

    @pytest.mark.asyncio
    async def test_invalid_file_type_fails_without_creating_space(self) -> None:
        """An invalid file type fails without persisting a study space."""
        doc_repo = InMemoryStudyDocumentRepository()
        job_repo = InMemoryDocumentProcessingJobRepository()
        space_repo = InMemoryStudySpaceRepository()
        storage = DocumentStorageSpy()
        publisher = PublisherSpy()
        use_case = UploadStudyDocumentUseCase(
            document_repository=doc_repo,
            document_storage=storage,
            publisher=publisher,
            job_repository=job_repo,
            space_repository=space_repo,
        )

        space_count_before = len(space_repo._spaces)

        with pytest.raises(StudyDocumentError, match="Only PDF files"):
            await use_case.execute(
                filename="notes.txt",
                content_type="text/plain",
                content=b"not a pdf",
                owner_user_id=uuid.uuid4(),
                study_space_name="Test",
            )

        assert len(space_repo._spaces) == space_count_before
        assert len(doc_repo._documents) == 0

    @pytest.mark.asyncio
    async def test_publish_failure_does_not_rollback_durable_state(self) -> None:
        """When publishing fails after commit, the document, space, and job remain persisted."""
        doc_repo = InMemoryStudyDocumentRepository()
        job_repo = InMemoryDocumentProcessingJobRepository()
        space_repo = InMemoryStudySpaceRepository()
        storage = DocumentStorageSpy()
        publisher = PublisherSpy(should_fail=True)
        use_case = UploadStudyDocumentUseCase(
            document_repository=doc_repo,
            document_storage=storage,
            publisher=publisher,
            job_repository=job_repo,
            space_repository=space_repo,
        )

        owner_id = uuid.uuid4()

        with pytest.raises(RuntimeError, match="RabbitMQ connection failed"):
            await use_case.execute(
                filename="test.pdf",
                content_type="application/pdf",
                content=b"%PDF-1.4 content",
                owner_user_id=owner_id,
                study_space_name="Derecho Administrativo",
            )

        # Despite publish failure, durable state was committed
        assert len(doc_repo._documents) == 1
        assert len(space_repo._spaces) == 1
        assert len(job_repo._jobs) == 1

    @pytest.mark.asyncio
    async def test_upload_response_includes_study_space_id(self) -> None:
        """The upload response includes the created study_space_id."""
        doc_repo = InMemoryStudyDocumentRepository()
        job_repo = InMemoryDocumentProcessingJobRepository()
        space_repo = InMemoryStudySpaceRepository()
        storage = DocumentStorageSpy()
        publisher = PublisherSpy()
        use_case = UploadStudyDocumentUseCase(
            document_repository=doc_repo,
            document_storage=storage,
            publisher=publisher,
            job_repository=job_repo,
            space_repository=space_repo,
        )

        response = await use_case.execute(
            filename="test.pdf",
            content_type="application/pdf",
            content=b"%PDF-1.4 content",
            owner_user_id=uuid.uuid4(),
            study_space_name="Derecho Administrativo",
        )

        assert response.study_space_id is not None

        space = await space_repo.find_by_id(response.study_space_id)
        assert space is not None
        assert str(space.name) == "Derecho Administrativo"


class TestGetStudyDocumentStatusUseCase:
    """Tests for GetStudyDocumentStatusUseCase."""

    @pytest.mark.asyncio
    async def test_returns_pending_status(self) -> None:
        """A pending document returns PENDING_PROCESSING status."""
        doc_repo = InMemoryStudyDocumentRepository()
        use_case = GetStudyDocumentStatusUseCase(document_repository=doc_repo)
        doc = StudyDocument.create(
            id=uuid.uuid4(),
            filename="test.pdf",
            content_type="application/pdf",
            storage_path="study_documents/test.pdf",
            owner_user_id=uuid.uuid4(),
            study_space_id=uuid.uuid4(),
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
            study_space_id=uuid.uuid4(),
        )
        doc.mark_as_processing()
        doc.mark_as_ready(chunk_count=5)
        await doc_repo.save(doc)

        response = await use_case.execute(doc.id)

        assert response.status == "READY"
        assert response.chunks_count == 5

    @pytest.mark.asyncio
    async def test_returns_failed_status_with_reason(self) -> None:
        """A failed document returns FAILED status with failure reason."""
        doc_repo = InMemoryStudyDocumentRepository()
        use_case = GetStudyDocumentStatusUseCase(document_repository=doc_repo)
        doc = StudyDocument.create(
            id=uuid.uuid4(),
            filename="test.pdf",
            content_type="application/pdf",
            storage_path="study_documents/test.pdf",
            owner_user_id=uuid.uuid4(),
            study_space_id=uuid.uuid4(),
        )
        doc.mark_as_failed(failure_reason="Invalid document type")
        await doc_repo.save(doc)

        response = await use_case.execute(doc.id)

        assert response.status == "FAILED"
        assert response.failure_reason == "Invalid document type"
        assert response.filename == "test.pdf"

    @pytest.mark.asyncio
    async def test_returns_processing_status_with_no_chunks(self) -> None:
        """A processing document returns PROCESSING status."""
        doc_repo = InMemoryStudyDocumentRepository()
        use_case = GetStudyDocumentStatusUseCase(document_repository=doc_repo)
        doc = StudyDocument.create(
            id=uuid.uuid4(),
            filename="test.pdf",
            content_type="application/pdf",
            storage_path="study_documents/test.pdf",
            owner_user_id=uuid.uuid4(),
            study_space_id=uuid.uuid4(),
        )
        doc.mark_as_processing()
        await doc_repo.save(doc)

        response = await use_case.execute(doc.id)

        assert response.status == "PROCESSING"

    @pytest.mark.asyncio
    async def test_returns_not_found_for_nonexistent_document(self) -> None:
        """A non-existent document raises a StudyDocumentError."""
        doc_repo = InMemoryStudyDocumentRepository()
        use_case = GetStudyDocumentStatusUseCase(document_repository=doc_repo)

        with pytest.raises(StudyDocumentError, match="Document not found"):
            await use_case.execute(uuid.uuid4(), owner_id=uuid.uuid4())

    @pytest.mark.asyncio
    async def test_returns_not_found_for_different_owner(self) -> None:
        """A document owned by a different user is not found."""
        doc_repo = InMemoryStudyDocumentRepository()
        use_case = GetStudyDocumentStatusUseCase(document_repository=doc_repo)
        owner_id = uuid.uuid4()
        doc = StudyDocument.create(
            id=uuid.uuid4(),
            filename="test.pdf",
            content_type="application/pdf",
            storage_path="study_documents/test.pdf",
            owner_user_id=owner_id,
            study_space_id=uuid.uuid4(),
        )
        await doc_repo.save(doc)

        with pytest.raises(StudyDocumentError, match="Document not found"):
            await use_case.execute(doc.id, owner_id=uuid.uuid4())
