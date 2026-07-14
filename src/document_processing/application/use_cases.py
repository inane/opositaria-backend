"""Application use case for processing study documents."""

import uuid

from src.document_processing.application.ports import (
    EmbeddingGenerator,
    PdfTextExtractor,
    TextChunker,
)
from src.document_processing.domain.entities import (
    DocumentProcessingError,
)
from src.document_processing.domain.repositories import DocumentProcessingJobRepository
from src.study_documents.domain.entities import (
    EMBEDDING_DIMENSION,
    StudyDocumentChunk,
    StudyDocumentError,
)
from src.study_documents.domain.repositories import (
    StudyDocumentChunkRepository,
    StudyDocumentRepository,
)


def _safe_failure_reason(error: Exception) -> str:
    """Return a user-safe failure reason without exposing internals."""
    if isinstance(error, StudyDocumentError) and error.safe:
        return error.code if error.code else str(error)
    return "Document processing failed due to an internal error"


class ProcessStudyDocumentUseCase:
    """Orchestrates the worker flow: extract, chunk, embed, persist."""

    def __init__(
        self,
        document_repository: StudyDocumentRepository,
        chunk_repository: StudyDocumentChunkRepository,
        job_repository: DocumentProcessingJobRepository,
        pdf_extractor: PdfTextExtractor,
        text_chunker: TextChunker,
        embedding_generator: EmbeddingGenerator,
    ) -> None:
        self._document_repository = document_repository
        self._chunk_repository = chunk_repository
        self._job_repository = job_repository
        self._pdf_extractor = pdf_extractor
        self._text_chunker = text_chunker
        self._embedding_generator = embedding_generator

    async def execute(self, job_id: uuid.UUID) -> None:
        """Process a document processing job."""
        job = await self._job_repository.find_by_id(job_id)
        if job is None:
            raise DocumentProcessingError(f"Job {job_id} not found")

        if job.status in {"COMPLETED", "FAILED"}:
            return

        document = await self._document_repository.find_by_id(job.document_id)
        if document is None:
            raise DocumentProcessingError(f"Document {job.document_id} not found")

        job.mark_as_running()
        document.mark_as_processing()
        await self._job_repository.save(job)
        await self._document_repository.save(document)
        await self._job_repository.flush()
        await self._document_repository.flush()

        try:
            text = await self._pdf_extractor.extract_text(document.storage_path)
            if not text:
                raise StudyDocumentError(
                    "No extractable text found in PDF",
                    safe=True,
                    code="no_extractable_text",
                )

            chunks = await self._text_chunker.chunk_text(text)
            if not chunks:
                raise StudyDocumentError("Text chunking produced no chunks", safe=True)

            doc_chunks = []
            for i, (chunk_text, page_number) in enumerate(chunks, start=1):
                embedding = await self._embedding_generator.generate(chunk_text)
                if len(embedding) != EMBEDDING_DIMENSION:
                    raise StudyDocumentError(
                        f"Embedding dimension {len(embedding)} does not match configured {EMBEDDING_DIMENSION}"
                    )
                doc_chunk = StudyDocumentChunk.create(
                    id=uuid.uuid4(),
                    document_id=document.id,
                    text=chunk_text,
                    sequence_number=i,
                    embedding=embedding,
                    embedding_model="all-MiniLM-L6-v2",
                    page_number=page_number,
                )
                doc_chunks.append(doc_chunk)

            await self._chunk_repository.replace_by_document_id(document.id, doc_chunks)

            document.mark_as_ready(chunk_count=len(doc_chunks))
            job.mark_as_completed()
        except Exception as e:
            reason = _safe_failure_reason(e)
            document.mark_as_failed(failure_reason=reason)
            job.mark_as_failed(failure_reason=reason)
        finally:
            await self._job_repository.save(job)
            await self._document_repository.save(document)
            await self._job_repository.commit()
            await self._document_repository.commit()
