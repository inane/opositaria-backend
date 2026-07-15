"""Application ports for external service adapters."""

from abc import abstractmethod
from typing import Protocol


class PasswordHasher(Protocol):
    """Port for password hashing and verification."""

    @abstractmethod
    def hash(self, plain_password: str) -> str:
        """Hash a plain password and return the hash string."""
        ...

    @abstractmethod
    def verify(self, plain_password: str, password_hash: str) -> bool:
        """Verify a plain password against a hash.

        Returns True if the password matches, False otherwise.
        """
        ...


class TokenService(Protocol):
    """Port for JWT bearer token issuing and validation."""

    @abstractmethod
    def issue_token(self, user_id: str) -> str:
        """Issue a bearer access token identifying the given user."""
        ...

    @abstractmethod
    def validate_token(self, token: str) -> str | None:
        """Validate a bearer token and return the user subject.

        Returns the user id as a string if valid, None otherwise.
        """
        ...
