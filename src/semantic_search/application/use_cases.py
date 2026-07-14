"""Application use case for semantic search."""

from src.document_processing.application.ports import EmbeddingGenerator
from src.semantic_search.application.dtos import MatchedChunk, SemanticSearchResponse
from src.semantic_search.application.ports import SemanticChunkSearchRepository
from src.semantic_search.domain.value_objects import SemanticQuery, SearchLimit, SemanticSearchError


class SearchStudyDocumentsSemanticallyUseCase:
    """Orchestrates semantic search: validate query, generate embedding, find nearest chunks."""

    def __init__(
        self,
        search_repository: SemanticChunkSearchRepository,
        embedding_generator: EmbeddingGenerator,
    ) -> None:
        self._search_repository = search_repository
        self._embedding_generator = embedding_generator

    async def execute(
        self,
        query_text: str,
        limit: int | None = None,
    ) -> SemanticSearchResponse:
        """Execute a semantic search query."""
        query = SemanticQuery(query_text)
        search_limit = SearchLimit(limit) if limit is not None else SearchLimit()

        try:
            embedding = await self._embedding_generator.generate(query.text)
        except Exception as e:
            raise SemanticSearchError(
                "Search service temporarily unavailable",
                error_type=SemanticSearchError.SERVICE,
            ) from e

        results = await self._search_repository.find_nearest_by_embedding(
            embedding=embedding,
            limit=search_limit.value,
        )

        return SemanticSearchResponse(
            query=query.text,
            limit=search_limit.value,
            results=[
                MatchedChunk(
                    chunk_id=r.chunk_id,
                    document_id=r.document_id,
                    text=r.text,
                    score=r.score,
                    sequence_number=r.sequence_number,
                    page_number=r.page_number,
                    document_filename=r.document_filename,
                )
                for r in results
            ],
        )
