"""PostgreSQL repository adapters for study documents."""

import uuid
from typing import Any

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.semantic_search.application.ports import ChunkSearchResult
from src.study_documents.domain.entities import StudyDocument, StudyDocumentChunk
from src.study_documents.infrastructure.models import (
    StudyDocumentChunkModel,
    StudyDocumentModel,
)


class PostgresStudyDocumentRepository:
    """PostgreSQL adapter for StudyDocumentRepository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, document: StudyDocument) -> None:
        """Persist a study document (upsert)."""
        await self._session.execute(
            text("""
                INSERT INTO study_documents (id, filename, content_type, storage_path, owner_user_id, study_space_id, status,
                    failure_reason, chunks_count, created_at, updated_at, processed_at)
                VALUES (:id, :filename, :content_type, :storage_path, :owner_user_id, :study_space_id, :status,
                    :failure_reason, :chunks_count, :created_at, :updated_at, :processed_at)
                ON CONFLICT (id) DO UPDATE SET
                    filename = EXCLUDED.filename,
                    content_type = EXCLUDED.content_type,
                    storage_path = EXCLUDED.storage_path,
                    status = EXCLUDED.status,
                    failure_reason = EXCLUDED.failure_reason,
                    chunks_count = EXCLUDED.chunks_count,
                    updated_at = EXCLUDED.updated_at,
                    processed_at = EXCLUDED.processed_at,
                    study_space_id = EXCLUDED.study_space_id
            """),
            {
                "id": document.id,
                "filename": document.filename,
                "content_type": document.content_type,
                "storage_path": document.storage_path,
                "owner_user_id": document.owner_user_id,
                "study_space_id": document.study_space_id,
                "status": document.status,
                "failure_reason": document.failure_reason,
                "chunks_count": document.chunks_count,
                "created_at": document.created_at,
                "updated_at": document.updated_at,
                "processed_at": document.processed_at,
            },
        )

    async def find_by_id(self, document_id: uuid.UUID) -> StudyDocument | None:
        """Find a study document by its identifier."""
        result = await self._session.execute(
            select(StudyDocumentModel).where(StudyDocumentModel.id == document_id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return self._to_domain(model)

    async def find_by_id_and_owner(
        self, document_id: uuid.UUID, owner_id: uuid.UUID
    ) -> StudyDocument | None:
        """Find a study document by its identifier and owner."""
        result = await self._session.execute(
            select(StudyDocumentModel).where(
                StudyDocumentModel.id == document_id,
                StudyDocumentModel.owner_user_id == owner_id,
            )
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return self._to_domain(model)

    async def find_by_study_space_id_and_owner(
        self, study_space_id: uuid.UUID, owner_id: uuid.UUID
    ) -> list[StudyDocument]:
        """Find all documents in a study space owned by the given user."""
        result = await self._session.execute(
            select(StudyDocumentModel).where(
                StudyDocumentModel.study_space_id == study_space_id,
                StudyDocumentModel.owner_user_id == owner_id,
            )
        )
        models = result.scalars().all()
        return [self._to_domain(m) for m in models]

    @staticmethod
    def _to_domain(model: StudyDocumentModel) -> StudyDocument:
        """Map ORM model to domain entity."""
        return StudyDocument(
            id=model.id,
            filename=model.filename,
            content_type=model.content_type,
            storage_path=model.storage_path,
            owner_user_id=model.owner_user_id,
            study_space_id=model.study_space_id,
            status=model.status,
            failure_reason=model.failure_reason,
            chunks_count=model.chunks_count,
            created_at=model.created_at,
            updated_at=model.updated_at,
            processed_at=model.processed_at,
        )

    async def flush(self) -> None:
        """Flush pending writes to the database session."""
        await self._session.flush()

    async def commit(self) -> None:
        """Commit the current transaction durably."""
        await self._session.commit()


class PostgresStudyDocumentChunkRepository:
    """PostgreSQL adapter for StudyDocumentChunkRepository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, chunk: StudyDocumentChunk) -> None:
        """Persist a document chunk (upsert)."""
        embedding_str = "[" + ",".join(str(v) for v in chunk.embedding) + "]"
        await self._session.execute(
            text("""
                INSERT INTO study_document_chunks (id, document_id, text, sequence_number,
                    page_number, embedding, embedding_model, created_at)
                VALUES (:id, :document_id, :text, :sequence_number,
                    :page_number, CAST(:embedding AS vector), :embedding_model, :created_at)
                ON CONFLICT (id) DO UPDATE SET
                    text = EXCLUDED.text,
                    sequence_number = EXCLUDED.sequence_number,
                    page_number = EXCLUDED.page_number,
                    embedding = CAST(EXCLUDED.embedding AS vector),
                    embedding_model = EXCLUDED.embedding_model
            """),
            {
                "id": chunk.id,
                "document_id": chunk.document_id,
                "text": chunk.text,
                "sequence_number": chunk.sequence_number,
                "page_number": chunk.page_number,
                "embedding": embedding_str,
                "embedding_model": chunk.embedding_model,
                "created_at": chunk.created_at,
            },
        )

    async def find_by_document_id(
        self, document_id: uuid.UUID
    ) -> list[StudyDocumentChunk]:
        """Find all chunks for a document, ordered by sequence number."""
        result = await self._session.execute(
            select(StudyDocumentChunkModel)
            .where(StudyDocumentChunkModel.document_id == document_id)
            .order_by(StudyDocumentChunkModel.sequence_number)
        )
        models = result.scalars().all()
        return [self._to_domain(m) for m in models]

    async def replace_by_document_id(
        self, document_id: uuid.UUID, chunks: list[StudyDocumentChunk]
    ) -> None:
        """Atomically replace all chunks for a document."""
        await self._session.execute(
            text("DELETE FROM study_document_chunks WHERE document_id = :doc_id"),
            {"doc_id": document_id},
        )
        for chunk in chunks:
            await self.save(chunk)

    def _to_domain(self, model: StudyDocumentChunkModel) -> StudyDocumentChunk:
        """Convert ORM model to domain entity."""
        return StudyDocumentChunk(
            id=model.id,
            document_id=model.document_id,
            text=model.text,
            sequence_number=model.sequence_number,
            page_number=model.page_number,
            embedding=list(model.embedding) if model.embedding else [],
            embedding_model=model.embedding_model,
            created_at=model.created_at,
        )

    async def flush(self) -> None:
        """Flush pending writes to the database session."""
        await self._session.flush()


