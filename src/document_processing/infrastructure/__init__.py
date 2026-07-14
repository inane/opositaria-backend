"""PostgreSQL repository adapter for document processing jobs."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.document_processing.domain.entities import DocumentProcessingJob
from src.study_documents.infrastructure.models import DocumentProcessingJobModel


class PostgresDocumentProcessingJobRepository:
    """PostgreSQL adapter for DocumentProcessingJobRepository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, job: DocumentProcessingJob) -> None:
        """Persist a processing job."""
        model = DocumentProcessingJobModel(
            id=job.id,
            document_id=job.document_id,
            status=job.status,
            attempts=job.attempts,
            failure_reason=job.failure_reason,
            created_at=job.created_at,
            updated_at=job.updated_at,
            completed_at=job.completed_at,
        )
        self._session.add(model)

    async def find_by_id(self, job_id: uuid.UUID) -> DocumentProcessingJob | None:
        """Find a processing job by its identifier."""
        result = await self._session.execute(
            select(DocumentProcessingJobModel).where(
                DocumentProcessingJobModel.id == job_id
            )
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return DocumentProcessingJob(
            id=model.id,
            document_id=model.document_id,
            status=model.status,
            attempts=model.attempts,
            failure_reason=model.failure_reason,
            created_at=model.created_at,
            updated_at=model.updated_at,
            completed_at=model.completed_at,
        )
