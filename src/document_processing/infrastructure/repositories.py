"""PostgreSQL repository adapter for document processing jobs."""

import uuid

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.document_processing.domain.entities import DocumentProcessingJob
from src.study_documents.infrastructure.models import DocumentProcessingJobModel


class PostgresDocumentProcessingJobRepository:
    """PostgreSQL adapter for DocumentProcessingJobRepository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, job: DocumentProcessingJob) -> None:
        """Persist a processing job (upsert)."""
        await self._session.execute(
            text("""
                INSERT INTO document_processing_jobs (id, document_id, status, attempts,
                    failure_reason, created_at, updated_at, completed_at)
                VALUES (:id, :document_id, :status, :attempts,
                    :failure_reason, :created_at, :updated_at, :completed_at)
                ON CONFLICT (id) DO UPDATE SET
                    status = EXCLUDED.status,
                    attempts = EXCLUDED.attempts,
                    failure_reason = EXCLUDED.failure_reason,
                    updated_at = EXCLUDED.updated_at,
                    completed_at = EXCLUDED.completed_at
            """),
            {
                "id": job.id,
                "document_id": job.document_id,
                "status": job.status,
                "attempts": job.attempts,
                "failure_reason": job.failure_reason,
                "created_at": job.created_at,
                "updated_at": job.updated_at,
                "completed_at": job.completed_at,
            },
        )

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

    async def flush(self) -> None:
        """Flush pending writes to the database session."""
        await self._session.flush()

    async def commit(self) -> None:
        """Commit the current transaction durably."""
        await self._session.commit()