class PostgresSemanticChunkSearchRepository:
    """PostgreSQL adapter for semantic chunk search using pgvector cosine similarity."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_nearest_by_embedding(
        self,
        embedding: list[float],
        limit: int,
        owner_id: uuid.UUID | None = None,
        study_space_id: uuid.UUID | None = None,
    ) -> list[ChunkSearchResult]:
        """Find the nearest chunks by cosine similarity, limited to READY documents.

        When owner_id is provided, only chunks from documents owned by that user are returned.
        When study_space_id is provided, only chunks from documents in that study space are returned.
        """
        vector_literal = "[" + ",".join(str(v) for v in embedding) + "]"
        filters: list[str] = ["d.status = 'READY'"]
        params: dict[str, Any] = {"embedding": vector_literal, "limit": limit}
        if owner_id:
            filters.append("d.owner_user_id = :owner_id")
            params["owner_id"] = owner_id
        if study_space_id:
            filters.append("d.study_space_id = :study_space_id")
            params["study_space_id"] = study_space_id
        where_clause = " AND ".join(filters)
        query = text(f"""
            SELECT
                c.id AS chunk_id,
                c.document_id AS document_id,
                c.text AS text,
                1 - (c.embedding <=> CAST(:embedding AS vector)) AS score,
                c.sequence_number AS sequence_number,
                c.page_number AS page_number,
                d.filename AS document_filename
            FROM study_document_chunks c
            JOIN study_documents d ON d.id = c.document_id
            WHERE {where_clause}
            ORDER BY c.embedding <=> CAST(:embedding AS vector)
            LIMIT :limit
        """)
        result = await self._session.execute(query, params)
        rows = result.fetchall()
        return [
            ChunkSearchResult(
                chunk_id=row.chunk_id,
                document_id=row.document_id,
                text=row.text,
                score=float(row.score),
                sequence_number=row.sequence_number,
                page_number=row.page_number,
                document_filename=row.document_filename,
            )
            for row in rows
        ]
