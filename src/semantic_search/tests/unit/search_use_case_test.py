"""Unit tests for SemanticSearchUseCase."""

import uuid
from dataclasses import dataclass, field

import pytest

from src.semantic_search.application.dtos import SemanticSearchResponse
from src.semantic_search.application.ports import (
    ChunkSearchResult,
)
from src.semantic_search.application.use_cases import (
    SemanticSearchUseCase,
)
from src.semantic_search.domain.value_objects import SemanticSearchError


@dataclass
class EmbeddingGeneratorStub:
    """Stub that returns a fixed-dimension embedding."""

    dimension: int = 384
    should_fail: bool = False

    async def generate(self, text: str) -> list[float]:
        if self.should_fail:
            raise RuntimeError("Embedding model failed to load")
        return [0.1] * self.dimension


@dataclass
class SearchRepositoryStub:
    """Stub that returns fixed search results."""

    results: list[ChunkSearchResult] = field(default_factory=list)

    async def find_nearest_by_embedding(
        self,
        embedding: list[float],
        limit: int,
        owner_id: uuid.UUID | None = None,
        study_space_id: uuid.UUID | None = None,
    ) -> list[ChunkSearchResult]:
        return self.results[:limit]


class TestSemanticSearchUseCase:
    """Tests for SemanticSearchUseCase."""

    @pytest.mark.asyncio
    async def test_returns_ordered_chunk_matches_with_parent_documents(self) -> None:
        """A valid query returns ordered chunk matches with parent document metadata."""
        document_id = uuid.uuid4()
        chunk_id = uuid.uuid4()
        repo = SearchRepositoryStub(
            results=[
                ChunkSearchResult(
                    chunk_id=chunk_id,
                    document_id=document_id,
                    text="Derecho administrativo regula la administración pública.",
                    score=0.92,
                    sequence_number=1,
                    page_number=1,
                    document_filename="admin-law.pdf",
                ),
            ]
        )
        use_case = SemanticSearchUseCase(
            search_repository=repo,
            embedding_generator=EmbeddingGeneratorStub(),
        )

        response = await use_case.execute(query_text="derecho administrativo")

        assert isinstance(response, SemanticSearchResponse)
        assert len(response.results) == 1
        assert (
            response.results[0].text
            == "Derecho administrativo regula la administración pública."
        )
        assert response.results[0].document_filename == "admin-law.pdf"
        assert response.results[0].score == 0.92

    @pytest.mark.asyncio
    async def test_rejects_blank_query(self) -> None:
        """A blank query is rejected before embedding generation."""
        use_case = SemanticSearchUseCase(
            search_repository=SearchRepositoryStub(),
            embedding_generator=EmbeddingGeneratorStub(),
        )

        with pytest.raises(SemanticSearchError, match="Query must not be blank"):
            await use_case.execute(query_text="   ")

    @pytest.mark.asyncio
    async def test_applies_default_limit_when_omitted(self) -> None:
        """When limit is omitted, the default limit is applied."""
        repo = SearchRepositoryStub(
            results=[
                ChunkSearchResult(
                    chunk_id=uuid.uuid4(),
                    document_id=uuid.uuid4(),
                    text="Chunk",
                    score=0.5,
                    sequence_number=1,
                    page_number=None,
                    document_filename="test.pdf",
                ),
            ]
        )
        use_case = SemanticSearchUseCase(
            search_repository=repo,
            embedding_generator=EmbeddingGeneratorStub(),
        )

        response = await use_case.execute(query_text="test")

        assert response.limit == 10

    @pytest.mark.asyncio
    async def test_rejects_invalid_limit(self) -> None:
        """An invalid limit is rejected."""
        use_case = SemanticSearchUseCase(
            search_repository=SearchRepositoryStub(),
            embedding_generator=EmbeddingGeneratorStub(),
        )

        with pytest.raises(SemanticSearchError, match="must be between 1 and 50"):
            await use_case.execute(query_text="test", limit=100)

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_no_ready_chunks(self) -> None:
        """When no ready chunks exist, an empty result list is returned."""
        use_case = SemanticSearchUseCase(
            search_repository=SearchRepositoryStub(results=[]),
            embedding_generator=EmbeddingGeneratorStub(),
        )

        response = await use_case.execute(query_text="test")

        assert response.results == []

    @pytest.mark.asyncio
    async def test_returns_safe_error_on_embedding_failure(self) -> None:
        """When embedding generation fails, a safe error is returned without exposing internals."""
        use_case = SemanticSearchUseCase(
            search_repository=SearchRepositoryStub(),
            embedding_generator=EmbeddingGeneratorStub(should_fail=True),
        )

        with pytest.raises(
            SemanticSearchError, match="Search service temporarily unavailable"
        ):
            await use_case.execute(query_text="test")

    @pytest.mark.asyncio
    async def test_rejects_foreign_study_space(self) -> None:
        """Searching a foreign study space raises validation error."""
        from src.study_spaces.domain.repositories import InMemoryStudySpaceRepository
        from src.study_spaces.domain.entities import StudySpace as SS

        space_repo = InMemoryStudySpaceRepository()
        owner_id = uuid.uuid4()
        other_owner = uuid.uuid4()
        space_id = uuid.uuid4()

        space = SS.create(
            id=space_id,
            owner_id=other_owner,
            name="Theirs",
            document_ids=[uuid.uuid4()],
        )
        await space_repo.save(space)

        use_case = SemanticSearchUseCase(
            search_repository=SearchRepositoryStub(),
            embedding_generator=EmbeddingGeneratorStub(),
            space_repository=space_repo,
        )

        with pytest.raises(SemanticSearchError, match="Study space not found"):
            await use_case.execute(
                query_text="test",
                owner_id=owner_id,
                study_space_id=space_id,
            )

    @pytest.mark.asyncio
    async def test_rejects_missing_study_space(self) -> None:
        """Searching a non-existent study space raises validation error."""
        from src.study_spaces.domain.repositories import InMemoryStudySpaceRepository

        space_repo = InMemoryStudySpaceRepository()

        use_case = SemanticSearchUseCase(
            search_repository=SearchRepositoryStub(),
            embedding_generator=EmbeddingGeneratorStub(),
            space_repository=space_repo,
        )

        with pytest.raises(SemanticSearchError, match="Study space not found"):
            await use_case.execute(
                query_text="test",
                owner_id=uuid.uuid4(),
                study_space_id=uuid.uuid4(),
            )

    @pytest.mark.asyncio
    async def test_accepts_owned_study_space(self) -> None:
        """Searching an owned study space succeeds."""
        from src.study_spaces.domain.repositories import InMemoryStudySpaceRepository
        from src.study_spaces.domain.entities import StudySpace as SS

        space_repo = InMemoryStudySpaceRepository()
        owner_id = uuid.uuid4()
        space_id = uuid.uuid4()

        space = SS.create(
            id=space_id, owner_id=owner_id, name="Mine", document_ids=[uuid.uuid4()]
        )
        await space_repo.save(space)

        use_case = SemanticSearchUseCase(
            search_repository=SearchRepositoryStub(),
            embedding_generator=EmbeddingGeneratorStub(),
            space_repository=space_repo,
        )

        response = await use_case.execute(
            query_text="test",
            owner_id=owner_id,
            study_space_id=space_id,
        )

        assert response is not None
        assert len(response.results) == 0
