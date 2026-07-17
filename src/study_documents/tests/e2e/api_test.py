"""E2E tests for study document API endpoints."""

import uuid

import pytest
from httpx import AsyncClient, ASGITransport

from src.study_documents.domain.entities import MAX_UPLOAD_SIZE_BYTES
from src.study_documents.tests.support.inmemory_app import (
    OWNER_ID,
    create_inmemory_app,
)


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_upload_valid_pdf_returns_202_accepted() -> None:
    """Uploading a valid PDF returns 202 Accepted with document ID and PENDING_PROCESSING."""
    app, _, _ = create_inmemory_app(authenticated=True)
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/study-documents/upload",
            files={"file": ("test.pdf", b"%PDF-1.4 test content", "application/pdf")},
            data={"study_space_name": "Derecho Administrativo"},
            headers={"Authorization": "Bearer test-token"},
        )

    assert response.status_code == 202
    data = response.json()
    assert "document_id" in data
    assert data["status"] == "PENDING_PROCESSING"


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_upload_non_pdf_returns_422() -> None:
    """Uploading a non-PDF file returns 422 with code invalid_file_type."""
    app, _, _ = create_inmemory_app(authenticated=True)
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/study-documents/upload",
            files={"file": ("notes.txt", b"not a pdf", "text/plain")},
            data={"study_space_name": "Test"},
            headers={"Authorization": "Bearer test-token"},
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
    app, _, _ = create_inmemory_app(authenticated=True)
    oversized_content = b"x" * (MAX_UPLOAD_SIZE_BYTES + 1)
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/study-documents/upload",
            files={"file": ("large.pdf", oversized_content, "application/pdf")},
            data={"study_space_name": "Test"},
            headers={"Authorization": "Bearer test-token"},
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
    app, _, _ = create_inmemory_app(authenticated=True)
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/study-documents/upload",
            files={"file": ("empty.pdf", b"", "application/pdf")},
            data={"study_space_name": "Test"},
            headers={"Authorization": "Bearer test-token"},
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
    app, _, _ = create_inmemory_app(authenticated=True)
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/study-documents/upload",
            files={
                "file": ("../malicious.pdf", b"%PDF-1.4 content", "application/pdf")
            },
            data={"study_space_name": "Test"},
            headers={"Authorization": "Bearer test-token"},
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
    app, _, _ = create_inmemory_app(authenticated=True)
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        # Test empty upload
        resp1 = await client.post(
            "/study-documents/upload",
            files={"file": ("empty.pdf", b"", "application/pdf")},
            data={"study_space_name": "Test"},
            headers={"Authorization": "Bearer test-token"},
        )
        # Test invalid filename
        resp2 = await client.post(
            "/study-documents/upload",
            files={"file": ("../bad.pdf", b"%PDF content", "application/pdf")},
            data={"study_space_name": "Test"},
            headers={"Authorization": "Bearer test-token"},
        )
        # Test invalid file type
        resp3 = await client.post(
            "/study-documents/upload",
            files={"file": ("notes.txt", b"content", "text/plain")},
            data={"study_space_name": "Test"},
            headers={"Authorization": "Bearer test-token"},
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
    app, _, _ = create_inmemory_app(authenticated=True)
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(
            f"/study-documents/{uuid.uuid4()}/status",
            headers={"Authorization": "Bearer test-token"},
        )

    assert response.status_code == 404


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_upload_without_auth_returns_401() -> None:
    """Uploading without a bearer token returns 401."""
    app, _, _ = create_inmemory_app(authenticated=False)
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/study-documents/upload",
            files={"file": ("test.pdf", b"%PDF-1.4 test content", "application/pdf")},
        )

    assert response.status_code == 401


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_upload_auth_user_creates_owned_document() -> None:
    """An authenticated upload creates a document owned by the authenticated user."""
    app, doc_repo, _ = create_inmemory_app(authenticated=True)
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/study-documents/upload",
            files={"file": ("test.pdf", b"%PDF-1.4 test content", "application/pdf")},
            data={"study_space_name": "Derecho Administrativo"},
            headers={"Authorization": "Bearer test-token"},
        )

    assert response.status_code == 202
    data = response.json()
    doc = await doc_repo.find_by_id(uuid.UUID(data["document_id"]))
    assert doc is not None
    assert doc.owner_user_id == OWNER_ID


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_upload_creates_listable_study_space() -> None:
    """An upload creates a study space that appears in GET /study-spaces."""
    app, doc_repo, space_repo = create_inmemory_app(authenticated=True)
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        upload_resp = await client.post(
            "/study-documents/upload",
            files={"file": ("test.pdf", b"%PDF-1.4 test content", "application/pdf")},
            data={"study_space_name": "Derecho Administrativo"},
            headers={"Authorization": "Bearer test-token"},
        )

    assert upload_resp.status_code == 202
    upload_data = upload_resp.json()
    assert "study_space_id" in upload_data

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        list_resp = await client.get(
            "/study-spaces",
            headers={"Authorization": "Bearer test-token"},
        )

    assert list_resp.status_code == 200
    spaces = list_resp.json()
    assert len(spaces) >= 1
    created = [s for s in spaces if s["id"] == upload_data["study_space_id"]]
    assert len(created) == 1
    assert created[0]["name"] == "Derecho Administrativo"
    assert created[0]["document_count"] == 1


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_upload_blank_space_name_returns_422() -> None:
    """Uploading with a blank study_space_name returns 422."""
    app, _, _ = create_inmemory_app(authenticated=True)
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/study-documents/upload",
            files={"file": ("test.pdf", b"%PDF-1.4 content", "application/pdf")},
            data={"study_space_name": ""},
            headers={"Authorization": "Bearer test-token"},
        )

    assert response.status_code == 422


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_status_without_auth_returns_401() -> None:
    """Retrieving status without a bearer token returns 401."""
    app, _, _ = create_inmemory_app(authenticated=False)
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(f"/study-documents/{uuid.uuid4()}/status")

    assert response.status_code == 401


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_owner_can_read_document_status() -> None:
    """An owner can read the status of their own document."""
    app, doc_repo, _ = create_inmemory_app(authenticated=True)
    doc = _create_document(doc_repo)

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(
            f"/study-documents/{doc.id}/status",
            headers={"Authorization": "Bearer test-token"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["document_id"] == str(doc.id)
    assert data["status"] == "PENDING_PROCESSING"


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_foreign_user_gets_404_for_document_status() -> None:
    """A different authenticated user receives 404 for foreign document status."""
    app, doc_repo, _ = create_inmemory_app(authenticated=True)
    # Create a document owned by the "wrong" user
    doc = _create_document(doc_repo, owner_id=uuid.uuid4())

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(
            f"/study-documents/{doc.id}/status",
            headers={"Authorization": "Bearer test-token"},
        )

    assert response.status_code == 404


def _create_document(doc_repo, owner_id=None):
    """Helper to create and save a test document in the in-memory repo."""
    from src.study_documents.domain.entities import StudyDocument

    doc = StudyDocument.create(
        id=uuid.uuid4(),
        filename="test.pdf",
        content_type="application/pdf",
        storage_path="study_documents/test.pdf",
        owner_user_id=owner_id or OWNER_ID,
        study_space_id=uuid.uuid4(),
    )
    doc_repo._documents[doc.id] = doc
    return doc
