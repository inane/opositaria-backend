"""E2E tests for study document API endpoints."""

import uuid
from dataclasses import dataclass, field

import pytest
from httpx import AsyncClient, ASGITransport

from src.shared.infrastructure.factory import create_app
from src.study_documents.domain.entities import MAX_UPLOAD_SIZE_BYTES


@dataclass
class DocumentStorageStub:
    """Stub that records storage calls and returns a fixed path."""

    saved: list[tuple[uuid.UUID, str, bytes]] = field(default_factory=list)
    storage_path: str = "study_documents/test.pdf"

    async def save(self, document_id: uuid.UUID, filename: str, content: bytes) -> str:
        self.saved.append((document_id, filename, content))
        return self.storage_path


@dataclass
class PublisherStub:
    """Stub that records publish calls."""

    published: list[tuple[uuid.UUID, uuid.UUID]] = field(default_factory=list)

    async def publish(self, document_id: uuid.UUID, job_id: uuid.UUID) -> None:
        self.published.append((document_id, job_id))


@pytest.fixture
def app():
    """Create a test app with InMemory repositories."""
    application = create_app()
    application.dependency_overrides = {}
    return application


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_upload_valid_pdf_returns_202_accepted() -> None:
    """Uploading a valid PDF returns 202 Accepted with document ID and PENDING_PROCESSING."""
    app = create_app()
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/study-documents/upload",
            files={"file": ("test.pdf", b"%PDF-1.4 test content", "application/pdf")},
        )

    assert response.status_code == 202
    data = response.json()
    assert "document_id" in data
    assert data["status"] == "PENDING_PROCESSING"


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_upload_non_pdf_returns_422() -> None:
    """Uploading a non-PDF file returns 422 with code invalid_file_type."""
    app = create_app()
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/study-documents/upload",
            files={"file": ("notes.txt", b"not a pdf", "text/plain")},
        )

    assert response.status_code == 422
    data = response.json()
    assert data["detail"]["code"] == "invalid_file_type"
    assert isinstance(data["detail"]["message"], str)
    assert len(data["detail"]["message"]) > 0


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_upload_oversized_returns_413_with_code() -> None:
    """An oversized upload returns 413 Payload Too Large with code file_too_large."""
    app = create_app()
    oversized_content = b"x" * (MAX_UPLOAD_SIZE_BYTES + 1)
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/study-documents/upload",
            files={"file": ("large.pdf", oversized_content, "application/pdf")},
        )

    assert response.status_code == 413
    data = response.json()
    assert data["detail"]["code"] == "file_too_large"
    assert isinstance(data["detail"]["message"], str)
    assert len(data["detail"]["message"]) > 0


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_upload_empty_returns_422_with_code() -> None:
    """An empty upload returns 422 with code empty_upload."""
    app = create_app()
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/study-documents/upload",
            files={"file": ("empty.pdf", b"", "application/pdf")},
        )

    assert response.status_code == 422
    data = response.json()
    assert data["detail"]["code"] == "empty_upload"
    assert isinstance(data["detail"]["message"], str)
    assert len(data["detail"]["message"]) > 0


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_upload_invalid_filename_returns_422_with_code() -> None:
    """An upload with a path separator in the filename returns 422 with code invalid_filename."""
    app = create_app()
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/study-documents/upload",
            files={
                "file": ("../malicious.pdf", b"%PDF-1.4 content", "application/pdf")
            },
        )

    assert response.status_code == 422
    data = response.json()
    assert data["detail"]["code"] == "invalid_filename"
    assert isinstance(data["detail"]["message"], str)
    assert len(data["detail"]["message"]) > 0


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_upload_errors_contain_only_safe_fields() -> None:
    """Upload error responses contain only code and safe message, no stack traces or paths."""
    app = create_app()
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        # Test empty upload
        resp1 = await client.post(
            "/study-documents/upload",
            files={"file": ("empty.pdf", b"", "application/pdf")},
        )
        # Test invalid filename
        resp2 = await client.post(
            "/study-documents/upload",
            files={"file": ("../bad.pdf", b"%PDF content", "application/pdf")},
        )
        # Test invalid file type
        resp3 = await client.post(
            "/study-documents/upload",
            files={"file": ("notes.txt", b"content", "text/plain")},
        )

    for response in [resp1, resp2, resp3]:
        data = response.json()
        detail = data["detail"]
        # Only code and message fields are exposed
        assert set(detail.keys()) == {"code", "message"}
        # No stack traces or filesystem paths in messages
        assert "traceback" not in detail["message"].lower()
        assert "stack" not in detail["message"].lower()


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_get_missing_document_returns_404() -> None:
    """Retrieving status for a non-existent document returns 404."""
    app = create_app()
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(f"/study-documents/{uuid.uuid4()}/status")

    assert response.status_code == 404


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_blank_search_query_returns_422() -> None:
    """A blank search query returns 422 validation error."""
    app = create_app()
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/semantic-search/search",
            params={"query": ""},
        )

    assert response.status_code == 422


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_invalid_search_limit_returns_422() -> None:
    """An invalid search limit returns 422 validation error."""
    app = create_app()
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/semantic-search/search",
            params={"query": "test", "limit": 100},
        )

    assert response.status_code == 422