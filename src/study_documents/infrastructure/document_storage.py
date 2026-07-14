"""Local filesystem document storage adapter."""

import uuid
from pathlib import Path, PurePosixPath

from src.shared.infrastructure.settings import DocumentStorageSettings


class LocalDocumentStorage:
    """Saves uploaded PDF bytes to a local filesystem directory."""

    def __init__(self, storage_path: str | None = None) -> None:
        if storage_path is None:
            storage_path = DocumentStorageSettings().document_storage_path
        self._base_path = Path(storage_path)
        self._base_path.mkdir(parents=True, exist_ok=True)

    async def save(self, document_id: uuid.UUID, filename: str, content: bytes) -> str:
        """Save uploaded file content and return a relative storage path."""
        safe_filename = PurePosixPath(filename).name
        relative_path = f"{document_id}/{safe_filename}"
        full_path = self._base_path / relative_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_bytes(content)
        return str(relative_path)
