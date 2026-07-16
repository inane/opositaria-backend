"""StudySpace domain entity, value objects, and errors."""

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone


class StudySpaceError(Exception):
    """Domain error for study space operations."""

    def __init__(self, message: str, *, safe: bool = False, code: str = "") -> None:
        self.message = message
        self.safe = safe
        self.code = code
        super().__init__(message)


@dataclass(frozen=True)
class StudySpaceName:
    """A validated non-blank study space name."""

    value: str

    def __post_init__(self) -> None:
        if not self.value or not self.value.strip():
            raise StudySpaceError(
                "Study space name must not be blank",
                safe=True,
                code="invalid_name",
            )

    def __str__(self) -> str:
        return self.value


@dataclass
class StudySpace:
    """A study space owned by an authenticated user, backed by ready documents."""

    id: uuid.UUID
    owner_id: uuid.UUID
    name: StudySpaceName
    document_ids: list[uuid.UUID]
    document_count: int = 0
    created_at: datetime | None = None

    def __post_init__(self) -> None:
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)
        self.document_count = len(self.document_ids)

    @classmethod
    def create(
        cls,
        id: uuid.UUID,
        owner_id: uuid.UUID,
        name: str,
        document_ids: list[uuid.UUID],
    ) -> "StudySpace":
        """Create a validated StudySpace.

        Raises StudySpaceError if validation fails.
        """
        validated_name = StudySpaceName(name)
        if not document_ids:
            raise StudySpaceError(
                "At least one document is required",
                safe=True,
                code="empty_documents",
            )
        # Deduplicate document IDs
        unique_ids = list(dict.fromkeys(document_ids))
        return cls(
            id=id,
            owner_id=owner_id,
            name=validated_name,
            document_ids=unique_ids,
        )