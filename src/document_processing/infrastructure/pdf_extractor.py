"""PDF text extraction adapter using pypdf."""

from pathlib import Path

from pypdf import PdfReader
from pypdf.errors import FileNotDecryptedError, PdfReadError

from src.shared.infrastructure.settings import DocumentStorageSettings
from src.study_documents.domain.entities import StudyDocumentError


class PypdfTextExtractor:
    """Extracts selectable text from PDF files using pypdf."""

    def __init__(self, storage_base_path: str | None = None) -> None:
        if storage_base_path is None:
            storage_base_path = DocumentStorageSettings().document_storage_path
        self._base_path = Path(storage_base_path)

    async def extract_text(self, storage_path: str) -> str | None:
        """Extract selectable text from a PDF. Returns None if no usable text."""
        full_path = self._base_path / storage_path
        if not full_path.exists():
            return None

        try:
            reader = PdfReader(str(full_path))
        except FileNotDecryptedError:
            raise StudyDocumentError(
                "The PDF is encrypted",
                safe=True,
                code="encrypted_pdf",
            )
        except PdfReadError:
            raise StudyDocumentError(
                "The PDF file could not be read",
                safe=True,
                code="pdf_cannot_be_read",
            )

        try:
            texts: list[str] = []
            for page in reader.pages:
                text = page.extract_text()
                if text and text.strip():
                    texts.append(text.strip())
        except FileNotDecryptedError:
            raise StudyDocumentError(
                "The PDF is encrypted",
                safe=True,
                code="encrypted_pdf",
            )

        if not texts:
            return None

        return "\n\n".join(texts)
