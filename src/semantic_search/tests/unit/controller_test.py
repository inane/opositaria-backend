"""Unit tests for semantic search HTTP controller."""

import uuid
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI, status
from httpx import ASGITransport, AsyncClient

from src.semantic_search.domain.value_objects import SemanticSearchError
from src.users.application.use_cases import GetCurrentUserUseCase
from src.users.domain.entities import User


@pytest.fixture
def app():
    """Create a minimal FastAPI app with the semantic search router and auth override."""
    from src.semantic_search.infrastructure.controllers import router
    from src.semantic_search.infrastructure.controllers import (
        _get_search_use_case,
    )
    from src.users.infrastructure.controllers import (
        _get_current_user_use_case,
        get_bearer_token,
    )

    application = FastAPI()
    application.include_router(router)

    # Override auth to use a mock that returns a test user
    mock_auth_use_case = AsyncMock()
    mock_auth_use_case.execute.return_value = User(
        id=uuid.uuid4(),
        email="test@example.com",
        password_hash="hash",
    )

    application.dependency_overrides[get_bearer_token] = lambda: "test-token"
    application.dependency_overrides[_get_current_user_use_case] = lambda: mock_auth_use_case

    return application


@pytest.mark.asyncio
async def test_embedding_failure_returns_503(app: FastAPI) -> None:
    """When embedding generation fails, the API returns 503 Service Unavailable."""
    mock_use_case = AsyncMock()
    mock_use_case.execute.side_effect = SemanticSearchError(
        "Search service temporarily unavailable",
        error_type=SemanticSearchError.SERVICE,
    )

    from src.semantic_search.infrastructure.controllers import _get_search_use_case

    app.dependency_overrides[_get_search_use_case] = lambda: mock_use_case

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/semantic-search/search",
            params={"query": "derecho administrativo"},
            headers={"Authorization": "Bearer test-token"},
        )

    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert "Search service temporarily unavailable" in response.text


@pytest.mark.asyncio
async def test_validation_error_returns_422(app: FastAPI) -> None:
    """A validation error (e.g. blank query) returns 422 Unprocessable Entity."""
    mock_use_case = AsyncMock()
    mock_use_case.execute.side_effect = SemanticSearchError("Query must not be blank")

    from src.semantic_search.infrastructure.controllers import _get_search_use_case

    app.dependency_overrides[_get_search_use_case] = lambda: mock_use_case

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/semantic-search/search",
            params={"query": "   "},
            headers={"Authorization": "Bearer test-token"},
        )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
