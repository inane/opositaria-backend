"""enforce not null on owner_user_id and study_space_id

Revision ID: a1b2c3d4e5f6
Revises: 3c4d5e6f7a8b
Create Date: 2026-07-17 13:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "3c4d5e6f7a8b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Enforce NOT NULL constraints on owner_user_id and study_space_id.

    This migration assumes all legacy null rows have been cleaned up
    before deployment. If nulls remain, the ALTER will fail with a clear
    PostgreSQL error.
    """
    op.alter_column(
        "study_documents",
        "owner_user_id",
        existing_type=sa.Uuid(),
        nullable=False,
    )
    op.alter_column(
        "study_documents",
        "study_space_id",
        existing_type=sa.Uuid(),
        nullable=False,
    )


def downgrade() -> None:
    """Revert to nullable columns."""
    op.alter_column(
        "study_documents",
        "study_space_id",
        existing_type=sa.Uuid(),
        nullable=True,
    )
    op.alter_column(
        "study_documents",
        "owner_user_id",
        existing_type=sa.Uuid(),
        nullable=True,
    )
