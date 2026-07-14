## 1. Project Infrastructure and Configuration

- [x] 1.1 Create a feature branch for `add-semantic-pdf-search` before implementation starts.
- [x] 1.2 Add Docker Compose service for PostgreSQL with a pgvector enabled and project-specific database, user, password, port, and volume.
- [x] 1.3 Add Docker Compose service for RabbitMQ with management UI, durable data volume, and project-specific ports.
- [x] 1.4 Add environment variables to `.env.example` for PostgreSQL async URL, RabbitMQ URL, document storage path, embedding model name, embedding dimension, default search limit, maximum search limit, maximum PDF size, and maximum chunk count.
- [x] 1.5 Add Python dependencies for async PostgreSQL, Alembic PostgreSQL support, pgvector SQLAlchemy integration, selectable-text PDF extraction, local embedding generation, and RabbitMQ client integration.
- [x] 1.6 Configure a shared PostgreSQL async engine / session factory without leaking SQLAlchemy imports into domain or application layers.
- [x] 1.7 Configure a shared RabbitMQ connection / publisher factory without leaking RabbitMQ imports into domain or application layers.
- [x] 1.8 Add local filesystem document storage directory configuration and development-safe defaults.
- [x] 1.9 Add Alembic migration that enables `CREATE EXTENSION IF NOT EXISTS vector`.
- [x] 1.10 Add Alembic migration for `study_documents`, `study_document_chunks`, and `document_processing_jobs` tables.
- [x] 1.11 Add Alembic migration for HNSW cosine vector index on chunk embeddings.
- [x] 1.12 Run migration smoke check against the Docker Compose PostgreSQL service.
- [x] 1.13 COMMIT with a conventional message for infrastructure and database setup.

## 2. Study Documents Domain

- [x] 2.1 RED write failing unit test for creating a `StudyDocument` in `PENDING_PROCESSING` with valid filename, content type, and storage reference → GREEN implements minimal `StudyDocument` entity/value objects → COMMIT → REFACTOR.
- [x] 2.2 RED write a failing unit test for rejecting invalid non-PDF content type at domain/application boundary → GREEN implement validation using domain error factory → COMMIT → REFACTOR.
- [x] 2.3 RED write failing unit test for marking a document as `PROCESSING` from `PENDING_PROCESSING` → GREEN implement status transition → COMMIT → REFACTOR.
- [x] 2.4 RED write failing unit test for marking a document as `READY` with chunk count from `PROCESSING` → GREEN implement ready transition → COMMIT → REFACTOR.
- [x] 2.5 RED write failing unit test for marking a document as `FAILED` with safe failure reason from pending or processing states → GREEN implement failed transition → COMMIT → REFACTOR.
- [x] 2.6 RED write failing unit test for preventing invalid lifecycle transitions such as `READY` back to `PROCESSING` → GREEN implement transition guards → COMMIT → REFACTOR.
- [x] 2.7 RED write failing unit test for creating `StudyDocumentChunk` with document identity, text, sequence number, optional page number, embedding vector, and embedding model → GREEN implements chunk entity/value objects → COMMIT → REFACTOR.
- [x] 2.8 RED write a failing unit test for rejecting blank chunk text → GREEN implement chunk text validation → COMMIT → REFACTOR.
- [x] 2.9 RED write a failing unit test for rejecting embedding vectors whose dimension does not match configured dimension → GREEN implement embedding vector validation → COMMIT → REFACTOR.
- [x] 2.10 RED write a failing unit test for preserving chunk sequence order in domain collections or repository retrieval contract → GREEN implement ordering behavior → COMMIT → REFACTOR.
- [x] 2.11 Add `StudyDocumentRepository` protocol with InMemory implementation in a domain repository file.
- [x] 2.12 Add `StudyDocumentChunkRepository` protocol with InMemory implementation in a domain repository file.
- [x] 2.13 RED write failing unit tests for InMemory study document repository save/find behavior → GREEN implement repository behavior → COMMIT → REFACTOR.
- [x] 2.14 RED write failing unit tests for InMemory chunk repository save, replace-by-document, and find-by-document behavior → GREEN implements repository behavior → COMMIT → REFACTOR.

## 3. Document Processing Domain

