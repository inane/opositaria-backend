"""Tests for PDF text extraction, chunking, and embedding adapters."""

import tempfile
from pathlib import Path

import pytest

from src.document_processing.infrastructure.embedding_generator import (
    NumpyEmbeddingGenerator,
)
from src.document_processing.infrastructure.pdf_extractor import PypdfTextExtractor
from src.document_processing.infrastructure.text_chunker import TextChunkerService
from src.study_documents.domain.entities import StudyDocumentError


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


class TestPypdfTextExtractor:
    """Tests for PypdfTextExtractor."""

    @pytest.mark.asyncio
    async def test_extracts_each_page_once(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Selectable text from each page is included once in order."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_path = str(tmpdir)
            extractor = PypdfTextExtractor(storage_base_path=base_path)
            pdf_path = Path(tmpdir) / "study_documents" / "readable.pdf"
            pdf_path.parent.mkdir(parents=True, exist_ok=True)
            pdf_path.write_bytes(b"%PDF-1.4")

            class FakePage:
                def __init__(self, text: str) -> None:
                    self._text = text

                def extract_text(self) -> str:
                    return self._text

            class FakeReader:
                pages = [FakePage("Page one"), FakePage("Page two")]

            monkeypatch.setattr(
                "src.document_processing.infrastructure.pdf_extractor.PdfReader",
                lambda path: FakeReader(),
            )

            result = await extractor.extract_text("study_documents/readable.pdf")

            assert result == "Page one\n\nPage two"

    @pytest.mark.asyncio
    async def test_maps_unreadable_pdf_to_pdf_cannot_be_read(self) -> None:
        """A corrupt/unreadable PDF is translated to pdf_cannot_be_read code."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_path = str(tmpdir)
            extractor = PypdfTextExtractor(storage_base_path=base_path)

            # Create a corrupt PDF file (not valid PDF bytes)
            corrupt_path = Path(tmpdir) / "study_documents" / "corrupt.pdf"
            corrupt_path.parent.mkdir(parents=True, exist_ok=True)
            corrupt_path.write_bytes(b"not a valid pdf content at all")

            with pytest.raises(StudyDocumentError) as exc:
                await extractor.extract_text("study_documents/corrupt.pdf")

            assert exc.value.code == "pdf_cannot_be_read"
            assert exc.value.safe is True

    @pytest.mark.asyncio
    async def test_maps_encrypted_pdf_to_encrypted_pdf(self) -> None:
        """An encrypted/password-protected PDF is translated to encrypted_pdf code."""
        from io import BytesIO

        from pypdf import PdfWriter

        with tempfile.TemporaryDirectory() as tmpdir:
            base_path = str(tmpdir)
            extractor = PypdfTextExtractor(storage_base_path=base_path)

            # Create an encrypted PDF
            writer = PdfWriter()
            writer.add_blank_page(width=612, height=792)
            writer.encrypt("password123")
            encrypted_bytes = BytesIO()
            writer.write(encrypted_bytes)
            encrypted_bytes.seek(0)

            encrypted_path = Path(tmpdir) / "study_documents" / "encrypted.pdf"
            encrypted_path.parent.mkdir(parents=True, exist_ok=True)
            encrypted_path.write_bytes(encrypted_bytes.getvalue())

            with pytest.raises(StudyDocumentError) as exc:
                await extractor.extract_text("study_documents/encrypted.pdf")

            assert exc.value.code == "encrypted_pdf"
            assert exc.value.safe is True

    @pytest.mark.asyncio
    async def test_maps_constructor_encryption_error_to_encrypted_pdf(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """An encryption error raised while opening the PDF is translated to encrypted_pdf."""
        from pypdf.errors import FileNotDecryptedError

        with tempfile.TemporaryDirectory() as tmpdir:
            base_path = str(tmpdir)
            extractor = PypdfTextExtractor(storage_base_path=base_path)
            pdf_path = Path(tmpdir) / "study_documents" / "encrypted.pdf"
            pdf_path.parent.mkdir(parents=True, exist_ok=True)
            pdf_path.write_bytes(b"%PDF-1.4")

            def raise_encryption_error(path: str) -> None:
                raise FileNotDecryptedError("File has not been decrypted")

            monkeypatch.setattr(
                "src.document_processing.infrastructure.pdf_extractor.PdfReader",
                raise_encryption_error,
            )

            with pytest.raises(StudyDocumentError) as exc:
                await extractor.extract_text("study_documents/encrypted.pdf")

            assert exc.value.code == "encrypted_pdf"
            assert exc.value.safe is True

    @pytest.mark.asyncio
    async def test_returns_none_for_no_selectable_text(self) -> None:
        """A scanned/image-only PDF with no selectable text returns None."""
        from io import BytesIO

        from pypdf import PdfWriter

        with tempfile.TemporaryDirectory() as tmpdir:
            base_path = str(tmpdir)
            extractor = PypdfTextExtractor(storage_base_path=base_path)

            # Create a PDF with no text (blank page)
            writer = PdfWriter()
            writer.add_blank_page(width=612, height=792)
            pdf_bytes = BytesIO()
            writer.write(pdf_bytes)
            pdf_bytes.seek(0)

            blank_path = Path(tmpdir) / "study_documents" / "blank.pdf"
            blank_path.parent.mkdir(parents=True, exist_ok=True)
            blank_path.write_bytes(pdf_bytes.getvalue())

            result = await extractor.extract_text("study_documents/blank.pdf")

            assert result is None

    @pytest.mark.asyncio
    async def test_sanitizes_read_failure_messages(self) -> None:
        """Raw parser messages, filesystem paths, and library internals are not exposed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_path = str(tmpdir)
            extractor = PypdfTextExtractor(storage_base_path=base_path)

            corrupt_path = Path(tmpdir) / "study_documents" / "corrupt.pdf"
            corrupt_path.parent.mkdir(parents=True, exist_ok=True)
            corrupt_path.write_bytes(b"not a valid pdf content at all")

            with pytest.raises(StudyDocumentError) as exc:
                await extractor.extract_text("study_documents/corrupt.pdf")

            # Message should be safe - no raw exception text, paths, or internals
            assert exc.value.safe is True
            assert "pypdf" not in exc.value.message
            assert "PdfReadError" not in exc.value.message
            assert "traceback" not in exc.value.message.lower()
            assert exc.value.message == "The PDF file could not be read"


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
