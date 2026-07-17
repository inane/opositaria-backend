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
from src.study_documents.domain.entities import (
    MAX_UPLOAD_SIZE_BYTES,
    StudyDocument,
    StudyDocumentError,
)
from src.study_documents.domain.repositories import StudyDocumentRepository
from src.study_spaces.domain.entities import StudySpace, StudySpaceError
from src.study_spaces.domain.repositories import StudySpaceRepository


class UploadStudyDocumentUseCase:
    """Orchestrates PDF upload: creates space, validates, persists, stores file, persists job, and publishes processing."""

    def __init__(
        self,
        document_repository: StudyDocumentRepository,
        document_storage: DocumentStorage,
        publisher: ProcessingRequestPublisher,
        job_repository: DocumentProcessingJobRepository,
        space_repository: StudySpaceRepository,
    ) -> None:
        self._document_repository = document_repository
        self._document_storage = document_storage
        self._publisher = publisher
        self._job_repository = job_repository
        self._space_repository = space_repository

    async def execute(
        self,
        filename: str,
        content_type: str,
        content: bytes,
        owner_user_id: uuid.UUID | None = None,
        study_space_name: str | None = None,
    ) -> UploadDocumentResponse:
        """Upload a PDF study document and create a study space."""
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
        space_id = uuid.uuid4()

        # Create the study space first (validates the name)
        if not study_space_name or not study_space_name.strip():
            raise StudySpaceError(
                "Study space name must not be blank",
                safe=True,
                code="invalid_name",
            )
        if not owner_user_id:
            raise StudyDocumentError(
                "Document owner is required", safe=True, code="missing_owner"
            )
        space = StudySpace.create(
            id=space_id,
            owner_id=owner_user_id,
            name=study_space_name,
            document_ids=[document_id],
        )

        doc = StudyDocument.create(
            id=document_id,
            filename=filename,
            content_type=content_type,
            storage_path="",
            owner_user_id=owner_user_id,
            study_space_id=space_id,
        )

        storage_path = await self._document_storage.save(document_id, filename, content)
        doc.storage_path = storage_path

        await self._space_repository.save(space)
        await self._document_repository.save(doc)

        job_id = uuid.uuid4()
        job = DocumentProcessingJob.create(id=job_id, document_id=document_id)
        await self._job_repository.save(job)

        # Commit before publishing so doc+space+job survive a publish failure
        await self._space_repository.commit()
        await self._document_repository.commit()
        await self._job_repository.commit()

        await self._publisher.publish(document_id, job_id)

        return UploadDocumentResponse(
            document_id=document_id,
            status=doc.status,
            study_space_id=space_id,
        )


class GetStudyDocumentStatusUseCase:
    """Retrieves the current processing status of a study document."""

    def __init__(
        self,
        document_repository: StudyDocumentRepository,
    ) -> None:
        self._document_repository = document_repository

    async def execute(
        self, document_id: uuid.UUID, owner_id: uuid.UUID | None = None
    ) -> DocumentStatusResponse:
        """Get the status of a study document."""
        if owner_id is not None:
            doc = await self._document_repository.find_by_id_and_owner(
                document_id, owner_id
            )
        else:
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
