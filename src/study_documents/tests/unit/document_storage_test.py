"""Tests for local filesystem document storage."""

import uuid
from pathlib import Path

import pytest

from src.study_documents.infrastructure.document_storage import LocalDocumentStorage


class TestLocalDocumentStorage:
    """Tests for LocalDocumentStorage."""

    @pytest.mark.asyncio
    async def test_saves_and_retrieves_file(self, tmp_path: Path) -> None:
        """A saved file is stored at the correct path and can be read back."""
        storage = LocalDocumentStorage(storage_path=str(tmp_path))
        doc_id = uuid.uuid4()
        content = b"%PDF-1.4 test content"

        storage_path = await storage.save(doc_id, "test.pdf", content)

        assert storage_path == f"{doc_id}/test.pdf"
        full_path = tmp_path / storage_path
        assert full_path.exists()
        assert full_path.read_bytes() == content
