"""enable pgvector extension

Revision ID: fb1ff5b252c1
Revises:
Create Date: 2026-07-14 12:19:00.193719

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "fb1ff5b252c1"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Enable pgvector extension."""
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")


def downgrade() -> None:
    """Disable pgvector extension."""
    op.execute("DROP EXTENSION IF EXISTS vector CASCADE")
