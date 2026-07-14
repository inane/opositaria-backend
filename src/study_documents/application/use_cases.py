"""Application use cases for study document operations."""

import uuid

from src.document_processing.domain.entities import DocumentProcessingJob
from src.document_processing.domain.repositories import (
    DocumentProcessingJobRepository,
)
from src.study_documents.application.dtos import (
    DocumentStatusResponse,
    UploadDocumentResponse,
)
from src.study_documents.application.ports import (
    DocumentStorage,
    ProcessingRequestPublisher,
)
from src.study_documents.domain.entities import MAX_UPLOAD_SIZE_BYTES, StudyDocument, StudyDocumentError
from src.study_documents.domain.repositories import StudyDocumentRepository


class UploadStudyDocumentUseCase:
    """Orchestrates PDF upload: validates, persists, stores file, persists job, and publishes processing."""

    def __init__(
        self,
        document_repository: StudyDocumentRepository,
        document_storage: DocumentStorage,
        publisher: ProcessingRequestPublisher,
        job_repository: DocumentProcessingJobRepository,
    ) -> None:
        self._document_repository = document_repository
        self._document_storage = document_storage
        self._publisher = publisher
        self._job_repository = job_repository

    async def execute(
        self,
        filename: str,
        content_type: str,
        content: bytes,
    ) -> UploadDocumentResponse:
        """Upload a PDF study document."""
        if not content:
            raise StudyDocumentError(
                "Upload content is empty", safe=True, code="empty_upload"
            )

        if len(content) > MAX_UPLOAD_SIZE_BYTES:
            raise StudyDocumentError(
                "Upload content exceeds the 50 MB size limit",
                safe=True,
                code="file_too_large",
            )

        document_id = uuid.uuid4()
        doc = StudyDocument.create(
            id=document_id,
            filename=filename,
            content_type=content_type,
            storage_path="",
        )

        storage_path = await self._document_storage.save(document_id, filename, content)
        doc.storage_path = storage_path

        await self._document_repository.save(doc)

        job_id = uuid.uuid4()
        job = DocumentProcessingJob.create(id=job_id, document_id=document_id)
        await self._job_repository.save(job)

        # Commit before publishing so doc+job survive a publish failure
        await self._document_repository.commit()
        await self._job_repository.commit()

        await self._publisher.publish(document_id, job_id)

        return UploadDocumentResponse(
            document_id=document_id,
            status=doc.status,
        )


class GetStudyDocumentStatusUseCase:
    """Retrieves the current processing status of a study document."""

    def __init__(
        self,
        document_repository: StudyDocumentRepository,
    ) -> None:
        self._document_repository = document_repository

    async def execute(self, document_id: uuid.UUID) -> DocumentStatusResponse:
        """Get the status of a study document."""
        doc = await self._document_repository.find_by_id(document_id)
        if doc is None:
            raise StudyDocumentError("Document not found", safe=True)
        return DocumentStatusResponse(
            document_id=doc.id,
            filename=doc.filename,
            status=doc.status,
            failure_reason=doc.failure_reason,
            chunks_count=doc.chunks_count,
        )