- [x] 3.1 RED write failing unit test for creating a `DocumentProcessingJob` in pending state for a document → GREEN implement job entity/value objects → COMMIT → REFACTOR.
- [x] 3.2 RED write a failing unit test for marking a processing job as a running → GREEN implement job running transition → COMMIT → REFACTOR.
- [x] 3.3 RED write a failing unit test for marking a processing job as completed → GREEN implement completion transition → COMMIT → REFACTOR.
- [x] 3.4 RED write a failing unit test for marking a processing job as failed with attempt count and safe failure reason → GREEN implement failure transition → COMMIT → REFACTOR.
- [x] 3.5 RED write a failing unit test for ignoring already completed duplicate job processing → GREEN implement idempotent status behavior → COMMIT → REFACTOR.
- [x] 3.6 Add `DocumentProcessingJobRepository` protocol with InMemory implementation.
- [x] 3.7 RED write failing unit tests for InMemory job repository save/find behavior → GREEN implements repository behavior → COMMIT → REFACTOR.

## 4. Semantic Search Domain

- [x] 4.1 RED write a failing unit test for creating valid non-blank semantic query text → GREEN implement semantic query value object → COMMIT → REFACTOR.
- [x] 4.2 RED write a failing unit test for rejecting blank semantic query text → GREEN implement validation → COMMIT → REFACTOR.
- [x] 4.3 RED write a failing unit test for applying the default search limit when omitted → GREEN implement a search limit value object → COMMIT → REFACTOR.
- [x] 4.4 RED write a failing unit test for rejecting search limits below a minimum or above maximum → GREEN implement limit validation → COMMIT → REFACTOR.
- [x] 4.5 RED write a failing unit test for creating a valid similarity score from a cosine search result → GREEN implement a similarity score value object → COMMIT → REFACTOR.

## 5. Study Documents Application Layer

- [x] 5.1 Define application DTOs for upload response and document status response.
- [x] 5.2 Define application port for `DocumentStorage` that saves uploaded PDF bytes and returns a storage reference.
- [x] 5.3 Define application port for publishing document processing requests.
- [x] 5.4 RED write failing use case unit test with InMemory repositories and publisher spy for successful PDF upload creating pending document, processing a job, storing file reference, publishing a message, and returning status → GREEN implement `UploadStudyDocumentUseCase` → COMMIT → REFACTOR.
- [x] 5.5 RED write a failing use case unit test for non-PDF upload rejection without storing file, creating a document, or publishing a message → GREEN implement a validation path → COMMIT → REFACTOR.
- [x] 5.6 RED write a failing use case unit test for empty upload rejection → GREEN implement an empty payload validation path → COMMIT → REFACTOR.
- [x] 5.7 RED write a failing use case unit test for publisher failure keeping a persisted document and job recoverable → GREEN implement recoverable failure behavior → COMMIT → REFACTOR.
- [x] 5.8 RED write failing use case unit test for retrieving pending document status → GREEN implement `GetStudyDocumentStatusUseCase` → COMMIT → REFACTOR.
- [x] 5.9 RED write a failing use case unit test for retrieving ready document status with chunk count → GREEN extend status use case → COMMIT → REFACTOR.
- [x] 5.10 RED write a failing use case unit test for retrieving failed document status with a safe failure reason → GREEN extend status use case → COMMIT → REFACTOR.
- [x] 5.11 RED write a failing use case unit test for missing document status raising not found domain error → GREEN implement a not found path → COMMIT → REFACTOR.

## 6. Document Processing Application Layer

- [x] 6.1 Define application ports for `PdfTextExtractor`, `TextChunker`, and `EmbeddingGenerator`.
- [x] 6.2 Define processing result DTOs or command objects for `ProcessStudyDocumentUseCase`.
- [x] 6.3 RED write failing use case unit test with InMemory repositories and stubs for successful processing flow from a pending job to a ready document with persisted chunks → GREEN implement `ProcessStudyDocumentUseCase` happy path → COMMIT → REFACTOR.
- [x] 6.4 RED write a failing use case unit test for marking document and job as processing before extraction starts → GREEN implement state update ordering → COMMIT → REFACTOR.
- [x] 6.5 RED write a failing use case unit test for PDF extraction returning no usable text causing a failed document and failed job → GREEN implements no-text failure path → COMMIT → REFACTOR.
- [x] 6.6 RED write a failing use case unit test for text chunker returning no chunks causing a failed document and failed job → GREEN implement no-chunks failure path → COMMIT → REFACTOR.
- [x] 6.7 RED write a failing use case unit test for embedding generation failure causing a failed document and failed job → GREEN implements an embedding failure path → COMMIT → REFACTOR.
- [x] 6.8 RED write a failing use case unit test for embedding dimension mismatch causing a failed document and failed job without persisted chunks → GREEN implement dimension guard → COMMIT → REFACTOR.
- [x] 6.9 RED write a failing use case unit test for a duplicate completed job message acknowledging idempotently without duplicating chunks → GREEN implement duplicate handling → COMMIT → REFACTOR.
- [x] 6.10 RED write a failing use case unit test for replacing existing document chunks during reprocessing → GREEN implement atomic replace behavior through repository contract → COMMIT → REFACTOR.
- [x] 6.11 RED write a failing use case unit test for preserving chunk sequence and optional page metadata from extraction/chunking output → GREEN implement mapping → COMMIT → REFACTOR.

