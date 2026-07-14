"""E2E tests for study document API endpoints."""

import uuid

import pytest
from httpx import AsyncClient, ASGITransport

from src.shared.infrastructure.factory import create_app
from src.study_documents.domain.repositories import InMemoryStudyDocumentRepository
from src.study_documents.tests.unit.use_cases_test import (
    DocumentStorageSpy,
    PublisherSpy,
)


@pytest.fixture
def app():
    """Create a test app with InMemory repositories."""
    application = create_app()
    InMemoryStudyDocumentRepository()
    DocumentStorageSpy()
    PublisherSpy()

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
    """Uploading a non-PDF file returns 422 validation error."""
    app = create_app()
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/study-documents/upload",
            files={"file": ("notes.txt", b"not a pdf", "text/plain")},
        )

    assert response.status_code == 422


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
