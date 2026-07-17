"""add study_space_id to study_documents and enforce ownership

Revision ID: 3c4d5e6f7a8b
Revises: 2b3c4d5e6f7a
Create Date: 2026-07-17 12:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "3c4d5e6f7a8b"
down_revision: Union[str, Sequence[str], None] = "2b3c4d5e6f7a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add study_space_id to study_documents and enforce ownership.

    Steps:
    1. Add study_space_id column (nullable initially) with FK to study_spaces.
    2. Check for existing rows with null owner_user_id that would block
       future non-null constraints — raises an informative error.
    3. Replace the owner_user_id FK SET NULL behavior with CASCADE so
       ownership cannot be accidentally erased.
    """
    # Step 1: Add study_space_id column and FK
    op.add_column(
        "study_documents",
        sa.Column("study_space_id", sa.Uuid(), nullable=True),
    )
    op.create_foreign_key(
        "fk_study_documents_study_space_id",
        "study_documents",
        "study_spaces",
        ["study_space_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # Step 2: Check for legacy orphaned rows
    conn = op.get_bind()
    result = conn.execute(
        sa.text("SELECT COUNT(*) FROM study_documents WHERE owner_user_id IS NULL")
    ).scalar()
    if result and result > 0:
        raise Exception(
            f"Found {result} study documents with NULL owner_user_id. "
            "These must be assigned an owner or removed before the migration "
            "can make owner_user_id NOT NULL. "
            "Run: UPDATE study_documents SET owner_user_id = '<user_id>' "
            "WHERE owner_user_id IS NULL;"
        )

    # Step 3: Drop old SET NULL FK and recreate with CASCADE
    op.drop_constraint(
        "fk_study_documents_owner_user_id",
        "study_documents",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "fk_study_documents_owner_user_id",
        "study_documents",
        "users",
        ["owner_user_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    """Revert the migration."""
    # Restore old SET NULL FK
    op.drop_constraint(
        "fk_study_documents_owner_user_id",
        "study_documents",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "fk_study_documents_owner_user_id",
        "study_documents",
        "users",
        ["owner_user_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # Remove study_space_id column and FK
    op.drop_constraint(
        "fk_study_documents_study_space_id",
        "study_documents",
        type_="foreignkey",
    )
    op.drop_column("study_documents", "study_space_id")
