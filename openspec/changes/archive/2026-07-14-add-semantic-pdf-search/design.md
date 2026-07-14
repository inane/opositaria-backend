## Context

The backend currently targets Python 3.12+, FastAPI, SQLAlchemy 2.0 async, Alembic, and Pydantic v2 with a hexagonal architecture organized by business module. The project needs semantic search over study notes where the initial source material is selectable-text PDF files.

The existing system-level PostgreSQL container uses `postgres:17-alpine`, is stopped, belongs outside the repository, and does not include pgvector. This change therefore introduces a repository-local development stack with PostgreSQL including pgvector and RabbitMQ.

The first semantic search target is PDF study documents. Scanned/image-only PDFs are out of scope. Embeddings must be generated locally at first, without requiring a cloud provider during runtime. The design must keep provider migration low-cost by depending on an application port rather than a concrete embedding implementation.

## Goals / Non-Goals

**Goals:**

- Persist uploaded PDF study documents and their processing lifecycle state.
- Process PDFs asynchronously through RabbitMQ workers.
- Keep PostgreSQL as the canonical source of truth for document and job state.
- Extract text from selectable-text PDFs.
- Split extracted text into searchable chunks.
- Generate local embeddings through an application port and infrastructure adapter.
- Store chunk embeddings in PostgreSQL using pgvector.
- Search chunks using cosine similarity and return both chunk matches and parent document metadata.
- Add pgvector indexes from the initial implementation.
- Keep the architecture hexagonal and vertically sliced by business module.

**Non-Goals:**

- OCR for scanned or image-only PDFs.
- Redis as a state machine or progress store in this change.
- Kafka event streaming.
- Cloud embedding providers.
- RAG, chat, answer synthesis, or LLM completion flows.
- Multi-user document ownership and authorization filtering.
- Hybrid lexical plus semantic ranking.
- Support for non-PDF uploads.

## Decisions

### Decision 1: Use PostgreSQL with pgvector from Docker Compose

Use a repository-local Docker Compose service based on a pgvector-enabled PostgreSQL image. Alembic will activate the extension with `CREATE EXTENSION IF NOT EXISTS vector` and create the required tables and indexes.

Alternatives considered:

- Reuse the existing system container: rejected because it is outside the repository, stopped, named for another database, and lacks pgvector.
- Install pgvector into `postgres:17-alpine`: rejected for MVP because a pgvector image is simpler and more reproducible.

### Decision 2: Store embeddings per document chunk

Model documents separately from chunks. A document owns metadata and lifecycle state; chunks own extracted text, optional page number, sequence position, embedding vector, and embedding model metadata.

Alternatives considered:

- One embedding per whole PDF: rejected because long notes can cover multiple topics and would produce coarse search results.
- Store only chunks without document aggregate metadata: rejected because search must return parent documents and clients need document processing status.

### Decision 3: Keep `study_documents` as the document module and add focused supporting modules

Use business module boundaries:

- `study_documents`: document aggregate, chunks, upload/status use cases, repositories, HTTP endpoints.
- `document_processing`: asynchronous processing workflow, processing job lifecycle, worker entrypoint, RabbitMQ ports/adapters.
- `semantic_search`: search query use case, semantic result DTOs, vector search repository port, HTTP endpoint.

The modules may import domain entities and ports from each other when needed, but no use case imports another use case.

Alternatives considered:

- Put everything under one `notes` or `study_documents` module: rejected because RabbitMQ worker orchestration and semantic querying are separate business capabilities with different lifecycle and test boundaries.
- Create a generic `ai` module: rejected because it names a technology area rather than a business capability.

### Decision 4: Use RabbitMQ for asynchronous PDF processing

On upload, the API stores a document with `PENDING_PROCESSING`, publishes a processing command to RabbitMQ, and returns `202 Accepted`. A worker consumes the message, marks the document as `PROCESSING`, extracts text, chunks it, generates embeddings, stores chunks, and finally marks the document as `READY` or `FAILED`.

RabbitMQ messages contain identifiers only, such as `document_id` and `job_id`. PostgreSQL remains the source of truth.

Alternatives considered:

