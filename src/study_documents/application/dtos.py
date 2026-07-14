"""Application DTOs for study document operations."""

import uuid
from dataclasses import dataclass


@dataclass(frozen=True)
class UploadDocumentResponse:
    """Response returned after a successful PDF upload."""

    document_id: uuid.UUID
    status: str


@dataclass(frozen=True)
class DocumentStatusResponse:
    """Document status with processing lifecycle information."""

    document_id: uuid.UUID
    filename: str
    status: str
    failure_reason: str | None = None
    chunks_count: int = 0


@dataclass(frozen=True)
class UploadError:
    """Structured error response for upload validation failures.

    Exposes only a stable error code and a user-safe message.
    """

    code: str
    message: str
