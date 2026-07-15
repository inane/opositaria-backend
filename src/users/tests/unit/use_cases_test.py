"""Unit tests for RegisterUserUseCase."""

import uuid

import pytest

from src.users.application.use_cases import (
    GetCurrentUserUseCase,
    LoginUserUseCase,
    RegisterUserUseCase,
)
from src.users.domain.entities import UserError
from src.users.domain.repositories import InMemoryUserRepository
from src.users.tests.unit.port_stubs import SpyTokenService, StubPasswordHasher


class TestRegisterUserUseCase:
    """Tests for user registration use case."""

    @pytest.mark.asyncio
    async def test_registers_user_with_valid_data(self) -> None:
        """A user is registered with normalized email, hashed password, and a token."""
        repo = InMemoryUserRepository()
        hasher = StubPasswordHasher()
        token_service = SpyTokenService()
        use_case = RegisterUserUseCase(
            user_repository=repo,
            password_hasher=hasher,
            token_service=token_service,
        )
        email = "student@example.com"
        password = "password123"

        result = await use_case.execute(email=email, password=password)

        # User is persisted
        saved_user = await repo.find_by_email(email)
        assert saved_user is not None
        assert saved_user.email == email
        # Password hash is not the plain password
        assert saved_user.password_hash != password
        assert saved_user.password_hash == "hashed:password123"

        # Auth response contains token
        assert result.access_token is not None
        assert result.token_type == "bearer"
        # Token references the saved user id
        assert token_service.validate_token(result.access_token) == str(saved_user.id)

        # Public user response has no password hash
        assert "password_hash" not in result.user.__dict__
        assert result.user.email == email

    @pytest.mark.asyncio
    async def test_rejects_duplicate_email(self) -> None:
        """Registering with an already-used email raises UserError."""
        repo = InMemoryUserRepository()
        hasher = StubPasswordHasher()
        token_service = SpyTokenService()
        use_case = RegisterUserUseCase(
            user_repository=repo,
            password_hasher=hasher,
            token_service=token_service,
        )
        email = "student@example.com"
        password = "password123"

        # Register first user
        await use_case.execute(email=email, password=password)

        # Attempt duplicate
        with pytest.raises(UserError) as exc_info:
            await use_case.execute(email=email, password=password)

        assert exc_info.value.code == "duplicate_email"

    @pytest.mark.asyncio
    async def test_rejects_duplicate_email_case_insensitive(self) -> None:
        """Registering with an email differing only by case is rejected."""
        repo = InMemoryUserRepository()
        hasher = StubPasswordHasher()
        token_service = SpyTokenService()
        use_case = RegisterUserUseCase(
            user_repository=repo,
            password_hasher=hasher,
            token_service=token_service,
        )

        # Register with lowercase
        await use_case.execute(email="student@example.com", password="password123")

        # Attempt with uppercase variant
        with pytest.raises(UserError) as exc_info:
            await use_case.execute(
                email="  Student@Example.COM  ", password="password123"
            )

        assert exc_info.value.code == "duplicate_email"

    @pytest.mark.asyncio
    async def test_rejects_invalid_email(self) -> None:
        """Registering with an invalid email raises ValueError."""
        repo = InMemoryUserRepository()
        hasher = StubPasswordHasher()
        token_service = SpyTokenService()
        use_case = RegisterUserUseCase(
            user_repository=repo,
            password_hasher=hasher,
            token_service=token_service,
        )

        with pytest.raises(ValueError, match="Invalid email address"):
            await use_case.execute(email="notanemail", password="password123")

    @pytest.mark.asyncio
    async def test_rejects_short_password(self) -> None:
        """Registering with a too-short password raises ValueError."""
        repo = InMemoryUserRepository()
        hasher = StubPasswordHasher()
        token_service = SpyTokenService()
        use_case = RegisterUserUseCase(
            user_repository=repo,
            password_hasher=hasher,
            token_service=token_service,
        )

        with pytest.raises(ValueError, match="Password must be at least"):
            await use_case.execute(email="student@example.com", password="short")