- FastAPI `BackgroundTasks`: rejected as the primary mechanism because PDF extraction and local embeddings can be heavy and tasks can be lost on process restart.
- PostgreSQL-backed queue only: viable but rejected because the user prefers a real broker-style approach.
- Kafka: rejected for MVP because event streaming, offsets, partitions, and consumer group management are unnecessary for one document-processing worker flow.

### Decision 5: Persist canonical processing state in PostgreSQL, not Redis

Document state is business data and must survive restarts and operational cache loss. PostgreSQL stores stable states such as `PENDING_PROCESSING`, `PROCESSING`, `READY`, and `FAILED`. Redis is not introduced in this change.

Alternatives considered:

- Redis as the state machine: rejected because document lifecycle state is canonical business data and should not depend on cache-style persistence semantics.
- Redis for transient progress: deferred; it can be added later for UI progress without changing canonical state.

### Decision 6: Use local embeddings behind an application port

Define an `EmbeddingGenerator` application port that receives text and returns a typed embedding vector. The first production adapter uses a local model. Tests use deterministic stubs or fake adapters for application ports, not repository mocks.

The vector dimension must be explicit and consistent across the local model, database column type, and validation. The initial dimension should be set once the local model is selected during implementation.

Alternatives considered:

- Direct OpenAI/cloud adapter: rejected for initial scope because runtime must not require internet.
- Hard-code local embedding code inside use cases: rejected because it would couple application logic to a provider and make future provider migration expensive.

### Decision 7: Use cosine similarity and an HNSW pgvector index

Use cosine distance for text embeddings and create an HNSW index for the chunk embedding column. Search orders by vector distance and limits results to the requested top matches.

Alternatives considered:

- No index initially: rejected because the proposal explicitly includes vector indexing from the start.
- IVFFlat: deferred because HNSW avoids training-list tuning for the MVP and is a strong default for approximate nearest-neighbor search.

### Decision 8: Fail unsupported PDFs explicitly

Only PDFs with extractable selectable text are accepted for processing. If extraction yields no usable text, the document becomes `FAILED` with a safe business error message.

Alternatives considered:

- Try OCR fallback: rejected because OCR substantially increases dependencies, runtime cost, and failure modes.
- Accept empty documents as ready: rejected because they would produce no meaningful search results.

## Component Mapping

### `study_documents` module

Domain:

- `StudyDocument` entity with identity, filename, content type, storage reference, status, optional failure reason, timestamps, and chunk count.
- `StudyDocumentChunk` entity with identity, document identity, text, sequence number, optional page number, and embedding metadata.
- Value objects for document identity, chunk identity, document status, chunk text, and embedding vector where useful.
- `StudyDocumentRepository` interface plus InMemory implementation.
- `StudyDocumentChunkRepository` interface plus InMemory implementation.

Application:

- `UploadStudyDocumentUseCase` validates upload metadata, persists the document, creates processing state, publishes a processing request through a port, and returns document status.
- `GetStudyDocumentStatusUseCase` returns stable document lifecycle state.
- Application port `DocumentStorage` for saving uploaded PDF bytes.

Infrastructure:

- SQLAlchemy PostgreSQL repository adapters.
- Local filesystem document storage adapter for development.
- FastAPI controller for upload and status endpoints.

### `document_processing` module

Domain:

- `DocumentProcessingJob` entity with job identity, document identity, status, attempt count, and failure reason.
- `DocumentProcessingJobRepository` interface plus InMemory implementation.

Application:

- `ProcessStudyDocumentUseCase` orchestrates the worker flow: load document, mark processing, extract text, chunk text, generate embeddings, store chunks, mark ready or failed.
- Ports: `PdfTextExtractor`, `TextChunker`, `EmbeddingGenerator`, and `ProcessingJobPublisher` or equivalent message publishing port.

Infrastructure:

- RabbitMQ publisher adapter.
- RabbitMQ consumer/worker entrypoint.
- PDF text extraction adapter for selectable-text PDFs.
- Local embedding generator adapter.

### `semantic_search` module

Domain:

- Value objects for semantic query text, similarity score, and search limit.

Application:

- `SearchStudyDocumentsSemanticallyUseCase` generates an embedding for the query and asks a vector search repository for nearest chunks.
- DTOs for matched documents and matched chunks.
- Port or repository interface for semantic chunk search.

Infrastructure:

- SQLAlchemy pgvector search adapter using cosine distance and result limit.
- FastAPI controller for semantic search endpoint.

