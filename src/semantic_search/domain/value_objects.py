"""Semantic search domain value objects."""

from dataclasses import dataclass

DEFAULT_SEARCH_LIMIT = 10
MIN_SEARCH_LIMIT = 1
MAX_SEARCH_LIMIT = 50


class SemanticSearchError(Exception):
    """Domain error for semantic search operations."""

    VALIDATION = "validation"
    SERVICE = "service"

    def __init__(
        self, message: str, error_type: str = VALIDATION, code: str = ""
    ) -> None:
        self.message = message
        self.error_type = error_type
        self.code = code
        super().__init__(message)


@dataclass(frozen=True)
class SemanticQuery:
    """A validated semantic search query text."""

    text: str

    def __post_init__(self) -> None:
        """Validate that query text is not blank."""
        if not self.text.strip():
            raise SemanticSearchError("Query must not be blank")


@dataclass(frozen=True)
class SearchLimit:
    """A validated search result limit."""

    value: int = DEFAULT_SEARCH_LIMIT

    def __post_init__(self) -> None:
        """Validate that limit is within allowable range."""
        if not MIN_SEARCH_LIMIT <= self.value <= MAX_SEARCH_LIMIT:
            raise SemanticSearchError(
                f"Search limit must be between {MIN_SEARCH_LIMIT} and {MAX_SEARCH_LIMIT}"
            )


@dataclass(frozen=True)
class SimilarityScore:
    """A cosine similarity score from a semantic search result."""

    value: float
