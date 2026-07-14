"""Application ports for document processing operations."""

from abc import abstractmethod
from typing import Protocol


class PdfTextExtractor(Protocol):
    """Port for extracting text content from PDF files."""

    @abstractmethod
    async def extract_text(self, storage_path: str) -> str | None:
        """Extract selectable text from a PDF. Returns None if no usable text."""
        ...


class TextChunker(Protocol):
    """Port for splitting text into searchable chunks."""

    @abstractmethod
    async def chunk_text(self, text: str) -> list[tuple[str, int | None]]:
        """Split text into chunks with optional page numbers.

        Returns a list of (chunk_text, page_number) tuples.
        """
        ...


class EmbeddingGenerator(Protocol):
    """Port for generating text embeddings using a local model."""

    @abstractmethod
    async def generate(self, text: str) -> list[float]:
        """Generate an embedding vector for the given text.

        Returns a list of floats with the configured dimension.
        """
        ...
