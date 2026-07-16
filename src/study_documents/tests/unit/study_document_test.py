"""Unit tests for the StudyDocument domain entity.

TDD case list for authenticated ownership:
[x] 2.1 A StudyDocument can be created with an owner_user_id
[x] 2.2 An owner_user_id is required for new study documents
[x] 2.3 Status transitions preserve owner_user_id
[ ] 2.4 Repository can find a document by id and owner id
[ ] 2.3 Status transitions preserve owner_user_id
[ ] 2.4 Repository can find a document by id and owner id
"""

import uuid

OWNER_ID = uuid.uuid4()

import pytest

from src.study_documents.domain.entities import (
    MAX_FILENAME_LENGTH,
    StudyDocument,
    StudyDocumentError,
)


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
        owner_user_id=OWNER_ID,
        )

        assert doc.id == doc_id
        assert doc.filename == filename
        assert doc.content_type == content_type
        assert doc.storage_path == storage_path
        assert doc.status == "PENDING_PROCESSING"
        assert doc.failure_reason is None
        assert doc.chunks_count == 0

    def test_rejects_non_pdf_content_type(self) -> None:
        """A non-PDF content type is rejected with code invalid_file_type."""
        doc_id = uuid.uuid4()

        with pytest.raises(
            StudyDocumentError, match="Only PDF files are accepted"
        ) as exc:
            StudyDocument.create(
                id=doc_id,
                filename="notas.txt",
                content_type="text/plain",
                storage_path="study_documents/abc.txt",
            owner_user_id=OWNER_ID,
            )
        assert exc.value.code == "invalid_file_type"

    def test_rejects_non_pdf_filename_extension(self) -> None:
        """A file without .pdf extension is rejected with code invalid_file_type."""
        doc_id = uuid.uuid4()

        with pytest.raises(
            StudyDocumentError, match="Only PDF files are accepted"
        ) as exc:
            StudyDocument.create(
                id=doc_id,
                filename="notas.txt",
                content_type="application/pdf",
                storage_path="study_documents/abc.txt",
            owner_user_id=OWNER_ID,
            )
        assert exc.value.code == "invalid_file_type"

    def test_rejects_blank_filename(self) -> None:
        """A blank filename is rejected with a domain error with code invalid_filename."""
        doc_id = uuid.uuid4()

        with pytest.raises(StudyDocumentError, match="Filename must not be blank"):
            StudyDocument.create(
                id=doc_id,
                filename="",
                content_type="application/pdf",
                storage_path="study_documents/abc.pdf",
            owner_user_id=OWNER_ID,
            )

    def test_rejects_dot_filename(self) -> None:
        """A filename consisting of only '.' is rejected."""
        doc_id = uuid.uuid4()

        with pytest.raises(StudyDocumentError, match="Filename is reserved"):
            StudyDocument.create(
                id=doc_id,
                filename=".",
                content_type="application/pdf",
                storage_path="study_documents/abc.pdf",
            owner_user_id=OWNER_ID,
            )

    def test_rejects_dot_dot_filename(self) -> None:
        """A filename consisting of only '..' is rejected."""
        doc_id = uuid.uuid4()

        with pytest.raises(StudyDocumentError, match="Filename is reserved"):
            StudyDocument.create(
                id=doc_id,
                filename="..",
                content_type="application/pdf",
                storage_path="study_documents/abc.pdf",
            owner_user_id=OWNER_ID,
            )

    def test_rejects_control_characters_in_filename(self) -> None:
        """A filename containing control characters is rejected."""
        doc_id = uuid.uuid4()

        with pytest.raises(StudyDocumentError, match="Invalid filename"):
            StudyDocument.create(
                id=doc_id,
                filename="test\x00.pdf",
                content_type="application/pdf",
                storage_path="study_documents/abc.pdf",
            owner_user_id=OWNER_ID,
            )

    def test_rejects_filename_exceeding_max_length(self) -> None:
        """A filename longer than the maximum allowed length is rejected."""
        doc_id = uuid.uuid4()
        long_filename = "a" * (MAX_FILENAME_LENGTH + 1) + ".pdf"

        with pytest.raises(StudyDocumentError, match="Filename must not exceed"):
            StudyDocument.create(
                id=doc_id,
                filename=long_filename,
                content_type="application/pdf",
                storage_path="study_documents/abc.pdf",
            owner_user_id=OWNER_ID,
            )

    def test_preserves_safe_filename_on_document(self) -> None:
        """A safe valid PDF filename is preserved unchanged on the document."""
        doc_id = uuid.uuid4()
        original_filename = "introduccion-derecho.pdf"

        doc = StudyDocument.create(
            id=doc_id,
            filename=original_filename,
            content_type="application/pdf",
            storage_path="study_documents/doc.pdf",
        owner_user_id=OWNER_ID,
        )

        assert doc.filename == original_filename

    def test_creates_document_with_owner(self) -> None:
        """A StudyDocument is created with the authenticated user identifier as owner."""
        doc_id = uuid.uuid4()
        owner_id = uuid.uuid4()

        doc = StudyDocument.create(
            id=doc_id,
            filename="test.pdf",
            content_type="application/pdf",
            storage_path="study_documents/test.pdf",
            owner_user_id=owner_id,
        )

        assert doc.owner_user_id == owner_id

    def test_preserves_owner_through_status_transitions(self) -> None:
        """The owner_user_id is preserved through the full document lifecycle."""
        owner_id = uuid.uuid4()
        doc = StudyDocument.create(
            id=uuid.uuid4(),
            filename="test.pdf",
            content_type="application/pdf",
            storage_path="study_documents/test.pdf",
            owner_user_id=owner_id,
        )

        assert doc.owner_user_id == owner_id

        doc.mark_as_processing()
        assert doc.owner_user_id == owner_id

        doc.mark_as_ready(chunk_count=3)
        assert doc.owner_user_id == owner_id

    def test_rejects_document_without_owner(self) -> None:
        """A StudyDocument without an owner_user_id is rejected."""
        with pytest.raises(StudyDocumentError, match="Document owner is required") as exc:
            StudyDocument.create(
                id=uuid.uuid4(),
                filename="test.pdf",
                content_type="application/pdf",
                storage_path="study_documents/test.pdf",
                owner_user_id=None,
            )
        assert exc.value.code == "missing_owner"

    def test_rejects_filename_with_path_separator(self) -> None:
        """A filename containing path separators is rejected for security."""
        doc_id = uuid.uuid4()

        with pytest.raises(StudyDocumentError, match="Invalid filename"):
            StudyDocument.create(
                id=doc_id,
                filename="../malicious.pdf",
                content_type="application/pdf",
                storage_path="study_documents/abc.pdf",
            owner_user_id=OWNER_ID,
            )

    def test_marks_pending_document_as_processing(self) -> None:
        """A pending document transitions to PROCESSING."""
        doc = StudyDocument.create(
            id=uuid.uuid4(),
            filename="test.pdf",
            content_type="application/pdf",
            storage_path="study_documents/test.pdf",
        owner_user_id=OWNER_ID,
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
        owner_user_id=OWNER_ID,
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
        owner_user_id=OWNER_ID,
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
        owner_user_id=OWNER_ID,
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
        owner_user_id=OWNER_ID,
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
        owner_user_id=OWNER_ID,
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
        owner_user_id=OWNER_ID,
        )
        doc.mark_as_failed(failure_reason="test")

        with pytest.raises(StudyDocumentError, match="Cannot transition"):
            doc.mark_as_processing()
