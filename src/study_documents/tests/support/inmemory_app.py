"""Test helper: create a FastAPI app with InMemory repositories for e2e tests."""

import uuid
from dataclasses import dataclass, field

from fastapi import FastAPI

from src.document_processing.domain.repositories import (
    InMemoryDocumentProcessingJobRepository,
)
from src.shared.infrastructure.factory import create_app
from src.study_documents.application.use_cases import (
    GetStudyDocumentStatusUseCase,
    UploadStudyDocumentUseCase,
)
from src.study_documents.domain.repositories import InMemoryStudyDocumentRepository
from src.study_documents.infrastructure.controllers import (
    _get_status_use_case,
    _get_upload_use_case,
)
from src.study_spaces.application.use_cases import (
    ListStudySpaceDocumentsUseCase,
    ListStudySpacesUseCase,
)
from src.study_spaces.domain.repositories import InMemoryStudySpaceRepository
from src.study_spaces.infrastructure.controllers import (
    _get_list_space_documents_use_case,
    _get_list_spaces_use_case,
)
from src.users.infrastructure.controllers import (
    _get_current_user_use_case,
    get_bearer_token,
)
from src.users.domain.entities import User

OWNER_ID = uuid.uuid4()


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


def create_inmemory_app(
    authenticated: bool = False,
) -> tuple[FastAPI, InMemoryStudyDocumentRepository, InMemoryStudySpaceRepository]:
    """Create a test app with InMemory repositories and stubs.

    If authenticated=True, the app accepts any bearer token and resolves
    a fixed owner user.
    """
    app = create_app()
    doc_repo = InMemoryStudyDocumentRepository()
    job_repo = InMemoryDocumentProcessingJobRepository()
    space_repo = InMemoryStudySpaceRepository()
    storage = DocumentStorageStub()
    publisher = PublisherStub()

    async def override_upload_use_case() -> UploadStudyDocumentUseCase:
        return UploadStudyDocumentUseCase(
            document_repository=doc_repo,
            document_storage=storage,
            publisher=publisher,
            job_repository=job_repo,
            space_repository=space_repo,
        )

    async def override_status_use_case() -> GetStudyDocumentStatusUseCase:
        return GetStudyDocumentStatusUseCase(document_repository=doc_repo)

    app.dependency_overrides[_get_upload_use_case] = override_upload_use_case
    app.dependency_overrides[_get_status_use_case] = override_status_use_case

    async def override_list_spaces_use_case() -> ListStudySpacesUseCase:
        return ListStudySpacesUseCase(space_repository=space_repo)

    async def override_list_space_docs_use_case() -> ListStudySpaceDocumentsUseCase:
        return ListStudySpaceDocumentsUseCase(
            space_repository=space_repo,
            document_repository=doc_repo,
        )

    app.dependency_overrides[_get_list_spaces_use_case] = override_list_spaces_use_case
    app.dependency_overrides[_get_list_space_documents_use_case] = override_list_space_docs_use_case

    if authenticated:
        user = User(id=OWNER_ID, email="test@example.com", password_hash="hash")

        async def override_get_bearer_token() -> str:
            return "test-token"

        class StubGetCurrentUser:
            async def execute(self, token: str) -> User:
                return user

        async def override_get_current_user() -> StubGetCurrentUser:
            return StubGetCurrentUser()

        app.dependency_overrides[get_bearer_token] = override_get_bearer_token
        app.dependency_overrides[_get_current_user_use_case] = override_get_current_user

    return app, doc_repo, space_repo
