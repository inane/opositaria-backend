"""User domain entity."""

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone


class UserError(Exception):
    """Domain error for user operations."""

    def __init__(self, message: str, *, code: str = "") -> None:
        self.message = message
        self.code = code
        super().__init__(message)


@dataclass
class User:
    """A registered user of the system.

    Users are created through registration and identified by a unique
    identifier. The email is stored normalized (lowercased, trimmed).
    """

    id: uuid.UUID
    email: str
    password_hash: str
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        """Set timestamps on creation."""
        now = datetime.now(timezone.utc)
        if self.created_at is None:
            self.created_at = now
        if self.updated_at is None:
            self.updated_at = now

    @classmethod
    def create(
        cls,
        id: uuid.UUID,
        email: str,
        password_hash: str,
    ) -> "User":
        """Create a validated User."""
        return cls(
            id=id,
            email=email,
            password_hash=password_hash,
        )

    def to_public_dict(self) -> dict[str, str]:
        """Return a public representation without sensitive fields."""
        return {
            "id": str(self.id),
            "email": self.email,
            "created_at": self.created_at.isoformat() if self.created_at else "",
            "updated_at": self.updated_at.isoformat() if self.updated_at else "",
        }