class TestLoginUserUseCase:
    """Tests for user login use case."""

    @pytest.mark.asyncio
    async def test_logs_in_with_valid_credentials(self) -> None:
        """A registered user can log in with correct credentials."""
        repo = InMemoryUserRepository()
        hasher = StubPasswordHasher()
        token_service = SpyTokenService()
        register_use_case = RegisterUserUseCase(
            user_repository=repo,
            password_hasher=hasher,
            token_service=token_service,
        )
        login_use_case = LoginUserUseCase(
            user_repository=repo,
            password_hasher=hasher,
            token_service=token_service,
        )

        await register_use_case.execute(
            email="student@example.com", password="password123"
        )

        result = await login_use_case.execute(
            email="student@example.com", password="password123"
        )

        assert result.access_token is not None
        assert result.token_type == "bearer"
        assert result.user.email == "student@example.com"

    @pytest.mark.asyncio
    async def test_rejects_unknown_email(self) -> None:
        """Login with an unregistered email raises UserError."""
        repo = InMemoryUserRepository()
        hasher = StubPasswordHasher()
        token_service = SpyTokenService()
        login_use_case = LoginUserUseCase(
            user_repository=repo,
            password_hasher=hasher,
            token_service=token_service,
        )

        with pytest.raises(UserError) as exc_info:
            await login_use_case.execute(
                email="unknown@example.com", password="password123"
            )

        assert exc_info.value.code == "invalid_credentials"

    @pytest.mark.asyncio
    async def test_rejects_incorrect_password(self) -> None:
        """Login with a wrong password raises UserError."""
        repo = InMemoryUserRepository()
        hasher = StubPasswordHasher()
        token_service = SpyTokenService()
        register_use_case = RegisterUserUseCase(
            user_repository=repo,
            password_hasher=hasher,
            token_service=token_service,
        )
        login_use_case = LoginUserUseCase(
            user_repository=repo,
            password_hasher=hasher,
            token_service=token_service,
        )

        await register_use_case.execute(
            email="student@example.com", password="password123"
        )

        with pytest.raises(UserError) as exc_info:
            await login_use_case.execute(
                email="student@example.com", password="wrongpassword"
            )

        assert exc_info.value.code == "invalid_credentials"

    @pytest.mark.asyncio
    async def test_normalizes_email_during_login(self) -> None:
        """Login normalizes email before lookup."""
        repo = InMemoryUserRepository()
        hasher = StubPasswordHasher()
        token_service = SpyTokenService()
        register_use_case = RegisterUserUseCase(
            user_repository=repo,
            password_hasher=hasher,
            token_service=token_service,
        )
        login_use_case = LoginUserUseCase(
            user_repository=repo,
            password_hasher=hasher,
            token_service=token_service,
        )

        await register_use_case.execute(
            email="student@example.com", password="password123"
        )

        result = await login_use_case.execute(
            email="  Student@Example.COM  ", password="password123"
        )

        assert result.user.email == "student@example.com"


class TestGetCurrentUserUseCase:
    """Tests for current-user lookup use case."""

    @pytest.mark.asyncio
    async def test_returns_user_for_valid_token(self) -> None:
        """A valid bearer token returns the authenticated user."""
        repo = InMemoryUserRepository()
        hasher = StubPasswordHasher()
        token_service = SpyTokenService()
        register_use_case = RegisterUserUseCase(
            user_repository=repo,
            password_hasher=hasher,
            token_service=token_service,
        )
        current_user_use_case = GetCurrentUserUseCase(
            user_repository=repo,
            token_service=token_service,
        )

        register_result = await register_use_case.execute(
            email="student@example.com", password="password123"
        )

        result = await current_user_use_case.execute(token=register_result.access_token)

        assert result.email == "student@example.com"
        assert result.id is not None

    @pytest.mark.asyncio
    async def test_rejects_invalid_token(self) -> None:
        """An invalid token raises UserError."""
        repo = InMemoryUserRepository()
        token_service = SpyTokenService()
        current_user_use_case = GetCurrentUserUseCase(
            user_repository=repo,
            token_service=token_service,
        )

        with pytest.raises(UserError) as exc_info:
            await current_user_use_case.execute(token="invalid-token")

        assert exc_info.value.code == "unauthorized"

    @pytest.mark.asyncio
    async def test_rejects_token_for_missing_user(self) -> None:
        """A token referencing a deleted user raises UserError."""
        repo = InMemoryUserRepository()
        token_service = SpyTokenService()
        current_user_use_case = GetCurrentUserUseCase(
            user_repository=repo,
            token_service=token_service,
        )

        # Issue token for a user id that doesn't exist in the repo
        token = token_service.issue_token(str(uuid.uuid4()))

        with pytest.raises(UserError) as exc_info:
            await current_user_use_case.execute(token=token)

        assert exc_info.value.code == "unauthorized"

    @pytest.mark.asyncio
    async def test_rejects_token_with_invalid_user_id(self) -> None:
        """A token with a malformed user id raises UserError."""
        repo = InMemoryUserRepository()
        token_service = SpyTokenService()
        current_user_use_case = GetCurrentUserUseCase(
            user_repository=repo,
            token_service=token_service,
        )
        token = token_service.issue_token("not-a-uuid")

        with pytest.raises(UserError) as exc_info:
            await current_user_use_case.execute(token=token)

        assert exc_info.value.code == "unauthorized"
