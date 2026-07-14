"""Application ports for semantic search."""

import uuid
from abc import abstractmethod
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class ChunkSearchResult:
    """A single result from a vector similarity search."""

    chunk_id: uuid.UUID
    document_id: uuid.UUID
    text: str
    score: float
    sequence_number: int
    page_number: int | None
    document_filename: str


class SemanticChunkSearchRepository(Protocol):
    """Port for semantic chunk search by vector similarity."""

    @abstractmethod
    async def find_nearest_by_embedding(
        self, embedding: list[float], limit: int
    ) -> list[ChunkSearchResult]:
        """Find the nearest chunks by embedding similarity, limited to READY documents."""
        ...