## 7. Semantic Search Application Layer

- [x] 7.1 Define semantic search request and response DTOs including document metadata, chunk metadata, text, score, and limit.
- [x] 7.2 Define semantic chunk search repository/port for the nearest chunk retrieval by embedding and limit.
- [x] 7.3 RED write failing use case unit test with embedding stub and semantic search repository stub for returning ordered chunk matches with parent documents → GREEN implement `SearchStudyDocumentsSemanticallyUseCase` happy path → COMMIT → REFACTOR.
- [x] 7.4 RED write a failing use case unit test for blank query rejection before embedding generation → GREEN implement a validation path → COMMIT → REFACTOR.
- [x] 7.5 RED write a failing use case unit test for omitted limit applying default limit → GREEN implement a default limit path → COMMIT → REFACTOR.
- [x] 7.6 RED write a failing use case unit test for invalid limit rejection → GREEN implement an invalid limit path → COMMIT → REFACTOR.
- [x] 7.7 RED write a failing use case unit test for no ready chunks returning an empty result list → GREEN implements an empty search result path → COMMIT → REFACTOR.
- [x] 7.8 RED write a failing use case unit test for query embedding generation failure returning safe service error → GREEN implement safe failure mapping → COMMIT → REFACTOR.

## 8. Infrastructure: PostgreSQL and pgvector Adapters

- [x] 8.1 Add SQLAlchemy models/mappings for study documents, study document chunks, and processing jobs in infrastructure only.
- [x] 8.2 Add pgvector SQLAlchemy column mapping with configured embedding dimension.
- [x] 8.3 RED write integration test for PostgreSQL study document repository save/find/status persistence against a real pgvector-enabled database → GREEN implement repository adapter → COMMIT → REFACTOR.
- [x] 8.4 RED write integration test for PostgreSQL chunk repository save and find-by-document preserving order → GREEN implement repository adapter → COMMIT → REFACTOR.
- [x] 8.5 RED write integration test for chunk repository replace-by-document removing old chunks atomically → GREEN implement replace behavior → COMMIT → REFACTOR.
- [x] 8.6 RED write integration test for PostgreSQL processing job repository save/find/status persistence → GREEN implement repository adapter → COMMIT → REFACTOR.
- [x] 8.7 RED write integration test for semantic pgvector search returning chunks ordered by cosine distance and excluding non-ready documents → GREEN implement semantic search adapter → COMMIT → REFACTOR.
- [x] 8.8 RED write integration test confirming pgvector extension and HNSW cosine index exist after migrations → GREEN adjusts migrations if needed → COMMIT → REFACTOR.

## 9. Infrastructure: Document Storage, PDF Extraction, Chunking, and Embeddings

- [x] 9.1 RED write integration/unit test for local filesystem document storage saving and retrieving uploaded PDF bytes safely under a configured storage directory → GREEN implement storage adapter → COMMIT → REFACTOR.
- [x] 9.2 RED write integration test for selectable-text PDF extractor returning normalized text from a text PDF fixture → GREEN implement PDF extraction adapter → COMMIT → REFACTOR.
- [x] 9.3 RED write integration test for PDF extractor returning no usable text from an image-only or empty-text PDF fixture without OCR → GREEN implement no-text behavior → COMMIT → REFACTOR.
- [x] 9.4 RED write unit test for chunker splitting long text into ordered chunks within configured size/overlap limits → GREEN implement text chunker adapter/service → COMMIT → REFACTOR.
- [x] 9.5 RED write unit test for chunker preserving page metadata when available → GREEN implement page-aware chunk output → COMMIT → REFACTOR.
- [x] 9.6 RED write integration test for local embedding adapter producing vectors with configured dimension without cloud API calls → GREEN implement local embedding adapter → COMMIT → REFACTOR.
- [x] 9.7 RED write integration test for local embedding adapter surfacing safe failures when the model cannot load → GREEN implement safe adapter error handling → COMMIT → REFACTOR.

## 10. Infrastructure: RabbitMQ Messaging and Worker

