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
    SearchStudyDocumentsSemanticallyUseCase,
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


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(title="Opositaria Backend", version="0.1.0")

    engine = create_async_engine_from_settings()
    session_factory = create_session_factory(engine)

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
    ) -> SearchStudyDocumentsSemanticallyUseCase:
        search_repo = PostgresSemanticChunkSearchRepository(session)
        embedding_generator = NumpyEmbeddingGenerator()
        return SearchStudyDocumentsSemanticallyUseCase(
            search_repository=search_repo,
            embedding_generator=embedding_generator,
        )

    app.dependency_overrides[_get_upload_use_case] = create_upload_use_case
    app.dependency_overrides[_get_status_use_case] = create_status_use_case
    app.dependency_overrides[_get_search_use_case] = create_search_use_case

    app.include_router(study_documents_router)
    app.include_router(semantic_search_router)

    return app
