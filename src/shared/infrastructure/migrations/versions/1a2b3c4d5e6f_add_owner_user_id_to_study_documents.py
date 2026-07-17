"""add owner_user_id to study_documents table

Revision ID: 1a2b3c4d5e6f
Revises: c2eeaf137305
Create Date: 2026-07-16 10:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "1a2b3c4d5e6f"
down_revision: Union[str, Sequence[str], None] = "c2eeaf137305"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add owner_user_id column to study_documents."""
    op.add_column(
        "study_documents",
        sa.Column("owner_user_id", sa.Uuid(), nullable=True),
    )
    op.create_foreign_key(
        "fk_study_documents_owner_user_id",
        "study_documents",
        "users",
        ["owner_user_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    """Remove owner_user_id column from study_documents."""
    op.drop_constraint(
        "fk_study_documents_owner_user_id",
        "study_documents",
        type_="foreignkey",
    )
    op.drop_column("study_documents", "owner_user_id")