- [x] 10.1 Define RabbitMQ queue name, exchange/routing convention, message schema, and durable queue configuration.
- [x] 10.2 RED write integration test for RabbitMQ publisher publishing document/job identifiers to the durable processing queue → GREEN implement publisher adapter → COMMIT → REFACTOR.
- [x] 10.3 RED write integration test for RabbitMQ consumer deserializing processing messages and invoking a worker handler → GREEN implement consumer adapter → COMMIT → REFACTOR.
- [x] 10.4 RED write an integration test for a worker acknowledging a message after successful processing → GREEN implement ack behavior → COMMIT → REFACTOR.
- [x] 10.5 RED write integration test for a worker not acknowledging or safely rejecting a message on recoverable processing failure, according to chosen retry policy → GREEN implement failure behavior → COMMIT → REFACTOR.
- [x] 10.6 Add a worker entrypoint command that wires repositories, PDF extractor, chunker, local embedding adapter, and RabbitMQ consumer through the factory.
- [x] 10.7 Add developer documentation or README section for starting API, PostgreSQL, RabbitMQ, and worker locally.
- [x] 10.8 COMMIT with a conventional message for RabbitMQ worker infrastructure.

## 11. HTTP API and E2E Behavior

- [x] 11.1 Add FastAPI controller for PDF study document upload using `UploadStudyDocumentUseCase`.
- [x] 11.2 Add FastAPI controller for document status using `GetStudyDocumentStatusUseCase`.
- [x] 11.3 Add FastAPI controller for semantic search using `SearchStudyDocumentsSemanticallyUseCase`.
- [x] 11.4 RED write E2E test for uploading a valid PDF returning `202 Accepted`, document identifier, and `PENDING_PROCESSING` status → GREEN implement HTTP route/wiring → COMMIT → REFACTOR.
- [x] 11.5 RED write E2E test for non-PDF upload returning validation error and creating no document → GREEN implements HTTP validation/error mapping → COMMIT → REFACTOR.
- [x] 11.6 RED write E2E test for retrieving missing document status returning not found → GREEN implement route/error mapping → COMMIT → REFACTOR.
- [x] 11.7 RED write E2E test for retrieving ready document status after seeded processing data → GREEN implement response mapping → COMMIT → REFACTOR.
- [x] 11.8 RED write E2E test for semantic search returning matched chunks with parent document metadata from seeded ready chunks → GREEN implement search route/wiring → COMMIT → REFACTOR.
- [x] 11.9 RED write E2E test for semantic search ignoring pending, processing, and failed documents → GREEN implement filtering through adapter/a use case → COMMIT → REFACTOR.
- [x] 11.10 RED write E2E test for a blank search query returning validation error → GREEN implement request validation → COMMIT → REFACTOR.
- [x] 11.11 RED write E2E test for invalid search limit returning validation error → GREEN implement limit validation mapping → COMMIT → REFACTOR.
- [x] 13.1 RED write integration/E2E flow test that uploads a text PDF, publishes a processing message, runs the worker handler, and observes document status `READY` with chunks persisted → GREEN complete missing wiring → COMMIT → REFACTOR.
- [x] 13.2 RED write integration/E2E flow test that processes a PDF with no selectable text and observes document status `FAILED` with safe reason → GREEN complete failure wiring → COMMIT → REFACTOR.
- [x] 13.3 RED write integration/E2E flow test that processes a document and then searches for text semantically, returning matching chunk and document metadata → GREEN complete full path → COMMIT → REFACTOR.
- [x] 13.4 RED write integration/E2E flow test for a duplicate RabbitMQ processing message not duplicating chunks → GREEN complete idempotency path → COMMIT → REFACTOR.

## 14. Documentation and Operational Notes

- [x] 14.1 Document how Alembic enables pgvector and why the Docker image must already include the extension.
- [x] 14.2 Document that Redis is intentionally out of scope and PostgreSQL is the canonical state store.
- [x] 14.3 Document that Kafka is intentionally out of scope for the MVP.
- [x] 14.4 Document that only selectable-text PDFs are supported and OCR is out of scope.
- [x] 14.5 Document how to run migrations, start RabbitMQ, run the worker, upload a PDF, check status, and run semantic search locally.
- [x] 14.6 COMMIT with a conventional message for documentation updates.

## 15. Final Validation and Review

- [x] 15.1 Run `uv run ruff format .` and commit formatting changes if any.
- [x] 15.2 Run `uv run ruff check .` and fix all lint issues.
- [x] 15.3 Run `uv run mypy src/` and fix all type issues.
- [x] 15.4 Run `uv run pytest` and fix all test failures.
- [x] 15.5 Run `/task-validate` and fix all findings.
- [x] 15.6 Run `/task-code-review` and fix design-principle findings.
- [x] 15.7 Run `/task-architecture-review` and fix layer-boundary findings.
- [x] 15.8 Run `/task-testing-review` and fix test-quality findings.
- [x] 15.9 Review OpenSpec specs against implemented behavior and capture any drift before archive.
- [x] 15.10 Create a final conventional commit for the completed change.
