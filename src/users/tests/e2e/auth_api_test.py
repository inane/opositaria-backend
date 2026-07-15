"""E2E tests for user authentication API endpoints."""

import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from src.shared.infrastructure.factory import create_app


@pytest.fixture
def app():
    """Create a test app with full dependency wiring."""
    return create_app()


def _unique_email(prefix: str = "test") -> str:
    """Generate a unique email for test isolation."""
    return f"{prefix}-{uuid.uuid4().hex[:8]}@example.com"


@pytest.mark.asyncio
async def test_register_new_user_returns_201(app) -> None:
    """Registering a new user returns 201 with token and user data."""
    email = _unique_email()
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/auth/register",
            json={"email": email, "password": "password123"},
        )

    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == email
    assert "id" in data["user"]
    assert "password_hash" not in data["user"]
    assert "password" not in data["user"]


@pytest.mark.asyncio
async def test_register_duplicate_email_returns_409(app) -> None:
    """Registering with an existing email returns 409."""
    email = _unique_email("dup")
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        await client.post(
            "/auth/register",
            json={"email": email, "password": "password123"},
        )
        response = await client.post(
            "/auth/register",
            json={"email": email, "password": "password123"},
        )

    assert response.status_code == 409
    data = response.json()
    assert data["detail"]["code"] == "duplicate_email"


@pytest.mark.asyncio
async def test_register_invalid_email_returns_422(app) -> None:
    """Registering with an invalid email returns 422."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/auth/register",
            json={"email": "notanemail", "password": "password123"},
        )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_short_password_returns_422(app) -> None:
    """Registering with a short password returns 422."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/auth/register",
            json={"email": _unique_email("short"), "password": "short"},
        )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login_valid_credentials_returns_200(app) -> None:
    """Logging in with valid credentials returns 200 with token."""
    email = _unique_email("login")
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        # Register first
        await client.post(
            "/auth/register",
            json={"email": email, "password": "password123"},
        )
        # Login
        response = await client.post(
            "/auth/login",
            json={"email": email, "password": "password123"},
        )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == email


@pytest.mark.asyncio
async def test_login_unknown_email_returns_401(app) -> None:
    """Logging in with an unknown email returns 401."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/auth/login",
            json={"email": "unknown@example.com", "password": "password123"},
        )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_invalid_email_returns_401(app) -> None:
    """Logging in with an invalid email returns 401."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/auth/login",
            json={"email": "notanemail", "password": "password123"},
        )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_wrong_password_returns_401(app) -> None:
    """Logging in with wrong password returns 401."""
    email = _unique_email("wrongpw")
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        await client.post(
            "/auth/register",
            json={"email": email, "password": "password123"},
        )
        response = await client.post(
            "/auth/login",
            json={"email": email, "password": "wrongpassword"},
        )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_with_valid_token(app) -> None:
    """Accessing /auth/me with a valid token returns the user."""
    email = _unique_email("me")
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        register_resp = await client.post(
            "/auth/register",
            json={"email": email, "password": "password123"},
        )
        token = register_resp.json()["access_token"]

        response = await client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == email
    assert "password_hash" not in data


@pytest.mark.asyncio
async def test_get_current_user_without_token_returns_401(app) -> None:
    """Accessing /auth/me without credentials returns 401."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/auth/me")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_with_invalid_token_returns_401(app) -> None:
    """Accessing /auth/me with an invalid token returns 401."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(
            "/auth/me",
            headers={"Authorization": "Bearer invalidtoken123"},
        )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_auth_responses_never_include_password_hash(app) -> None:
    """All auth responses exclude password_hash from the response body."""
    email = _unique_email("pwcheck")
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        register_resp = await client.post(
            "/auth/register",
            json={"email": email, "password": "password123"},
        )
        token = register_resp.json()["access_token"]

        register_data = register_resp.json()
        assert "password_hash" not in register_data
        assert "password_hash" not in register_data["user"]

        login_resp = await client.post(
            "/auth/login",
            json={"email": email, "password": "password123"},
        )
        login_data = login_resp.json()
        assert "password_hash" not in login_data
        assert "password_hash" not in login_data["user"]

        me_resp = await client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        me_data = me_resp.json()
        assert "password_hash" not in me_data
