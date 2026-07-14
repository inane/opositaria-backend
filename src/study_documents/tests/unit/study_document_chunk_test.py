"""Unit tests for the StudyDocumentChunk domain entity."""

import uuid

import pytest

from src.study_documents.domain.entities import StudyDocumentChunk, StudyDocumentError


class TestStudyDocumentChunk:
    """Tests for StudyDocumentChunk entity creation and validation."""

    def test_creates_chunk_with_required_fields(self) -> None:
        """A chunk is created with document identity, text, sequence, embedding, and model."""
        chunk_id = uuid.uuid4()
        document_id = uuid.uuid4()
        text = "El derecho administrativo regula la organización y funcionamiento de la Administración pública."
        sequence_number = 1
        embedding = [0.1] * 384
        embedding_model = "all-MiniLM-L6-v2"

        chunk = StudyDocumentChunk.create(
            id=chunk_id,
            document_id=document_id,
            text=text,
            sequence_number=sequence_number,
            embedding=embedding,
            embedding_model=embedding_model,
        )

        assert chunk.id == chunk_id
        assert chunk.document_id == document_id
        assert chunk.text == text
        assert chunk.sequence_number == sequence_number
        assert chunk.embedding == embedding
        assert chunk.embedding_model == embedding_model
        assert chunk.page_number is None

    def test_rejects_blank_chunk_text(self) -> None:
        """A chunk with blank text is rejected."""
        with pytest.raises(StudyDocumentError, match="Chunk text must not be blank"):
            StudyDocumentChunk.create(
                id=uuid.uuid4(),
                document_id=uuid.uuid4(),
                text="   ",
                sequence_number=1,
                embedding=[0.1] * 384,
                embedding_model="all-MiniLM-L6-v2",
            )

    def test_rejects_embedding_with_wrong_dimension(self) -> None:
        """A chunk with an embedding dimension mismatch is rejected."""
        with pytest.raises(StudyDocumentError, match="must be 384"):
            StudyDocumentChunk.create(
                id=uuid.uuid4(),
                document_id=uuid.uuid4(),
                text="Valid chunk text for testing.",
                sequence_number=1,
                embedding=[0.1] * 128,
                embedding_model="all-MiniLM-L6-v2",
            )

    def test_orders_chunks_by_sequence_number(self) -> None:
        """Chunks are ordered by their sequence number."""
        document_id = uuid.uuid4()
        chunks = [
            StudyDocumentChunk.create(
                id=uuid.uuid4(),
                document_id=document_id,
                text="Third chunk.",
                sequence_number=3,
                embedding=[0.1] * 384,
                embedding_model="all-MiniLM-L6-v2",
            ),
            StudyDocumentChunk.create(
                id=uuid.uuid4(),
                document_id=document_id,
                text="First chunk.",
                sequence_number=1,
                embedding=[0.2] * 384,
                embedding_model="all-MiniLM-L6-v2",
            ),
            StudyDocumentChunk.create(
                id=uuid.uuid4(),
                document_id=document_id,
                text="Second chunk.",
                sequence_number=2,
                embedding=[0.3] * 384,
                embedding_model="all-MiniLM-L6-v2",
            ),
        ]

        sorted_chunks = sorted(chunks, key=lambda c: c.sequence_number)

        assert sorted_chunks[0].sequence_number == 1
        assert sorted_chunks[0].text == "First chunk."
        assert sorted_chunks[1].sequence_number == 2
        assert sorted_chunks[1].text == "Second chunk."
        assert sorted_chunks[2].sequence_number == 3
        assert sorted_chunks[2].text == "Third chunk."