### Shared infrastructure

- Database engine/session factory for PostgreSQL async access.
- Alembic migrations for pgvector extension, tables, and indexes.
- Application factory wiring repositories, ports, controllers, RabbitMQ publisher, and worker dependencies.
- Docker Compose services for PostgreSQL with pgvector and RabbitMQ.

## Data Model

Conceptual tables:

- `study_documents`
  - `id`
  - `filename`
  - `content_type`
  - `storage_path`
  - `status`
  - `failure_reason`
  - `chunks_count`
  - `created_at`
  - `updated_at`
  - `processed_at`
- `study_document_chunks`
  - `id`
  - `document_id`
  - `text`
  - `sequence_number`
  - `page_number`
  - `embedding vector(<dimension>)`
  - `embedding_model`
  - `created_at`
- `document_processing_jobs`
  - `id`
  - `document_id`
  - `status`
  - `attempts`
  - `failure_reason`
  - `created_at`
  - `updated_at`
  - `completed_at`

The exact vector dimension is fixed after choosing the local embedding model. The model name and dimension must be stored or configured so migrations, adapters, and validation remain aligned.

## Processing Flow

```text
POST /study-documents
  ├─ validate PDF metadata
  ├─ store PDF bytes
  ├─ persist StudyDocument(PENDING_PROCESSING)
  ├─ persist DocumentProcessingJob(PENDING)
  ├─ publish RabbitMQ message(document_id, job_id)
  └─ return 202 Accepted with document status

Worker consumes message
  ├─ load job and document
  ├─ mark job/document PROCESSING
  ├─ extract selectable text from PDF
  ├─ fail if no usable text
  ├─ split text into chunks
  ├─ generate local embeddings per chunk
  ├─ save chunks with pgvector embeddings
  ├─ mark job COMPLETED
  └─ mark document READY
```

## Search Flow

```text
POST /semantic-search
  ├─ validate query text and limit
  ├─ generate local query embedding
  ├─ query pgvector by cosine distance over READY document chunks
  └─ return matched chunks grouped or annotated with parent document metadata
```

## Risks / Trade-offs

- Local embedding dependency may be large or CPU-heavy → keep it behind a port, choose a small multilingual model, and use deterministic stubs in unit tests.
- Vector dimension can drift from the chosen model → centralize model configuration and validate embedding dimensions before persistence.
- RabbitMQ publish can fail after the document is saved → persist a processing job first and expose a retry/requeue path in implementation tasks.
- Worker can process the same message more than once → make processing idempotent by checking job/document state and replacing chunks for a document inside a transaction.
- Large PDFs can produce many chunks and slow processing → enforce upload size and chunk count limits in application rules.
- PDF extraction can produce poor text ordering → keep OCR and advanced layout reconstruction out of scope; preserve page and sequence metadata to improve later ranking.
- pgvector integration tests require a real PostgreSQL service with the extension → run integration tests against the Docker Compose database, not SQLite.
- HNSW index creation can be slow on large data → acceptable for MVP; migrations should be reviewed before production-size datasets.

## Migration Plan

1. Add Docker Compose services for PostgreSQL with pgvector and RabbitMQ.
2. Add configuration for PostgreSQL, RabbitMQ, document storage path, local embedding model, vector dimension, and processing limits.
3. Add Alembic migration to enable `vector` extension.
4. Add Alembic migration for `study_documents`, `study_document_chunks`, and `document_processing_jobs`.
5. Add HNSW vector index using cosine operator class for chunk embeddings.
6. Implement modules inside-out with TDD: domain, application, infrastructure adapters, HTTP, worker.
7. Verify migrations and integration tests against the pgvector-enabled PostgreSQL service.

Rollback strategy:

- Stop the worker before rolling back schema that affects processing tables.
- Roll back Alembic revisions in reverse order.
- Drop RabbitMQ messages for jobs whose persisted documents no longer exist.
- Keep uploaded PDF files in development storage unless explicit cleanup is added.

## Open Questions

- Which exact local embedding model will be selected for the first implementation, and therefore what vector dimension should the migration use?
- What maximum PDF size and maximum extracted chunk count should the API allow for the MVP?
- Should failed jobs be manually requeued through an endpoint in this first change or only via internal tooling?
