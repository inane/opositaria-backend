"""Unit tests for semantic search HTTP controller."""

from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI, status
from httpx import ASGITransport, AsyncClient

from src.semantic_search.domain.value_objects import SemanticSearchError


@pytest.fixture
def app():
    """Create a minimal FastAPI app with the semantic search router."""
    from src.semantic_search.infrastructure.controllers import router

    application = FastAPI()
    application.include_router(router)
    return application


@pytest.mark.asyncio
async def test_embedding_failure_returns_503(app: FastAPI) -> None:
    """When embedding generation fails, the API returns 503 Service Unavailable."""
    mock_use_case = AsyncMock()
    mock_use_case.execute.side_effect = SemanticSearchError(
        "Search service temporarily unavailable",
        error_type=SemanticSearchError.SERVICE,
    )

    app.dependency_overrides = {}
    from src.semantic_search.infrastructure.controllers import _get_search_use_case

    app.dependency_overrides[_get_search_use_case] = lambda: mock_use_case

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/semantic-search/search",
            params={"query": "derecho administrativo"},
        )

    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert "Search service temporarily unavailable" in response.text


@pytest.mark.asyncio
async def test_validation_error_returns_422(app: FastAPI) -> None:
    """A validation error (e.g. blank query) returns 422 Unprocessable Entity."""
    mock_use_case = AsyncMock()
    mock_use_case.execute.side_effect = SemanticSearchError("Query must not be blank")

    app.dependency_overrides = {}
    from src.semantic_search.infrastructure.controllers import _get_search_use_case

    app.dependency_overrides[_get_search_use_case] = lambda: mock_use_case

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/semantic-search/search",
            params={"query": "   "},
        )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
