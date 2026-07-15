"""Application use cases for user authentication."""

import uuid

from src.users.application.dtos import AuthResponse, UserPublicResponse
from src.users.application.ports import PasswordHasher, TokenService
from src.users.domain.entities import User, UserError
from src.users.domain.repositories import UserRepository
from src.users.domain.value_objects import EmailAddress, PlainPassword


class RegisterUserUseCase:
    """Register a new user with email and password.

    Validates input, normalizes the email, hashes the password,
    persists the user, and returns a bearer access token.
    """

    def __init__(
        self,
        user_repository: UserRepository,
        password_hasher: PasswordHasher,
        token_service: TokenService,
    ) -> None:
        self._user_repository = user_repository
        self._password_hasher = password_hasher
        self._token_service = token_service

    async def execute(self, email: str, password: str) -> AuthResponse:
        """Register a new user and return an auth response with a bearer token."""
        email_obj = EmailAddress(email)
        normalized_email = email_obj.value
        PlainPassword(password)
        existing = await self._user_repository.find_by_email(normalized_email)
        if existing is not None:
            raise UserError("Email already registered", code="duplicate_email")
        password_hash = self._password_hasher.hash(password)
        user = User.create(
            id=uuid.uuid4(),
            email=normalized_email,
            password_hash=password_hash,
        )

        await self._user_repository.save(user)
        access_token = self._token_service.issue_token(str(user.id))

        return AuthResponse(
            access_token=access_token,
            token_type="bearer",
            user=_create_user_public_response(user),
        )


class LoginUserUseCase:
    """Authenticate a user with email and password.

    Validates credentials, returns a bearer access token,
    and raises UserError for invalid credentials.
    """

    def __init__(
        self,
        user_repository: UserRepository,
        password_hasher: PasswordHasher,
        token_service: TokenService,
    ) -> None:
        self._user_repository = user_repository
        self._password_hasher = password_hasher
        self._token_service = token_service

    async def execute(self, email: str, password: str) -> AuthResponse:
        """Authenticate a user and return an auth response."""
        normalized_email = EmailAddress(email).value

        user = await self._user_repository.find_by_email(normalized_email)
        if user is None or not self._password_hasher.verify(
            password, user.password_hash
        ):
            raise UserError("Invalid credentials", code="invalid_credentials")

        access_token = self._token_service.issue_token(str(user.id))

        return AuthResponse(
            access_token=access_token,
            token_type="bearer",
            user=_create_user_public_response(user),
        )


class GetCurrentUserUseCase:
    """Resolve the authenticated user from a bearer token."""

    def __init__(
        self,
        user_repository: UserRepository,
        token_service: TokenService,
    ) -> None:
        self._user_repository = user_repository
        self._token_service = token_service

    async def execute(self, token: str) -> UserPublicResponse:
        """Resolve and return the current user from a bearer token."""
        user_id = self._token_service.validate_token(token)
        if user_id is None:
            raise UserError("Unauthorized", code="unauthorized")

        try:
            user_uuid = uuid.UUID(user_id)
        except ValueError as error:
            raise UserError("Unauthorized", code="unauthorized") from error

        user = await self._user_repository.find_by_id(user_uuid)
        if user is None:
            raise UserError("Unauthorized", code="unauthorized")

        return _create_user_public_response(user)


def _create_user_public_response(user: User) -> UserPublicResponse:
    return UserPublicResponse(
        id=str(user.id),
        email=user.email,
        created_at=user.created_at.isoformat() if user.created_at else "",
        updated_at=user.updated_at.isoformat() if user.updated_at else "",
    )
