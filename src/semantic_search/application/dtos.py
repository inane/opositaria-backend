"""Application DTOs for semantic search."""

import uuid
from dataclasses import dataclass


@dataclass(frozen=True)
class MatchedChunk:
    """A single matched chunk from a semantic search result."""

    chunk_id: uuid.UUID
    document_id: uuid.UUID
    text: str
    score: float
    sequence_number: int
    page_number: int | None = None
    document_filename: str = ""


@dataclass(frozen=True)
class SemanticSearchResponse:
    """Response containing semantic search results."""

    query: str
    results: list[MatchedChunk]
    limit: int
