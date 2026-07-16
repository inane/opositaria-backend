"""Application factory wiring all dependencies together."""

from collections.abc import AsyncGenerator

from fastapi import Depends, FastAPI
from sqlalchemy.ext.asyncio import AsyncSession

from src.document_processing.infrastructure.embedding_generator import (
    NumpyEmbeddingGenerator,
)
from src.document_processing.infrastructure.rabbitmq_publisher import (
    RabbitMQProcessingPublisher,
)
from src.document_processing.infrastructure.repositories import (
    PostgresDocumentProcessingJobRepository,
)
from src.semantic_search.application.use_cases import (
    SemanticSearchUseCase,
)
from src.semantic_search.infrastructure.controllers import (
    _get_search_use_case,
    router as semantic_search_router,
)
from src.shared.infrastructure.database import (
    create_async_engine_from_settings,
    create_session_factory,
)
from src.shared.infrastructure.rabbitmq import create_rabbitmq_connection
from src.shared.infrastructure.settings import AuthSettings
from src.study_documents.application.use_cases import (
    GetStudyDocumentStatusUseCase,
    UploadStudyDocumentUseCase,
)
from src.study_documents.infrastructure.controllers import (
    _get_status_use_case,
    _get_upload_use_case,
    router as study_documents_router,
)
from src.study_documents.infrastructure.document_storage import LocalDocumentStorage
from src.study_documents.infrastructure.repositories import (
    PostgresSemanticChunkSearchRepository,
    PostgresStudyDocumentRepository,
)
from src.users.application.use_cases import (
    GetCurrentUserUseCase,
    LoginUserUseCase,
    RegisterUserUseCase,
)
from src.users.infrastructure.controllers import (
    _get_current_user_use_case,
    _get_login_use_case,
    _get_register_use_case,
    router as auth_router,
)
from src.users.infrastructure.repositories import PostgresUserRepository
from src.users.infrastructure.security import BcryptPasswordHasher, JwtTokenService
from src.study_spaces.application.use_cases import (
    CreateStudySpaceUseCase,
    ListStudySpacesUseCase,
)
from src.study_spaces.infrastructure.controllers import (
    _get_create_space_use_case,
    _get_list_spaces_use_case,
    router as study_spaces_router,
)
from src.study_spaces.infrastructure.repositories import (
    PostgresStudySpaceRepository,
)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(title="Opositaria Backend", version="0.1.0")

    engine = create_async_engine_from_settings()
    session_factory = create_session_factory(engine)

    # JWT and password hasher instances (no session needed)
    password_hasher = BcryptPasswordHasher()
    jwt_settings = AuthSettings()
    token_service = JwtTokenService(settings=jwt_settings)

    async def get_db() -> AsyncGenerator[AsyncSession, None]:
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    async def get_rabbitmq_publisher() -> RabbitMQProcessingPublisher:
        connection = await create_rabbitmq_connection()
        return RabbitMQProcessingPublisher(connection=connection)

    async def create_upload_use_case(
        session: AsyncSession = Depends(get_db),
        publisher: RabbitMQProcessingPublisher = Depends(get_rabbitmq_publisher),
    ) -> UploadStudyDocumentUseCase:
        doc_repo = PostgresStudyDocumentRepository(session)
        job_repo = PostgresDocumentProcessingJobRepository(session)
        storage = LocalDocumentStorage()
        return UploadStudyDocumentUseCase(
            document_repository=doc_repo,
            document_storage=storage,
            publisher=publisher,
            job_repository=job_repo,
        )

    async def create_status_use_case(
        session: AsyncSession = Depends(get_db),
    ) -> GetStudyDocumentStatusUseCase:
        doc_repo = PostgresStudyDocumentRepository(session)
        return GetStudyDocumentStatusUseCase(document_repository=doc_repo)

    async def create_search_use_case(
        session: AsyncSession = Depends(get_db),
    ) -> SemanticSearchUseCase:
        search_repo = PostgresSemanticChunkSearchRepository(session)
        embedding_generator = NumpyEmbeddingGenerator()
        return SemanticSearchUseCase(
            search_repository=search_repo,
            embedding_generator=embedding_generator,
        )

    app.dependency_overrides[_get_upload_use_case] = create_upload_use_case
    app.dependency_overrides[_get_status_use_case] = create_status_use_case
    app.dependency_overrides[_get_search_use_case] = create_search_use_case

    async def create_register_use_case(
        session: AsyncSession = Depends(get_db),
    ) -> RegisterUserUseCase:
        user_repo = PostgresUserRepository(session)
        return RegisterUserUseCase(
            user_repository=user_repo,
            password_hasher=password_hasher,
            token_service=token_service,
        )

    async def create_login_use_case(
        session: AsyncSession = Depends(get_db),
    ) -> LoginUserUseCase:
        user_repo = PostgresUserRepository(session)
        return LoginUserUseCase(
            user_repository=user_repo,
            password_hasher=password_hasher,
            token_service=token_service,
        )

    async def create_current_user_use_case(
        session: AsyncSession = Depends(get_db),
    ) -> GetCurrentUserUseCase:
        user_repo = PostgresUserRepository(session)
        return GetCurrentUserUseCase(
            user_repository=user_repo,
            token_service=token_service,
        )

    app.dependency_overrides[_get_register_use_case] = create_register_use_case
    app.dependency_overrides[_get_login_use_case] = create_login_use_case
    app.dependency_overrides[_get_current_user_use_case] = create_current_user_use_case

    async def create_create_space_use_case(
        session: AsyncSession = Depends(get_db),
    ) -> CreateStudySpaceUseCase:
        space_repo = PostgresStudySpaceRepository(session)
        doc_repo = PostgresStudyDocumentRepository(session)
        return CreateStudySpaceUseCase(
            space_repository=space_repo,
            document_repository=doc_repo,
        )

    async def create_list_spaces_use_case(
        session: AsyncSession = Depends(get_db),
    ) -> ListStudySpacesUseCase:
        space_repo = PostgresStudySpaceRepository(session)
        return ListStudySpacesUseCase(space_repository=space_repo)

    app.dependency_overrides[_get_create_space_use_case] = create_create_space_use_case
    app.dependency_overrides[_get_list_spaces_use_case] = create_list_spaces_use_case

    app.include_router(study_documents_router)
    app.include_router(semantic_search_router)
    app.include_router(auth_router)
    app.include_router(study_spaces_router)

    return app
