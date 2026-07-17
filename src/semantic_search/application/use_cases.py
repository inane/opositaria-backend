"""Semantic search use cases."""

import uuid

from src.document_processing.application.ports import EmbeddingGenerator
from src.semantic_search.application.dtos import MatchedChunk, SemanticSearchResponse
from src.semantic_search.application.ports import SemanticChunkSearchRepository
from src.semantic_search.domain.value_objects import (
    SemanticQuery,
    SearchLimit,
    SemanticSearchError,
)
from src.study_spaces.domain.repositories import StudySpaceRepository


class SemanticSearchUseCase:
    def __init__(
        self,
        search_repository: SemanticChunkSearchRepository,
        embedding_generator: EmbeddingGenerator,
        space_repository: StudySpaceRepository | None = None,
    ) -> None:
        self._search_repository = search_repository
        self._embedding_generator = embedding_generator
        self._space_repository = space_repository

    async def execute(
        self,
        query_text: str,
        limit: int | None = None,
        owner_id: uuid.UUID | None = None,
        study_space_id: uuid.UUID | None = None,
    ) -> SemanticSearchResponse:
        query = SemanticQuery(query_text)
        search_limit = SearchLimit(limit) if limit is not None else SearchLimit()

        # Validate space ownership if study_space_id is provided
        if (
            study_space_id is not None
            and owner_id is not None
            and self._space_repository is not None
        ):
            space = await self._space_repository.find_by_id_and_owner(
                study_space_id, owner_id
            )
            if space is None:
                raise SemanticSearchError(
                    "Study space not found",
                    error_type=SemanticSearchError.VALIDATION,
                    code="space_not_found",
                )

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
            owner_id=owner_id,
            study_space_id=study_space_id,
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
