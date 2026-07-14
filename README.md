# Opositaria Backend - Semantic PDF Search

## Prerequisites

- Docker and Docker Compose
- Python 3.12+ (3.12 or 3.13 recommended; 3.14 has limited ML library support)
- `uv` (Python package manager)

## Quick Start

### 1. Start Infrastructure

```bash
# Start PostgreSQL (with pgvector) and RabbitMQ
docker compose up -d

# Verify both services are healthy
docker compose ps
```

### 2. Run Database Migrations

```bash
uv run alembic upgrade head
```

This applies three migrations:
1. Enables the `vector` extension (pgvector)
2. Creates `study_documents`, `study_document_chunks`, and `document_processing_jobs` tables
3. Creates an HNSW cosine vector index on chunk embeddings

### 3. Install Dependencies

```bash
# Core dependencies
uv sync

# For local embeddings (requires Python 3.12 or 3.13):
uv sync --extra ml
```

### 4. Start the API

```bash
uv run uvicorn src.main:app --reload --port 8000
```

### 5. Start the Worker (separate terminal)

```bash
uv run python -m src.document_processing.infrastructure.worker_entrypoint
```

## API Endpoints

### Upload a PDF

```bash
curl -X POST http://localhost:8000/study-documents/upload \
  -F "file=@/path/to/document.pdf"
```

Returns `202 Accepted` with document ID and `PENDING_PROCESSING` status.

### Check Document Status

```bash
curl http://localhost:8000/study-documents/{document_id}/status
```

Returns the current lifecycle status: `PENDING_PROCESSING`, `PROCESSING`, `READY`, or `FAILED`.

### Semantic Search

```bash
curl -X POST http://localhost:8000/semantic-search/search \
  -H "Content-Type: application/json" \
  -d '{"query": "derecho administrativo", "limit": 10}'
```

Returns matched chunks ordered by cosine similarity with parent document metadata.

## Architecture Notes

### pgvector

The `vector` extension is enabled via Alembic migration. The Docker image `pgvector/pgvector:pg17` already includes the extension - it is a PostgreSQL 17 image with pgvector pre-installed.

### PostgreSQL as Canonical State Store

Document lifecycle state and processing job state are persisted exclusively in PostgreSQL. Redis is intentionally out of scope for the MVP. If Redis is added later, it would only be for transient progress reporting, not for canonical state.

### RabbitMQ over Kafka

RabbitMQ is used for the MVP's asynchronous document processing. Kafka is intentionally out of scope - its offset management, consumer groups, and partitioning are unnecessary overhead for a single document-processing worker flow.

### PDF Support (Selectable Text Only)

Only selectable-text PDFs are supported. OCR for scanned/image-only PDFs is out of scope. If a PDF has no extractable text, the document transitions to `FAILED` with a clear failure reason.

### Embeddings

Local embeddings are generated using numpy (development) or sentence-transformers (production, requires `uv sync --extra ml`). The embedding dimension is 384 (all-MiniLM-L6-v2). The dimension is validated before persistence to prevent data corruption.

## Running Tests

```bash
# Unit tests (fast, no external deps)
uv run pytest src/ -m unit -v

# Integration tests (require PostgreSQL)
uv run pytest src/ -m integration -v

# All tests
uv run pytest src/ -v
```
