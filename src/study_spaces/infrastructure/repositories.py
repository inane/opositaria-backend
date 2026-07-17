"""PostgreSQL repository adapter for study spaces."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.study_spaces.domain.entities import StudySpace, StudySpaceName
from src.study_spaces.infrastructure.models import StudySpaceModel


class PostgresStudySpaceRepository:
    """PostgreSQL adapter for StudySpaceRepository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, space: StudySpace) -> None:
        """Persist a study space (upsert)."""
        model = StudySpaceModel(
            id=space.id,
            owner_id=space.owner_id,
            name=str(space.name),
            document_count=space.document_count,
            created_at=space.created_at,
        )
        await self._session.merge(model)

    async def find_by_id(self, space_id: uuid.UUID) -> StudySpace | None:
        """Find a study space by its identifier."""
        result = await self._session.execute(
            select(StudySpaceModel).where(StudySpaceModel.id == space_id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return self._to_domain(model)

    async def find_by_owner_id(self, owner_id: uuid.UUID) -> list[StudySpace]:
        """Find all study spaces for an owner, newest first."""
        result = await self._session.execute(
            select(StudySpaceModel)
            .where(StudySpaceModel.owner_id == owner_id)
            .order_by(StudySpaceModel.created_at.desc())
        )
        models = result.scalars().all()
        return [self._to_domain(m) for m in models]

    async def find_by_id_and_owner(
        self, space_id: uuid.UUID, owner_id: uuid.UUID
    ) -> StudySpace | None:
        """Find a study space by its identifier and verify ownership."""
        result = await self._session.execute(
            select(StudySpaceModel).where(
                StudySpaceModel.id == space_id,
                StudySpaceModel.owner_id == owner_id,
            )
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return self._to_domain(model)

    async def flush(self) -> None:
        """Flush pending writes to durable storage."""
        await self._session.flush()

    async def commit(self) -> None:
        """Commit the current transaction durably."""
        await self._session.commit()

    @staticmethod
    def _to_domain(model: StudySpaceModel) -> StudySpace:
        """Map an ORM model to a domain StudySpace entity."""
        space = StudySpace(
            id=model.id,
            owner_id=model.owner_id,
            name=StudySpaceName(value=model.name),
            document_ids=[],
            created_at=model.created_at,
        )
        space.document_count = model.document_count
        return space
