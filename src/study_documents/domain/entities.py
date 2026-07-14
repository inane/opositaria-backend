"""StudyDocument domain entity."""

import re
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone


class StudyDocumentError(Exception):
    """Domain error for study document operations."""

    def __init__(self, message: str, *, safe: bool = False, code: str = "") -> None:
        self.message = message
        self.safe = safe
        self.code = code
        super().__init__(message)


ALLOWED_CONTENT_TYPES = {"application/pdf"}
ALLOWED_EXTENSIONS = {".pdf"}
FORBIDDEN_FILENAME_CHARS = {"/", "\\"}
RESERVED_FILENAMES = {".", ".."}
CONTROL_CHARACTERS_RE = re.compile(r"[\x00-\x1f\x7f]")
MAX_FILENAME_LENGTH = 255
EMBEDDING_DIMENSION = 384
MAX_UPLOAD_SIZE_BYTES = 50 * 1024 * 1024


@dataclass
class StudyDocumentChunk:
    """A chunk of extracted text from a study document with its embedding.

    Each chunk belongs to a single document and preserves the original
    sequence order from the extraction process.
    """

    id: uuid.UUID
    document_id: uuid.UUID
    text: str
    sequence_number: int
    embedding: list[float]
    embedding_model: str
    page_number: int | None = None
    created_at: datetime | None = None

    def __post_init__(self) -> None:
        """Set timestamp on creation."""
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)

    @classmethod
    def create(
        cls,
        id: uuid.UUID,
        document_id: uuid.UUID,
        text: str,
        sequence_number: int,
        embedding: list[float],
        embedding_model: str,
        page_number: int | None = None,
    ) -> "StudyDocumentChunk":
        """Create a validated StudyDocumentChunk.

        Raises StudyDocumentError if validation fails.
        """
        if not text.strip():
            raise StudyDocumentError("Chunk text must not be blank", safe=True)
        if len(embedding) != EMBEDDING_DIMENSION:
            raise StudyDocumentError(
                f"Embedding dimension must be {EMBEDDING_DIMENSION}, got {len(embedding)}"
            )
        return cls(
            id=id,
            document_id=document_id,
            text=text,
            sequence_number=sequence_number,
            embedding=embedding,
            embedding_model=embedding_model,
            page_number=page_number,
        )


@dataclass
class StudyDocument:
    """A study document uploaded for semantic search processing.

    Documents flow through a lifecycle: PENDING_PROCESSING → PROCESSING → READY | FAILED.
    """

    id: uuid.UUID
    filename: str
    content_type: str
    storage_path: str
    status: str = "PENDING_PROCESSING"
    failure_reason: str | None = None
    chunks_count: int = 0
    created_at: datetime | None = None
    updated_at: datetime | None = None
    processed_at: datetime | None = None

    def __post_init__(self) -> None:
        """Set timestamps on creation."""
        now = datetime.now(timezone.utc)
        if self.created_at is None:
            self.created_at = now
        if self.updated_at is None:
            self.updated_at = now

    @classmethod
    def create(
        cls,
        id: uuid.UUID,
        filename: str,
        content_type: str,
        storage_path: str,
    ) -> "StudyDocument":
        """Create a validated StudyDocument.

        Raises StudyDocumentError if the content type is not allowed.
        """
        if not filename:
            raise StudyDocumentError(
                "Filename must not be blank",
                safe=True,
                code="invalid_filename",
            )
        if filename in RESERVED_FILENAMES:
            raise StudyDocumentError(
                "Filename is reserved",
                safe=True,
                code="invalid_filename",
            )
        if CONTROL_CHARACTERS_RE.search(filename):
            raise StudyDocumentError(
                "Invalid filename",
                safe=True,
                code="invalid_filename",
            )
        if len(filename) > MAX_FILENAME_LENGTH:
            raise StudyDocumentError(
                "Filename must not exceed 255 characters",
                safe=True,
                code="invalid_filename",
            )
        if content_type not in ALLOWED_CONTENT_TYPES:
            raise StudyDocumentError(
                f"Only PDF files are accepted: received {content_type}",
                safe=True,
                code="invalid_file_type",
            )
        if not any(filename.lower().endswith(ext) for ext in ALLOWED_EXTENSIONS):
            raise StudyDocumentError(
                f"Only PDF files are accepted: received {filename}",
                safe=True,
                code="invalid_file_type",
            )
        if any(c in filename for c in FORBIDDEN_FILENAME_CHARS):
            raise StudyDocumentError(
                f"Invalid filename: {filename}",
                safe=True,
                code="invalid_filename",
            )
        return cls(
            id=id,
            filename=filename,
            content_type=content_type,
            storage_path=storage_path,
        )

    def mark_as_processing(self) -> None:
        """Transition from PENDING_PROCESSING to PROCESSING."""
        self._assert_can_transition_to("PROCESSING", {"PENDING_PROCESSING"})
        self.status = "PROCESSING"
        self.updated_at = datetime.now(timezone.utc)

    def mark_as_ready(self, chunk_count: int) -> None:
        """Transition from PROCESSING to READY with the given chunk count."""
        self._assert_can_transition_to("READY", {"PROCESSING"})
        self.status = "READY"
        self.chunks_count = chunk_count
        self.processed_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)

    def mark_as_failed(self, failure_reason: str) -> None:
        """Transition from PENDING_PROCESSING or PROCESSING to FAILED."""
        self._assert_can_transition_to("FAILED", {"PENDING_PROCESSING", "PROCESSING"})
        self.status = "FAILED"
        self.failure_reason = failure_reason
        self.updated_at = datetime.now(timezone.utc)

    def _assert_can_transition_to(self, target: str, valid_from: set[str]) -> None:
        """Raise StudyDocumentError if the current status does not allow the transition."""
        if self.status not in valid_from:
            raise StudyDocumentError(
                f"Cannot transition from {self.status} to {target}",
                safe=True,
            )
