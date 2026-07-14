"""create study_documents, study_document_chunks, and document_processing_jobs tables

Revision ID: eded98b91c99
Revises: fb1ff5b252c1
Create Date: 2026-07-14 12:19:45.008279

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision: str = "eded98b91c99"
down_revision: Union[str, Sequence[str], None] = "fb1ff5b252c1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


EMBEDDING_DIMENSION = 384


def upgrade() -> None:
    """Create study document, chunk, and processing job tables."""
    op.create_table(
        "study_documents",
        sa.Column("id", sa.Uuid(), nullable=False, primary_key=True),
        sa.Column("filename", sa.String(), nullable=False),
        sa.Column("content_type", sa.String(), nullable=False),
        sa.Column("storage_path", sa.String(), nullable=False),
        sa.Column(
            "status", sa.String(), nullable=False, server_default="PENDING_PROCESSING"
        ),
        sa.Column("failure_reason", sa.String(), nullable=True),
        sa.Column("chunks_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_table(
        "study_document_chunks",
        sa.Column("id", sa.Uuid(), nullable=False, primary_key=True),
        sa.Column(
            "document_id",
            sa.Uuid(),
            sa.ForeignKey("study_documents.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("sequence_number", sa.Integer(), nullable=False),
        sa.Column("page_number", sa.Integer(), nullable=True),
        sa.Column("embedding", Vector(EMBEDDING_DIMENSION), nullable=False),
        sa.Column("embedding_model", sa.String(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_table(
        "document_processing_jobs",
        sa.Column("id", sa.Uuid(), nullable=False, primary_key=True),
        sa.Column(
            "document_id",
            sa.Uuid(),
            sa.ForeignKey("study_documents.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("status", sa.String(), nullable=False, server_default="PENDING"),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failure_reason", sa.String(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    """Drop study document, chunk, and processing job tables."""
    op.drop_table("document_processing_jobs")
    op.drop_table("study_document_chunks")
    op.drop_table("study_documents")
