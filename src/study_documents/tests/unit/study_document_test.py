"""Unit tests for the StudyDocument domain entity."""

import uuid

import pytest

from src.study_documents.domain.entities import StudyDocument, StudyDocumentError


class TestStudyDocument:
    """Tests for StudyDocument entity creation and lifecycle."""

    def test_creates_pending_document_with_valid_metadata(self) -> None:
        """A StudyDocument is created in PENDING_PROCESSING with valid filename, content type, and storage reference."""
        doc_id = uuid.uuid4()
        filename = "introduccion-derecho.pdf"
        content_type = "application/pdf"
        storage_path = "study_documents/abc123.pdf"

        doc = StudyDocument.create(
            id=doc_id,
            filename=filename,
            content_type=content_type,
            storage_path=storage_path,
        )

        assert doc.id == doc_id
        assert doc.filename == filename
        assert doc.content_type == content_type
        assert doc.storage_path == storage_path
        assert doc.status == "PENDING_PROCESSING"
        assert doc.failure_reason is None
        assert doc.chunks_count == 0

    def test_rejects_non_pdf_content_type(self) -> None:
        """A non-PDF content type is rejected with a domain error."""
        doc_id = uuid.uuid4()

        with pytest.raises(StudyDocumentError, match="Only PDF files are accepted"):
            StudyDocument.create(
                id=doc_id,
                filename="notas.txt",
                content_type="text/plain",
                storage_path="study_documents/abc.txt",
            )

    def test_rejects_non_pdf_filename_extension(self) -> None:
        """A file without .pdf extension is rejected even with PDF content type."""
        doc_id = uuid.uuid4()

        with pytest.raises(StudyDocumentError, match="Only PDF files are accepted"):
            StudyDocument.create(
                id=doc_id,
                filename="notas.txt",
                content_type="application/pdf",
                storage_path="study_documents/abc.txt",
            )

    def test_rejects_filename_with_path_separator(self) -> None:
        """A filename containing path separators is rejected for security."""
        doc_id = uuid.uuid4()

        with pytest.raises(StudyDocumentError, match="Invalid filename"):
            StudyDocument.create(
                id=doc_id,
                filename="../malicious.pdf",
                content_type="application/pdf",
                storage_path="study_documents/abc.pdf",
            )

    def test_marks_pending_document_as_processing(self) -> None:
        """A pending document transitions to PROCESSING."""
        doc = StudyDocument.create(
            id=uuid.uuid4(),
            filename="test.pdf",
            content_type="application/pdf",
            storage_path="study_documents/test.pdf",
        )

        doc.mark_as_processing()

        assert doc.status == "PROCESSING"
        assert doc.updated_at is not None

    def test_marks_processing_document_as_ready_with_chunk_count(self) -> None:
        """A processing document transitions to READY with chunk count."""
        doc = StudyDocument.create(
            id=uuid.uuid4(),
            filename="test.pdf",
            content_type="application/pdf",
            storage_path="study_documents/test.pdf",
        )
        doc.mark_as_processing()

        doc.mark_as_ready(chunk_count=5)

        assert doc.status == "READY"
        assert doc.chunks_count == 5
        assert doc.processed_at is not None

    def test_marks_pending_document_as_failed_with_reason(self) -> None:
        """A pending document transitions to FAILED with a safe failure reason."""
        doc = StudyDocument.create(
            id=uuid.uuid4(),
            filename="test.pdf",
            content_type="application/pdf",
            storage_path="study_documents/test.pdf",
        )

        doc.mark_as_failed(failure_reason="No extractable text found")

        assert doc.status == "FAILED"
        assert doc.failure_reason == "No extractable text found"

    def test_marks_processing_document_as_failed_with_reason(self) -> None:
        """A processing document transitions to FAILED with a safe failure reason."""
        doc = StudyDocument.create(
            id=uuid.uuid4(),
            filename="test.pdf",
            content_type="application/pdf",
            storage_path="study_documents/test.pdf",
        )
        doc.mark_as_processing()

        doc.mark_as_failed(failure_reason="Embedding generation failed")

        assert doc.status == "FAILED"
        assert doc.failure_reason == "Embedding generation failed"

    def test_rejects_transition_from_ready_to_processing(self) -> None:
        """A ready document cannot transition back to PROCESSING."""
        doc = StudyDocument.create(
            id=uuid.uuid4(),
            filename="test.pdf",
            content_type="application/pdf",
            storage_path="study_documents/test.pdf",
        )
        doc.mark_as_processing()
        doc.mark_as_ready(chunk_count=3)

        with pytest.raises(StudyDocumentError, match="Cannot transition"):
            doc.mark_as_processing()

    def test_rejects_transition_from_ready_to_failed(self) -> None:
        """A ready document cannot transition to FAILED."""
        doc = StudyDocument.create(
            id=uuid.uuid4(),
            filename="test.pdf",
            content_type="application/pdf",
            storage_path="study_documents/test.pdf",
        )
        doc.mark_as_processing()
        doc.mark_as_ready(chunk_count=3)

        with pytest.raises(StudyDocumentError, match="Cannot transition"):
            doc.mark_as_failed(failure_reason="test")

    def test_rejects_transition_from_failed_to_processing(self) -> None:
        """A failed document cannot transition to PROCESSING."""
        doc = StudyDocument.create(
            id=uuid.uuid4(),
            filename="test.pdf",
            content_type="application/pdf",
            storage_path="study_documents/test.pdf",
        )
        doc.mark_as_failed(failure_reason="test")

        with pytest.raises(StudyDocumentError, match="Cannot transition"):
            doc.mark_as_processing()
