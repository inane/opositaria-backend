"""Worker entrypoint that wires all dependencies."""

import asyncio

from src.document_processing.application.use_cases import ProcessStudyDocumentUseCase
from src.document_processing.infrastructure.embedding_generator import (
    NumpyEmbeddingGenerator,
)
from src.document_processing.infrastructure.pdf_extractor import PypdfTextExtractor
from src.document_processing.infrastructure.repositories import (
    PostgresDocumentProcessingJobRepository,
)
from src.document_processing.infrastructure.text_chunker import TextChunkerService
from src.document_processing.infrastructure.worker import DocumentProcessingWorker
from src.shared.infrastructure.database import (
    create_async_engine_from_settings,
    create_session_factory,
)
from src.shared.infrastructure.rabbitmq import create_rabbitmq_connection
from src.study_documents.infrastructure.repositories import (
    PostgresStudyDocumentChunkRepository,
    PostgresStudyDocumentRepository,
)


async def run_worker() -> None:
    """Run the document processing worker."""
    engine = create_async_engine_from_settings()
    session_factory = create_session_factory(engine)

    connection = await create_rabbitmq_connection()

    async with session_factory() as session:
        doc_repo = PostgresStudyDocumentRepository(session)
        chunk_repo = PostgresStudyDocumentChunkRepository(session)
        job_repo = PostgresDocumentProcessingJobRepository(session)

        process_use_case = ProcessStudyDocumentUseCase(
            document_repository=doc_repo,
            chunk_repository=chunk_repo,
            job_repository=job_repo,
            pdf_extractor=PypdfTextExtractor(),
            text_chunker=TextChunkerService(),
            embedding_generator=NumpyEmbeddingGenerator(),
        )

        worker = DocumentProcessingWorker(
            connection=connection,
            process_use_case=process_use_case,
        )

        await worker.start()


if __name__ == "__main__":
    asyncio.run(run_worker())
