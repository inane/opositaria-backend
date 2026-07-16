"""Unit tests for study space use cases."""

import uuid

import pytest

from src.study_documents.domain.entities import StudyDocument
from src.study_documents.domain.repositories import InMemoryStudyDocumentRepository
from src.study_spaces.application.use_cases import (
    CreateStudySpaceUseCase,
    ListStudySpacesUseCase,
)
from src.study_spaces.domain.entities import StudySpaceError
from src.study_spaces.domain.repositories import InMemoryStudySpaceRepository


class TestCreateStudySpaceUseCase:
    """Tests for CreateStudySpaceUseCase."""

    @pytest.mark.asyncio
    async def test_creates_space_from_ready_owned_document(self) -> None:
        """An owner creates a study space from one ready owned document."""
        space_repo = InMemoryStudySpaceRepository()
        doc_repo = InMemoryStudyDocumentRepository()
        owner_id = uuid.uuid4()
        doc = StudyDocument.create(
            id=uuid.uuid4(),
            filename="test.pdf",
            content_type="application/pdf",
            storage_path="study_documents/test.pdf",
            owner_user_id=owner_id,
        )
        doc.mark_as_processing()
        doc.mark_as_ready(chunk_count=5)
        await doc_repo.save(doc)

        use_case = CreateStudySpaceUseCase(
            space_repository=space_repo,
            document_repository=doc_repo,
        )
        response = await use_case.execute(
            owner_id=owner_id,
            name="Derecho Administrativo",
            document_ids=[doc.id],
        )

        assert response.name == "Derecho Administrativo"
        assert response.document_count == 1
        assert response.id is not None
        assert response.created_at is not None

        # Verify it's persisted
        saved = await space_repo.find_by_id(response.id)
        assert saved is not None

    @pytest.mark.asyncio
    async def test_rejects_blank_name(self) -> None:
        """A blank name maps to invalid_name error."""
        space_repo = InMemoryStudySpaceRepository()
        doc_repo = InMemoryStudyDocumentRepository()

        use_case = CreateStudySpaceUseCase(
            space_repository=space_repo,
            document_repository=doc_repo,
        )
        with pytest.raises(StudySpaceError, match="Study space name must not be blank") as exc:
            await use_case.execute(
                owner_id=uuid.uuid4(),
                name="",
                document_ids=[uuid.uuid4()],
            )
        assert exc.value.code == "invalid_name"

    @pytest.mark.asyncio
    async def test_rejects_empty_document_list(self) -> None:
        """An empty document list maps to empty_documents error."""
        space_repo = InMemoryStudySpaceRepository()
        doc_repo = InMemoryStudyDocumentRepository()

        use_case = CreateStudySpaceUseCase(
            space_repository=space_repo,
            document_repository=doc_repo,
        )
        with pytest.raises(StudySpaceError, match="At least one document is required") as exc:
            await use_case.execute(
                owner_id=uuid.uuid4(),
                name="Test",
                document_ids=[],
            )
        assert exc.value.code == "empty_documents"

    @pytest.mark.asyncio
    async def test_rejects_missing_document(self) -> None:
        """A missing document maps to document_not_found error."""
        space_repo = InMemoryStudySpaceRepository()
        doc_repo = InMemoryStudyDocumentRepository()

        use_case = CreateStudySpaceUseCase(
            space_repository=space_repo,
            document_repository=doc_repo,
        )
        with pytest.raises(StudySpaceError, match="Document not found") as exc:
            await use_case.execute(
                owner_id=uuid.uuid4(),
                name="Test",
                document_ids=[uuid.uuid4()],
            )
        assert exc.value.code == "document_not_found"

    @pytest.mark.asyncio
    async def test_rejects_foreign_document(self) -> None:
        """A foreign document maps to document_not_found error."""
        space_repo = InMemoryStudySpaceRepository()
        doc_repo = InMemoryStudyDocumentRepository()
        owner_id = uuid.uuid4()
        other_owner = uuid.uuid4()
        doc = StudyDocument.create(
            id=uuid.uuid4(),
            filename="test.pdf",
            content_type="application/pdf",
            storage_path="study_documents/test.pdf",
            owner_user_id=other_owner,
        )
        await doc_repo.save(doc)

        use_case = CreateStudySpaceUseCase(
            space_repository=space_repo,
            document_repository=doc_repo,
        )
        with pytest.raises(StudySpaceError, match="Document not found") as exc:
            await use_case.execute(
                owner_id=owner_id,
                name="Test",
                document_ids=[doc.id],
            )
        assert exc.value.code == "document_not_found"

    @pytest.mark.asyncio
    async def test_rejects_pending_document(self) -> None:
        """A pending document maps to document_not_ready error."""
        space_repo = InMemoryStudySpaceRepository()
        doc_repo = InMemoryStudyDocumentRepository()
        owner_id = uuid.uuid4()
        doc = StudyDocument.create(
            id=uuid.uuid4(),
            filename="test.pdf",
            content_type="application/pdf",
            storage_path="study_documents/test.pdf",
            owner_user_id=owner_id,
        )
        await doc_repo.save(doc)

        use_case = CreateStudySpaceUseCase(
            space_repository=space_repo,
            document_repository=doc_repo,
        )
        with pytest.raises(StudySpaceError, match="Document is not ready") as exc:
            await use_case.execute(
                owner_id=owner_id,
                name="Test",
                document_ids=[doc.id],
            )
        assert exc.value.code == "document_not_ready"

    @pytest.mark.asyncio
    async def test_rejects_failed_document(self) -> None:
        """A failed document maps to document_not_ready error."""
        space_repo = InMemoryStudySpaceRepository()
        doc_repo = InMemoryStudyDocumentRepository()
        owner_id = uuid.uuid4()
        doc = StudyDocument.create(
            id=uuid.uuid4(),
            filename="test.pdf",
            content_type="application/pdf",
            storage_path="study_documents/test.pdf",
            owner_user_id=owner_id,
        )
        doc.mark_as_failed("Processing error")
        await doc_repo.save(doc)

        use_case = CreateStudySpaceUseCase(
            space_repository=space_repo,
            document_repository=doc_repo,
        )
        with pytest.raises(StudySpaceError, match="Document is not ready") as exc:
            await use_case.execute(
                owner_id=owner_id,
                name="Test",
                document_ids=[doc.id],
            )
        assert exc.value.code == "document_not_ready"


