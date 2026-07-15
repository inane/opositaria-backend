"""Tests for the reusable current-user dependency pattern.

These tests verify that the get_bearer_token function can be imported
and used by future modules to protect their endpoints.
"""

import pytest
from httpx import ASGITransport, AsyncClient

from src.shared.infrastructure.factory import create_app
from src.users.infrastructure.controllers import get_bearer_token


class TestGetBearerToken:
    """Tests for the reusable bearer token extraction function."""

    def test_importable_from_controllers(self) -> None:
        """The get_bearer_token function is importable by future modules."""
        assert get_bearer_token is not None
        assert callable(get_bearer_token)


@pytest.mark.asyncio
async def test_protected_endpoint_with_valid_token() -> None:
    """A protected endpoint receives the authenticated user via the reusable dependency.

    In this system, the /auth/me endpoint uses the get_bearer_token dependency
    and the GetCurrentUserUseCase. Future modules can import get_bearer_token
    from src.users.infrastructure.controllers and use it the same way.
    """
    app = create_app()
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        register_resp = await client.post(
            "/auth/register",
            json={"email": "future-module-test@example.com", "password": "password123"},
        )
        token = register_resp.json()["access_token"]

        response = await client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    assert response.json()["email"] == "future-module-test@example.com"


@pytest.mark.asyncio
async def test_protected_endpoint_rejects_missing_token() -> None:
    """A protected endpoint using the reusable dependency rejects requests without tokens."""
    app = create_app()
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/auth/me")

    assert response.status_code == 401
