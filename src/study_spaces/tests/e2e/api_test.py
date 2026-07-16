"""E2E tests for study space API endpoints."""

import uuid

import pytest
from httpx import AsyncClient, ASGITransport

from src.study_documents.domain.entities import StudyDocument
from src.study_documents.tests.support.inmemory_app import (
    OWNER_ID,
    create_inmemory_app,
)


def _create_ready_document(doc_repo, owner_id=None):
    """Create and save a ready document owned by the given user."""
    doc = StudyDocument.create(
        id=uuid.uuid4(),
        filename="test.pdf",
        content_type="application/pdf",
        storage_path="study_documents/test.pdf",
        owner_user_id=owner_id or OWNER_ID,
    )
    doc.mark_as_processing()
    doc.mark_as_ready(chunk_count=5)
    doc_repo._documents[doc.id] = doc
    return doc


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_list_spaces_without_auth_returns_401() -> None:
    """GET /study-spaces without bearer token returns 401."""
    app, _ = create_inmemory_app(authenticated=False)
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/study-spaces")

    assert response.status_code == 401


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_list_spaces_returns_empty_for_new_user() -> None:
    """An authenticated user with no study spaces gets an empty list."""
    from src.study_spaces.application.use_cases import ListStudySpacesUseCase
    from src.study_spaces.domain.repositories import InMemoryStudySpaceRepository

    from src.study_spaces.infrastructure.controllers import _get_list_spaces_use_case

    def make_inmemory_app():
        app, _ = create_inmemory_app(authenticated=True)
        space_repo = InMemoryStudySpaceRepository()

        async def override_list() -> ListStudySpacesUseCase:
            return ListStudySpacesUseCase(space_repository=space_repo)

        app.dependency_overrides[_get_list_spaces_use_case] = override_list
        return app

    app = make_inmemory_app()
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(
            "/study-spaces",
            headers={"Authorization": "Bearer test-token"},
        )

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_create_space_without_auth_returns_401() -> None:
    """POST /study-spaces without bearer token returns 401."""
    app, _ = create_inmemory_app(authenticated=False)
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/study-spaces",
            json={"name": "Test", "document_ids": [str(uuid.uuid4())]},
        )

    assert response.status_code == 401


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_create_space_from_ready_owned_document_returns_201() -> None:
    """An authenticated user creates a study space from a ready owned document."""
    from src.study_spaces.application.use_cases import CreateStudySpaceUseCase, ListStudySpacesUseCase
    from src.study_spaces.domain.repositories import InMemoryStudySpaceRepository
    from src.study_spaces.infrastructure.controllers import (
        _get_create_space_use_case,
        _get_list_spaces_use_case,
    )

    app, doc_repo = create_inmemory_app(authenticated=True)
    space_repo = InMemoryStudySpaceRepository()
    doc = _create_ready_document(doc_repo)

    async def override_create() -> CreateStudySpaceUseCase:
        return CreateStudySpaceUseCase(
            space_repository=space_repo,
            document_repository=doc_repo,
        )

    async def override_list() -> ListStudySpacesUseCase:
        return ListStudySpacesUseCase(space_repository=space_repo)

    app.dependency_overrides[_get_create_space_use_case] = override_create
    app.dependency_overrides[_get_list_spaces_use_case] = override_list

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/study-spaces",
            json={"name": "Derecho Administrativo", "document_ids": [str(doc.id)]},
            headers={"Authorization": "Bearer test-token"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Derecho Administrativo"
        assert data["document_count"] == 1
        assert data["id"] is not None

        # Verify it shows up in the list using the same client
        list_resp = await client.get(
            "/study-spaces",
            headers={"Authorization": "Bearer test-token"},
        )
        assert len(list_resp.json()) == 1


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_create_space_blank_name_returns_422() -> None:
    """A blank name returns 422 with code invalid_name."""
    from src.study_spaces.application.use_cases import CreateStudySpaceUseCase
    from src.study_spaces.domain.repositories import InMemoryStudySpaceRepository
    from src.study_spaces.infrastructure.controllers import _get_create_space_use_case

    app, doc_repo = create_inmemory_app(authenticated=True)
    space_repo = InMemoryStudySpaceRepository()

    async def override_create() -> CreateStudySpaceUseCase:
        return CreateStudySpaceUseCase(
            space_repository=space_repo,
            document_repository=doc_repo,
        )

    app.dependency_overrides[_get_create_space_use_case] = override_create

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/study-spaces",
            json={"name": "", "document_ids": [str(uuid.uuid4())]},
            headers={"Authorization": "Bearer test-token"},
        )

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "invalid_name"


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_create_space_with_foreign_document_returns_404() -> None:
    """Creating a study space with another user's document returns 404."""
    from src.study_spaces.application.use_cases import CreateStudySpaceUseCase
    from src.study_spaces.domain.repositories import InMemoryStudySpaceRepository
    from src.study_spaces.infrastructure.controllers import _get_create_space_use_case

    app, doc_repo = create_inmemory_app(authenticated=True)
    space_repo = InMemoryStudySpaceRepository()

    # Document owned by a different user
    doc = _create_ready_document(doc_repo, owner_id=uuid.uuid4())

    async def override_create() -> CreateStudySpaceUseCase:
        return CreateStudySpaceUseCase(
            space_repository=space_repo,
            document_repository=doc_repo,
        )

    app.dependency_overrides[_get_create_space_use_case] = override_create

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/study-spaces",
            json={"name": "Test", "document_ids": [str(doc.id)]},
            headers={"Authorization": "Bearer test-token"},
        )

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "document_not_found"


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_create_space_with_processing_document_returns_409() -> None:
    """Creating a study space with a processing document returns 409."""
    from src.study_spaces.application.use_cases import CreateStudySpaceUseCase
    from src.study_spaces.domain.repositories import InMemoryStudySpaceRepository
    from src.study_spaces.infrastructure.controllers import _get_create_space_use_case

    app, doc_repo = create_inmemory_app(authenticated=True)
    space_repo = InMemoryStudySpaceRepository()

    # Document owned by the user but still processing
    doc = StudyDocument.create(
        id=uuid.uuid4(),
        filename="test.pdf",
        content_type="application/pdf",
        storage_path="study_documents/test.pdf",
        owner_user_id=OWNER_ID,
    )
    doc.mark_as_processing()
    doc_repo._documents[doc.id] = doc

    async def override_create() -> CreateStudySpaceUseCase:
        return CreateStudySpaceUseCase(
            space_repository=space_repo,
            document_repository=doc_repo,
        )

    app.dependency_overrides[_get_create_space_use_case] = override_create

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/study-spaces",
            json={"name": "Test", "document_ids": [str(doc.id)]},
            headers={"Authorization": "Bearer test-token"},
        )

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "document_not_ready"