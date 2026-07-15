"""PostgreSQL repository adapter for users."""

import uuid

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.users.domain.entities import User
from src.users.infrastructure.models import UserModel


class PostgresUserRepository:
    """PostgreSQL adapter for UserRepository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, user: User) -> None:
        """Persist a user (upsert)."""
        await self._session.execute(
            text("""
                INSERT INTO users (id, email, password_hash, created_at, updated_at)
                VALUES (:id, :email, :password_hash, :created_at, :updated_at)
                ON CONFLICT (id) DO UPDATE SET
                    email = EXCLUDED.email,
                    password_hash = EXCLUDED.password_hash,
                    updated_at = EXCLUDED.updated_at
            """),
            {
                "id": user.id,
                "email": user.email,
                "password_hash": user.password_hash,
                "created_at": user.created_at,
                "updated_at": user.updated_at,
            },
        )

    async def find_by_id(self, user_id: uuid.UUID) -> User | None:
        """Find a user by their identifier."""
        result = await self._session.execute(
            select(UserModel).where(UserModel.id == user_id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return self._to_domain(model)

    async def find_by_email(self, email: str) -> User | None:
        """Find a user by their normalized email."""
        result = await self._session.execute(
            select(UserModel).where(UserModel.email == email)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return self._to_domain(model)

    async def flush(self) -> None:
        """Flush pending writes to the database session."""
        await self._session.flush()

    async def commit(self) -> None:
        """Commit the current transaction durably."""
        await self._session.commit()

    @staticmethod
    def _to_domain(model: UserModel) -> User:
        """Convert ORM model to domain entity."""
        return User(
            id=model.id,
            email=model.email,
            password_hash=model.password_hash,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
