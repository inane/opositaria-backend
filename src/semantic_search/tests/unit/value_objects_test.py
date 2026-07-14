"""Unit tests for semantic search domain value objects."""

import pytest

from src.semantic_search.domain.value_objects import (
    SemanticQuery,
    SearchLimit,
    SimilarityScore,
    SemanticSearchError,
)


class TestSemanticQuery:
    """Tests for SemanticQuery value object."""

    def test_creates_valid_non_blank_query(self) -> None:
        """A valid non-blank query is accepted."""
        query = SemanticQuery("derecho administrativo")

        assert query.text == "derecho administrativo"

    def test_rejects_blank_query(self) -> None:
        """A blank query is rejected."""
        with pytest.raises(SemanticSearchError, match="Query must not be blank"):
            SemanticQuery("   ")


class TestSearchLimit:
    """Tests for SearchLimit value object."""

    def test_applies_default_limit_when_omitted(self) -> None:
        """Default limit is applied when no value is provided."""
        limit = SearchLimit()

        assert limit.value == 10

    def test_accepts_valid_limit(self) -> None:
        """A valid limit within range is accepted."""
        limit = SearchLimit(25)

        assert limit.value == 25

    def test_rejects_limit_below_minimum(self) -> None:
        """A limit below the minimum is rejected."""
        with pytest.raises(SemanticSearchError, match="must be between 1 and 50"):
            SearchLimit(0)

    def test_rejects_limit_above_maximum(self) -> None:
        """A limit above the maximum is rejected."""
        with pytest.raises(SemanticSearchError, match="must be between 1 and 50"):
            SearchLimit(100)


class TestSimilarityScore:
    """Tests for SimilarityScore value object."""

    def test_creates_valid_score(self) -> None:
        """A valid similarity score is accepted."""
        score = SimilarityScore(0.85)

        assert score.value == 0.85
