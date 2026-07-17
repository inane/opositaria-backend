"""Unit tests for StudySpace domain entities."""

import uuid

import pytest

from src.study_spaces.domain.entities import StudySpace, StudySpaceError, StudySpaceName


class TestStudySpaceName:
    """Tests for StudySpaceName value object."""

    def test_creates_name_from_non_blank_value(self) -> None:
        """A non-blank value creates a valid StudySpaceName."""
        name = StudySpaceName("Derecho Administrativo")
        assert str(name) == "Derecho Administrativo"

    def test_preserves_whitespace_in_name(self) -> None:
        """A name with surrounding whitespace is preserved as-is."""
        name = StudySpaceName("  Derecho Civil  ")
        assert (
            str(name) == "  Derecho Civil  "
        )  # frozen=True, no __post_init__ normalization

    def test_rejects_blank_name(self) -> None:
        """A blank name is rejected with code invalid_name."""
        with pytest.raises(
            StudySpaceError, match="Study space name must not be blank"
        ) as exc:
            StudySpaceName("")
        assert exc.value.code == "invalid_name"

    def test_rejects_whitespace_only_name(self) -> None:
        """A whitespace-only name is rejected with code invalid_name."""
        with pytest.raises(StudySpaceError, match="Study space name must not be blank"):
            StudySpaceName("   ")


class TestStudySpace:
    """Tests for StudySpace entity creation."""

    def test_creates_study_space_with_owner_and_name_and_document(self) -> None:
        """A StudySpace is created with owner id, name, and one document id."""
        space_id = uuid.uuid4()
        owner_id = uuid.uuid4()
        doc_id = uuid.uuid4()

        space = StudySpace.create(
            id=space_id,
            owner_id=owner_id,
            name="Derecho Administrativo",
            document_ids=[doc_id],
        )

        assert space.id == space_id
        assert space.owner_id == owner_id
        assert str(space.name) == "Derecho Administrativo"
        assert space.document_ids == [doc_id]
        assert space.document_count == 1
        assert space.created_at is not None

    def test_requires_at_least_one_document_id(self) -> None:
        """A study space without document ids is rejected with code empty_documents."""
        with pytest.raises(
            StudySpaceError, match="At least one document is required"
        ) as exc:
            StudySpace.create(
                id=uuid.uuid4(),
                owner_id=uuid.uuid4(),
                name="Test",
                document_ids=[],
            )
        assert exc.value.code == "empty_documents"

    def test_deduplicates_document_ids(self) -> None:
        """Duplicate document ids are collapsed into unique ids."""
        doc_id = uuid.uuid4()
        space = StudySpace.create(
            id=uuid.uuid4(),
            owner_id=uuid.uuid4(),
            name="Test",
            document_ids=[doc_id, doc_id, doc_id],
        )

        assert len(space.document_ids) == 1
        assert space.document_ids == [doc_id]
        assert space.document_count == 1

    def test_rejects_blank_name(self) -> None:
        """A blank study space name is rejected."""
        with pytest.raises(StudySpaceError, match="Study space name must not be blank"):
            StudySpace.create(
                id=uuid.uuid4(),
                owner_id=uuid.uuid4(),
                name="",
                document_ids=[uuid.uuid4()],
            )
