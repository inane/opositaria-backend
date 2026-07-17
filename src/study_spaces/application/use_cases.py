"""Application use cases for study spaces."""

import uuid
from datetime import datetime, timezone

from src.study_documents.domain.repositories import StudyDocumentRepository
from src.study_spaces.domain.entities import StudySpace, StudySpaceError
from src.study_spaces.domain.repositories import StudySpaceRepository
from src.study_spaces.application.dtos import (
    CreateStudySpaceResponse,
    StudySpaceDocumentSummary,
    StudySpaceSummary,
)


class CreateStudySpaceUseCase:
    """Creates a study space from ready owned documents."""

    def __init__(
        self,
        space_repository: StudySpaceRepository,
        document_repository: StudyDocumentRepository,
    ) -> None:
        self._space_repository = space_repository
        self._document_repository = document_repository

    async def execute(
        self,
        owner_id: uuid.UUID,
        name: str,
        document_ids: list[uuid.UUID],
    ) -> CreateStudySpaceResponse:
        """Create a study space from ready owned documents.

        Raises StudySpaceError for validation or business rule violations.
        """
        # Validate name first
        if not name or not name.strip():
            raise StudySpaceError(
                "Study space name must not be blank",
                safe=True,
                code="invalid_name",
            )

        # Then validate documents
        for doc_id in document_ids:
            doc = await self._document_repository.find_by_id_and_owner(doc_id, owner_id)
            if doc is None:
                raise StudySpaceError(
                    "Document not found or not owned by user",
                    safe=True,
                    code="document_not_found",
                )
            if doc.status not in ("READY",):
                raise StudySpaceError(
                    "Document is not ready for study space creation",
                    safe=True,
                    code="document_not_ready",
                )

        space_id = uuid.uuid4()
        space = StudySpace.create(
            id=space_id,
            owner_id=owner_id,
            name=name,
            document_ids=document_ids,
        )
        await self._space_repository.save(space)
        await self._space_repository.commit()

        return CreateStudySpaceResponse(
            id=space.id,
            name=str(space.name),
            document_count=space.document_count,
            created_at=space.created_at or datetime.now(timezone.utc),
        )


class ListStudySpacesUseCase:
    """Lists study spaces owned by the authenticated user."""

    def __init__(
        self,
        space_repository: StudySpaceRepository,
    ) -> None:
        self._space_repository = space_repository

    async def execute(
        self,
        owner_id: uuid.UUID,
    ) -> list[StudySpaceSummary]:
        """List owned study spaces, newest first."""
        spaces = await self._space_repository.find_by_owner_id(owner_id)
        return [
            StudySpaceSummary(
                id=s.id,
                name=str(s.name),
                document_count=s.document_count,
                created_at=s.created_at or datetime.now(timezone.utc),
            )
            for s in spaces
        ]


class ListStudySpaceDocumentsUseCase:
    """Lists documents belonging to an owned study space."""

    def __init__(
        self,
        space_repository: StudySpaceRepository,
        document_repository: StudyDocumentRepository,
    ) -> None:
        self._space_repository = space_repository
        self._document_repository = document_repository

    async def execute(
        self,
        space_id: uuid.UUID,
        owner_id: uuid.UUID,
    ) -> list[StudySpaceDocumentSummary]:
        """List documents in a study space owned by the given user.

        Raises StudySpaceError with space_not_found if the space does not
        exist or does not belong to the owner.
        """
        space = await self._space_repository.find_by_id_and_owner(space_id, owner_id)
        if space is None:
            raise StudySpaceError(
                "Study space not found",
                safe=True,
                code="space_not_found",
            )

        documents = await self._document_repository.find_by_study_space_id_and_owner(
            space_id, owner_id
        )
        return [
            StudySpaceDocumentSummary(
                id=d.id,
                filename=d.filename,
                status=d.status,
                chunks_count=d.chunks_count,
                created_at=d.created_at or datetime.now(timezone.utc),
                processed_at=d.processed_at,
            )
            for d in documents
        ]
