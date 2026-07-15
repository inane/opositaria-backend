"""Application DTOs for user authentication operations."""

from dataclasses import dataclass


@dataclass(frozen=True)
class AuthResponse:
    """Response returned after successful registration or login."""

    access_token: str
    token_type: str
    user: "UserPublicResponse"


@dataclass(frozen=True)
class UserPublicResponse:
    """Public user data returned in API responses.

    Excludes sensitive fields like password_hash.
    """

    id: str
    email: str
    created_at: str
    updated_at: str
