"""Application ports for study document operations."""

import uuid
from abc import abstractmethod
from typing import Protocol


class DocumentStorage(Protocol):
    """Port for saving uploaded PDF bytes to a persistent store."""

    @abstractmethod
    async def save(self, document_id: uuid.UUID, filename: str, content: bytes) -> str:
        """Save uploaded file content and return a storage reference path."""
        ...


class ProcessingRequestPublisher(Protocol):
    """Port for publishing document processing requests to a message broker."""

    @abstractmethod
    async def publish(self, document_id: uuid.UUID, job_id: uuid.UUID) -> None:
        """Publish a processing request containing document and job identifiers."""
        ...
