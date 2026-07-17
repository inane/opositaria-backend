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
        study_space_id=uuid.uuid4(),
    )
    doc.mark_as_processing()
    doc.mark_as_ready(chunk_count=5)
    doc_repo._documents[doc.id] = doc
    return doc


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_list_spaces_without_auth_returns_401() -> None:
    """GET /study-spaces without bearer token returns 401."""
    app, _, _ = create_inmemory_app(authenticated=False)
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
        app, _, _ = create_inmemory_app(authenticated=True)
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
    app, _, _ = create_inmemory_app(authenticated=False)
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
    from src.study_spaces.application.use_cases import (
        CreateStudySpaceUseCase,
        ListStudySpacesUseCase,
    )
    from src.study_spaces.domain.repositories import InMemoryStudySpaceRepository
    from src.study_spaces.infrastructure.controllers import (
        _get_create_space_use_case,
        _get_list_spaces_use_case,
    )

    app, doc_repo, _ = create_inmemory_app(authenticated=True)
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

    app, doc_repo, _ = create_inmemory_app(authenticated=True)
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

    app, doc_repo, _ = create_inmemory_app(authenticated=True)
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

    app, doc_repo, _ = create_inmemory_app(authenticated=True)
    space_repo = InMemoryStudySpaceRepository()

    # Document owned by the user but still processing
    doc = StudyDocument.create(
        id=uuid.uuid4(),
        filename="test.pdf",
        content_type="application/pdf",
        storage_path="study_documents/test.pdf",
        owner_user_id=OWNER_ID,
        study_space_id=uuid.uuid4(),
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


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_list_space_documents_without_auth_returns_401() -> None:
    """GET /study-spaces/{space_id}/documents without bearer token returns 401."""
    app, _, _ = create_inmemory_app(authenticated=False)
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(f"/study-spaces/{uuid.uuid4()}/documents")

    assert response.status_code == 401


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_list_space_documents_returns_owned_documents() -> None:
    """An authenticated user gets documents in their owned study space."""
    from src.study_spaces.application.use_cases import ListStudySpaceDocumentsUseCase
    from src.study_spaces.domain.repositories import InMemoryStudySpaceRepository
    from src.study_spaces.infrastructure.controllers import (
        _get_list_space_documents_use_case,
    )

    app, doc_repo, _ = create_inmemory_app(authenticated=True)
    space_repo = InMemoryStudySpaceRepository()
    space_id = uuid.uuid4()
    owner_id = OWNER_ID

    from src.study_spaces.domain.entities import StudySpace as SS

    space = SS.create(
        id=space_id, owner_id=owner_id, name="Test", document_ids=[uuid.uuid4()]
    )
    await space_repo.save(space)

    doc = StudyDocument.create(
        id=uuid.uuid4(),
        filename="test.pdf",
        content_type="application/pdf",
        storage_path="study_documents/test.pdf",
        owner_user_id=owner_id,
        study_space_id=space_id,
    )
    doc.mark_as_processing()
    doc.mark_as_ready(chunk_count=5)
    doc_repo._documents[doc.id] = doc

    async def override_list_docs() -> ListStudySpaceDocumentsUseCase:
        return ListStudySpaceDocumentsUseCase(
            space_repository=space_repo,
            document_repository=doc_repo,
        )

    app.dependency_overrides[_get_list_space_documents_use_case] = override_list_docs

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(
            f"/study-spaces/{space_id}/documents",
            headers={"Authorization": "Bearer test-token"},
        )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["filename"] == "test.pdf"
    assert data[0]["status"] == "READY"
    assert data[0]["chunks_count"] == 5


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_list_space_documents_foreign_space_returns_404() -> None:
    """A space owned by another user returns 404."""
    from src.study_spaces.application.use_cases import ListStudySpaceDocumentsUseCase
    from src.study_spaces.domain.repositories import InMemoryStudySpaceRepository
    from src.study_spaces.infrastructure.controllers import (
        _get_list_space_documents_use_case,
    )

    app, doc_repo, _ = create_inmemory_app(authenticated=True)
    space_repo = InMemoryStudySpaceRepository()
    space_id = uuid.uuid4()

    from src.study_spaces.domain.entities import StudySpace as SS

    space = SS.create(
        id=space_id, owner_id=uuid.uuid4(), name="Theirs", document_ids=[uuid.uuid4()]
    )
    await space_repo.save(space)

    async def override_list_docs() -> ListStudySpaceDocumentsUseCase:
        return ListStudySpaceDocumentsUseCase(
            space_repository=space_repo,
            document_repository=doc_repo,
        )

    app.dependency_overrides[_get_list_space_documents_use_case] = override_list_docs

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(
            f"/study-spaces/{space_id}/documents",
            headers={"Authorization": "Bearer test-token"},
        )

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "space_not_found"


class _FailingEmbeddingGenerator:
    async def generate(self, text: str) -> list[float]:
        raise AssertionError("embedding generation should not run")


class _FailingSearchRepository:
    async def find_nearest_by_embedding(
        self,
        embedding: list[float],
        limit: int,
        owner_id: uuid.UUID | None = None,
        study_space_id: uuid.UUID | None = None,
    ) -> list[object]:
        raise AssertionError("semantic search should not run")


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_search_foreign_space_returns_404() -> None:
    """Semantic search in another user's space returns 404."""
    from src.semantic_search.application.use_cases import SemanticSearchUseCase
    from src.study_spaces.domain.entities import StudySpace as SS
    from src.study_spaces.domain.repositories import InMemoryStudySpaceRepository
    from src.study_spaces.infrastructure.controllers import _get_search_use_case

    app, _, _ = create_inmemory_app(authenticated=True)
    space_repo = InMemoryStudySpaceRepository()
    space_id = uuid.uuid4()
    await space_repo.save(
        SS.create(
            id=space_id,
            owner_id=uuid.uuid4(),
            name="Theirs",
            document_ids=[uuid.uuid4()],
        )
    )

    async def override_search() -> SemanticSearchUseCase:
        return SemanticSearchUseCase(
            search_repository=_FailingSearchRepository(),
            embedding_generator=_FailingEmbeddingGenerator(),
            space_repository=space_repo,
        )

    app.dependency_overrides[_get_search_use_case] = override_search

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(
            f"/study-spaces/{space_id}/semantic-search",
            params={"query": "derecho administrativo"},
            headers={"Authorization": "Bearer test-token"},
        )

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "space_not_found"


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_search_missing_space_returns_404() -> None:
    """Semantic search in a missing space returns 404."""
    from src.semantic_search.application.use_cases import SemanticSearchUseCase
    from src.study_spaces.domain.repositories import InMemoryStudySpaceRepository
    from src.study_spaces.infrastructure.controllers import _get_search_use_case

    app, _, _ = create_inmemory_app(authenticated=True)
    space_repo = InMemoryStudySpaceRepository()

    async def override_search() -> SemanticSearchUseCase:
        return SemanticSearchUseCase(
            search_repository=_FailingSearchRepository(),
            embedding_generator=_FailingEmbeddingGenerator(),
            space_repository=space_repo,
        )

    app.dependency_overrides[_get_search_use_case] = override_search

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(
            f"/study-spaces/{uuid.uuid4()}/semantic-search",
            params={"query": "derecho administrativo"},
            headers={"Authorization": "Bearer test-token"},
        )

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "space_not_found"
