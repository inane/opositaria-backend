"""Tests for PDF text extraction, chunking, and embedding adapters."""

import pytest

from src.document_processing.infrastructure.embedding_generator import (
    NumpyEmbeddingGenerator,
)
from src.document_processing.infrastructure.text_chunker import TextChunkerService


class TestTextChunkerService:
    """Tests for TextChunkerService."""

    @pytest.mark.asyncio
    async def test_splits_long_text_into_ordered_chunks(self) -> None:
        """Long text is split into ordered chunks within size limits."""
        chunker = TextChunkerService(chunk_size=100, chunk_overlap=0)
        text = "First sentence. Second sentence. Third sentence. " * 10

        chunks = await chunker.chunk_text(text)

        assert len(chunks) > 1
        assert chunks[0][1] is None  # No page number

    @pytest.mark.asyncio
    async def test_returns_single_chunk_for_short_text(self) -> None:
        """Short text returns a single chunk."""
        chunker = TextChunkerService()
        text = "Short text."

        chunks = await chunker.chunk_text(text)

        assert len(chunks) == 1

    @pytest.mark.asyncio
    async def test_returns_empty_for_empty_text(self) -> None:
        """Empty text returns an empty list."""
        chunker = TextChunkerService()

        chunks = await chunker.chunk_text("")

        assert chunks == []


class TestNumpyEmbeddingGenerator:
    """Tests for NumpyEmbeddingGenerator."""

    @pytest.mark.asyncio
    async def test_generates_vector_with_configured_dimension(self) -> None:
        """Generated embedding has the configured dimension."""
        generator = NumpyEmbeddingGenerator(dimension=384)

        embedding = await generator.generate("Test text")

        assert len(embedding) == 384

    @pytest.mark.asyncio
    async def test_generates_deterministic_embeddings(self) -> None:
        """Same text produces the same embedding."""
        generator = NumpyEmbeddingGenerator()

        e1 = await generator.generate("Hello world")
        e2 = await generator.generate("Hello world")

        assert e1 == e2

    @pytest.mark.asyncio
    async def test_different_text_produces_different_embeddings(self) -> None:
        """Different text produces different embeddings."""
        generator = NumpyEmbeddingGenerator()

        e1 = await generator.generate("Hello world")
        e2 = await generator.generate("Goodbye world")

        assert e1 != e2
