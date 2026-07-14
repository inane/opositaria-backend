"""Unit tests for DocumentProcessingJob domain entity."""

import uuid


from src.document_processing.domain.entities import (
    DocumentProcessingJob,
)


class TestDocumentProcessingJob:
    """Tests for DocumentProcessingJob entity creation and lifecycle."""

    def test_creates_pending_job_for_document(self) -> None:
        """A processing job is created in PENDING state for a document."""
        job_id = uuid.uuid4()
        document_id = uuid.uuid4()

        job = DocumentProcessingJob.create(
            id=job_id,
            document_id=document_id,
        )

        assert job.id == job_id
        assert job.document_id == document_id
        assert job.status == "PENDING"
        assert job.attempts == 0
        assert job.failure_reason is None

    def test_marks_pending_job_as_running(self) -> None:
        """A pending job transitions to RUNNING."""
        job = DocumentProcessingJob.create(id=uuid.uuid4(), document_id=uuid.uuid4())

        job.mark_as_running()

        assert job.status == "RUNNING"

    def test_marks_running_job_as_completed(self) -> None:
        """A running job transitions to COMPLETED."""
        job = DocumentProcessingJob.create(id=uuid.uuid4(), document_id=uuid.uuid4())
        job.mark_as_running()

        job.mark_as_completed()

        assert job.status == "COMPLETED"
        assert job.completed_at is not None

    def test_marks_running_job_as_failed_with_reason(self) -> None:
        """A running job transitions to FAILED with attempt count and reason."""
        job = DocumentProcessingJob.create(id=uuid.uuid4(), document_id=uuid.uuid4())
        job.mark_as_running()

        job.mark_as_failed(failure_reason="PDF extraction timeout")

        assert job.status == "FAILED"
        assert job.failure_reason == "PDF extraction timeout"
        assert job.attempts == 1

    def test_ignores_completed_duplicate_processing(self) -> None:
        """A completed job ignores duplicate processing attempts."""
        job = DocumentProcessingJob.create(id=uuid.uuid4(), document_id=uuid.uuid4())
        job.mark_as_running()
        job.mark_as_completed()

        job.mark_as_running()

        assert job.status == "COMPLETED"
