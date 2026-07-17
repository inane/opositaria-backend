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
        self,
        embedding: list[float],
        limit: int,
        owner_id: uuid.UUID | None = None,
        study_space_id: uuid.UUID | None = None,
    ) -> list[ChunkSearchResult]:
        """Find the nearest chunks by embedding similarity, limited to READY documents.

        When owner_id is provided, only chunks from documents owned by that user are returned.
        When study_space_id is provided, only chunks from documents in that study space are returned.
        """
        ...
