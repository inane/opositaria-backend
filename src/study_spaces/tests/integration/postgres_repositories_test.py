"""Integration tests for PostgreSQL study space repository."""

import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.study_spaces.domain.entities import StudySpace
from src.study_spaces.infrastructure.repositories import PostgresStudySpaceRepository


async def _create_user(session: AsyncSession) -> uuid.UUID:
    """Insert a minimal user row and return its id."""
    user_id = uuid.uuid4()
    await session.execute(
        text("""
            INSERT INTO users (id, email, password_hash, created_at)
            VALUES (:id, :email, :hash, :now)
        """),
        {
            "id": user_id,
            "email": f"{user_id}@test.com",
            "hash": "dummy_hash",
            "now": datetime.now(timezone.utc),
        },
    )
    return user_id


@pytest.mark.integration
class TestPostgresStudySpaceRepository:
    """Integration tests for PostgresStudySpaceRepository."""

    @pytest.mark.asyncio
    async def test_save_and_find_by_id(self, session: AsyncSession) -> None:
        """A saved space is retrievable by its identifier."""
        owner_id = await _create_user(session)
        await session.commit()

        repo = PostgresStudySpaceRepository(session)
        space = StudySpace.create(
            id=uuid.uuid4(),
            owner_id=owner_id,
            name="Derecho Administrativo",
            document_ids=[uuid.uuid4()],
        )

        await repo.save(space)
        await session.commit()

        found = await repo.find_by_id(space.id)

        assert found is not None
        assert found.name == space.name
        assert found.owner_id == owner_id
        assert found.document_count == 1

    @pytest.mark.asyncio
    async def test_find_by_id_and_owner_returns_owned_space(
        self, session: AsyncSession
    ) -> None:
        """An owned space is found by id and owner."""
        owner_id = await _create_user(session)
        await session.commit()

        repo = PostgresStudySpaceRepository(session)
        space = StudySpace.create(
            id=uuid.uuid4(),
            owner_id=owner_id,
            name="Mi Espacio",
            document_ids=[uuid.uuid4()],
        )

        await repo.save(space)
        await session.commit()

        found = await repo.find_by_id_and_owner(space.id, owner_id)

        assert found is not None
        assert found.id == space.id

    @pytest.mark.asyncio
    async def test_find_by_id_and_owner_hides_foreign_spaces(
        self, session: AsyncSession
    ) -> None:
        """A space owned by another user is not found."""
        owner1 = await _create_user(session)
        owner2 = await _create_user(session)
        await session.commit()

        repo = PostgresStudySpaceRepository(session)
        space = StudySpace.create(
            id=uuid.uuid4(),
            owner_id=owner1,
            name="Espacio de Owner1",
            document_ids=[uuid.uuid4()],
        )

        await repo.save(space)
        await session.commit()

        found = await repo.find_by_id_and_owner(space.id, owner2)

        assert found is None

    @pytest.mark.asyncio
    async def test_find_by_id_and_owner_hides_missing_spaces(
        self, session: AsyncSession
    ) -> None:
        """A non-existent space id returns None."""
        owner_id = await _create_user(session)
        await session.commit()

        repo = PostgresStudySpaceRepository(session)

        found = await repo.find_by_id_and_owner(uuid.uuid4(), owner_id)

        assert found is None

    @pytest.mark.asyncio
    async def test_find_by_owner_id_returns_all_owned_spaces(
        self, session: AsyncSession
    ) -> None:
        """All spaces for an owner are returned, newest first."""
        owner_id = await _create_user(session)
        other_owner = await _create_user(session)
        await session.commit()

        repo = PostgresStudySpaceRepository(session)
        space1 = StudySpace.create(
            id=uuid.uuid4(),
            owner_id=owner_id,
            name="Espacio A",
            document_ids=[uuid.uuid4()],
        )
        space2 = StudySpace.create(
            id=uuid.uuid4(),
            owner_id=owner_id,
            name="Espacio B",
            document_ids=[uuid.uuid4()],
        )
        space_other = StudySpace.create(
            id=uuid.uuid4(),
            owner_id=other_owner,
            name="Espacio de otro",
            document_ids=[uuid.uuid4()],
        )

        await repo.save(space1)
        await repo.save(space2)
        await repo.save(space_other)
        await session.commit()

        found = await repo.find_by_owner_id(owner_id)

        assert len(found) == 2
        ids = {s.id for s in found}
        assert space1.id in ids
        assert space2.id in ids
        assert space_other.id not in ids
