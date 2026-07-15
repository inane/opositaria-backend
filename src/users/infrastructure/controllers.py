"""FastAPI controllers for user authentication.

## Reusing the current-user dependency in other modules

Future modules can protect their endpoints by importing:

    from src.users.infrastructure.controllers import get_bearer_token

Then using it as a FastAPI dependency:

    from fastapi import Depends
    from src.users.infrastructure.controllers import get_bearer_token

    @router.get("/protected")
    async def protected_endpoint(
        token: str = Depends(get_bearer_token),
    ):
        # token is the validated bearer token string
        ...

For full user resolution (not just the token), inject a GetCurrentUserUseCase
via the factory pattern used in this module.
"""

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel

from src.users.application.dtos import AuthResponse, UserPublicResponse
from src.users.application.use_cases import (
    GetCurrentUserUseCase,
    LoginUserUseCase,
    RegisterUserUseCase,
)
from src.users.domain.entities import UserError

router = APIRouter(prefix="/auth", tags=["auth"])


class AuthRequest(BaseModel):
    email: str
    password: str


async def _get_register_use_case() -> RegisterUserUseCase:
    """Placeholder - overridden by factory."""
    raise NotImplementedError


async def _get_login_use_case() -> LoginUserUseCase:
    """Placeholder - overridden by factory."""
    raise NotImplementedError


async def _get_current_user_use_case() -> GetCurrentUserUseCase:
    """Placeholder - overridden by factory."""
    raise NotImplementedError


async def get_bearer_token(
    authorization: str | None = Header(None),
) -> str:
    """Extract the bearer token from the Authorization header."""
    if authorization is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "unauthorized", "message": "Missing authorization header"},
        )
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "unauthorized", "message": "Invalid authorization header"},
        )
    return parts[1]


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    response_model=AuthResponse,
)
async def register(
    body: AuthRequest,
    use_case: RegisterUserUseCase = Depends(_get_register_use_case),
) -> AuthResponse:
    """Register a new user with email and password."""
    try:
        return await use_case.execute(
            email=body.email,
            password=body.password,
        )
    except UserError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": e.code, "message": e.message},
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={"message": str(e)},
        )


@router.post("/login", response_model=AuthResponse)
async def login(
    body: AuthRequest,
    use_case: LoginUserUseCase = Depends(_get_login_use_case),
) -> AuthResponse:
    """Authenticate a user with email and password."""
    try:
        return await use_case.execute(
            email=body.email,
            password=body.password,
        )
    except UserError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": e.code, "message": e.message},
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "invalid_credentials", "message": "Invalid credentials"},
        )


@router.get("/me", response_model=UserPublicResponse)
async def get_current_user(
    use_case: GetCurrentUserUseCase = Depends(_get_current_user_use_case),
    authorization: str = Depends(get_bearer_token),
) -> UserPublicResponse:
    """Get the current authenticated user."""
    try:
        return await use_case.execute(token=authorization)
    except UserError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": e.code, "message": e.message},
        )
