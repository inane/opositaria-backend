"""DocumentProcessingJob domain entity."""

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone


class DocumentProcessingError(Exception):
    """Domain error for document processing operations."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


@dataclass
class DocumentProcessingJob:
    """A job that tracks the asynchronous processing of a study document.

    Jobs flow through a lifecycle: PENDING → RUNNING → COMPLETED | FAILED.
    """

    id: uuid.UUID
    document_id: uuid.UUID
    status: str = "PENDING"
    attempts: int = 0
    failure_reason: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    completed_at: datetime | None = None

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
        document_id: uuid.UUID,
    ) -> "DocumentProcessingJob":
        """Create a processing job in PENDING state."""
        return cls(
            id=id,
            document_id=document_id,
        )

    def mark_as_running(self) -> None:
        """Transition from PENDING to RUNNING. Ignored if already in a terminal state."""
        if self.status in {"COMPLETED", "FAILED"}:
            return
        self.status = "RUNNING"
        self.updated_at = datetime.now(timezone.utc)

    def mark_as_completed(self) -> None:
        """Transition from RUNNING to COMPLETED."""
        self.status = "COMPLETED"
        self.completed_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)

    def mark_as_failed(self, failure_reason: str) -> None:
        """Transition from RUNNING to FAILED with reason and incremented attempt."""
        self.status = "FAILED"
        self.failure_reason = failure_reason
        self.attempts += 1
        self.updated_at = datetime.now(timezone.utc)
