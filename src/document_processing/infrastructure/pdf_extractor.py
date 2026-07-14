"""PDF text extraction adapter using pypdf."""

from pathlib import Path

from pypdf import PdfReader

from src.shared.infrastructure.settings import DocumentStorageSettings


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

        reader = PdfReader(str(full_path))
        texts: list[str] = []
        for page in reader.pages:
            text = page.extract_text()
            if text and text.strip():
                texts.append(text.strip())

        if not texts:
            return None

        return "\n\n".join(texts)