class TestListStudySpacesUseCase:
    """Tests for ListStudySpacesUseCase."""

    @pytest.mark.asyncio
    async def test_returns_only_owner_spaces(self) -> None:
        """Listing returns only the owner's study spaces."""
        space_repo = InMemoryStudySpaceRepository()
        owner_id = uuid.uuid4()
        other_owner = uuid.uuid4()

        from src.study_spaces.domain.entities import StudySpace as SS
        s1 = SS.create(id=uuid.uuid4(), owner_id=owner_id, name="Mine", document_ids=[uuid.uuid4()])
        s2 = SS.create(id=uuid.uuid4(), owner_id=other_owner, name="Theirs", document_ids=[uuid.uuid4()])
        await space_repo.save(s1)
        await space_repo.save(s2)

        use_case = ListStudySpacesUseCase(space_repository=space_repo)
        result = await use_case.execute(owner_id=owner_id)

        assert len(result) == 1
        assert result[0].name == "Mine"

    @pytest.mark.asyncio
    async def test_returns_newest_spaces_first(self) -> None:
        """The list is ordered with newest study spaces first."""
        space_repo = InMemoryStudySpaceRepository()
        owner_id = uuid.uuid4()

        from src.study_spaces.domain.entities import StudySpace as SS
        import datetime
        from datetime import timezone

        s1 = SS.create(id=uuid.uuid4(), owner_id=owner_id, name="First", document_ids=[uuid.uuid4()])
        s1.created_at = datetime.datetime(2024, 1, 1, tzinfo=timezone.utc)
        s2 = SS.create(id=uuid.uuid4(), owner_id=owner_id, name="Second", document_ids=[uuid.uuid4()])
        s2.created_at = datetime.datetime(2025, 1, 1, tzinfo=timezone.utc)
        await space_repo.save(s1)
        await space_repo.save(s2)

        use_case = ListStudySpacesUseCase(space_repository=space_repo)
        result = await use_case.execute(owner_id=owner_id)

        assert len(result) == 2
        assert result[0].name == "Second"
        assert result[1].name == "First"

    @pytest.mark.asyncio
    async def test_returns_empty_list_for_no_spaces(self) -> None:
        """A user with no study spaces gets an empty list."""
        space_repo = InMemoryStudySpaceRepository()

        use_case = ListStudySpacesUseCase(space_repository=space_repo)
        result = await use_case.execute(owner_id=uuid.uuid4())

        assert result == []