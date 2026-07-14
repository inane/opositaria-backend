"""add HNSW cosine vector index on chunk embeddings

Revision ID: f56d4cbfb3fc
Revises: eded98b91c99
Create Date: 2026-07-14 12:20:46.390658

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "f56d4cbfb3fc"
down_revision: Union[str, Sequence[str], None] = "eded98b91c99"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add HNSW cosine vector index on chunk embeddings."""
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_study_document_chunks_embedding "
        "ON study_document_chunks "
        "USING hnsw (embedding vector_cosine_ops)"
    )


def downgrade() -> None:
    """Drop HNSW cosine vector index."""
    op.execute("DROP INDEX IF EXISTS ix_study_document_chunks_embedding")
