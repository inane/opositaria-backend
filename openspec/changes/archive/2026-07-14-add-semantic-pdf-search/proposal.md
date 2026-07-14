## Why

The project needs searchable study material based on the meaning of PDF notes, not only exact keyword matches. PostgreSQL with pgvector enables semantic retrieval while keeping document metadata, chunks, and embeddings in the same relational database used by the backend.

## What Changes

- Add a development Docker Compose environment with PostgreSQL, including the pgvector extension and RabbitMQ for asynchronous document processing.
- Add database migrations that enable pgvector and persist study documents, document chunks, vector embeddings, and processing state.
- Add support for uploading selectable-text PDF study documents.
- Add asynchronous PDF processing through RabbitMQ workers while PostgreSQL remains the canonical source of truth for document state.
- Add local embedding generation behind an application port so cloud providers can be introduced later with low migration cost.
- Add semantic search over processed PDF chunks using cosine similarity and a pgvector index.
- Return both matched chunks and their parent documents in semantic search results.
- Expose processing status so clients can tell whether a document is pending, processing, ready, or failed.
- Exclude Redis from the initial implementation; it may be added later only for transient progress reporting.
- Exclude Kafka from the MVP.

## Non-goals

- No OCR for scanned PDFs or image-only documents.
- No cloud embedding provider in the initial implementation.
- No chat, RAG answer generation, or conversational interface.
- No multi-user document ownership or per-user search filtering yet.
- No hybrid lexical plus semantic ranking in the initial implementation.
- No Redis-based state machine in the initial implementation.
- No Kafka-based event streaming in the initial implementation.
- No support for DOCX, Markdown upload, web pages, or arbitrary file formats.

## Capabilities

### New Capabilities

- `study-documents`: Upload, persist, process, and inspect selectable-text PDF study documents.
- `semantic-search`: Search processed study document chunks by meaning and return matching chunks with parent document metadata.
- `document-processing`: Process uploaded PDFs asynchronously through RabbitMQ workers and persist lifecycle state in PostgreSQL.

### Modified Capabilities

- None.

## Impact

- Affected modules: new `study_documents`, `semantic_search`, and `document_processing` business modules, plus shared database and messaging infrastructure.
- API impact: new HTTP endpoints for PDF upload, document status retrieval, and semantic search.
- Database impact: PostgreSQL becomes the development database target; Alembic migrations enable pgvector and create a document, chunk, embedding, and processing state tables.
- Infrastructure impact: add Docker Compose services for PostgreSQL with pgvector and RabbitMQ.
- Dependency impact: add Python dependencies for PostgreSQL async access, pgvector integration, PDF text extraction, local embeddings, and RabbitMQ messaging.
- Operational impact: add a worker process that consumes RabbitMQ messages and updates PostgreSQL document state.
