# Opositaria Backend - Semantic PDF Search

## Prerequisites

- Docker and Docker Compose
- Python 3.12+ (3.12 or 3.13 recommended; 3.14 has limited ML library support)
- `uv` (Python package manager)

## Quick Start

### 1. Start local infrastructure and worker

```bash
# Start PostgreSQL, RabbitMQ, and the worker
docker compose up -d

# Verify services are healthy/running
docker compose ps
```

This starts:

- `postgres`: PostgreSQL with pgvector on `localhost:5433`
- `rabbitmq`: RabbitMQ on `localhost:5673` and management UI on `localhost:15673`
- `worker`: RabbitMQ consumer for asynchronous document processing

The worker mounts the local `./data/documents` directory at
`/app/data/documents`, so PDFs uploaded by the local API are readable by the
worker container.

### 2. Install Dependencies

```bash
# Core dependencies
uv sync

# For local embeddings (requires Python 3.12 or 3.13):
uv sync --extra ml
```

### 3. Start the API locally

```bash
uv run uvicorn src.main:app --reload --port 8000
```

This is the recommended development flow: edit code locally, keep FastAPI on
`--reload`, and let Docker run PostgreSQL, RabbitMQ, and the worker.

Run migrations from your host when the schema changes:

```bash
uv run alembic upgrade head
```

Alternatively, run the one-shot migration container:

```bash
docker compose --profile migrate up migrate
```

### 4. Optional: start only infrastructure

If you want to run both API and worker manually on your host, start only
PostgreSQL and RabbitMQ:

```bash
docker compose up -d postgres rabbitmq
uv run alembic upgrade head
```

Then run the worker manually in a separate terminal:

```bash
uv run python -m src.document_processing.infrastructure.worker_entrypoint
```

### 5. Optional: run the API in Docker

The API container is available behind the `api` Compose profile:

```bash
docker compose --profile api up -d --build
```

This starts the `opositaria-api` container on `localhost:8000`. For day-to-day
local development, prefer the local `uvicorn --reload` command above.

The migrations prepare the database schema, including pgvector, users, study
documents, document processing jobs, semantic-search chunks, and study spaces.

## API Endpoints

### Upload a PDF

```bash
curl -X POST http://localhost:8000/study-documents/upload \
  -F "file=@/path/to/document.pdf"
```

Returns `202 Accepted` with document ID and `PENDING_PROCESSING` status on success.

**Error responses:**

| Status | Code | Description |
|--------|------|-------------|
| `413 Payload Too Large` | `file_too_large` | Upload exceeds the 50 MB size limit |
| `422 Unprocessable Content` | `empty_upload` | Upload content is empty |
| `422 Unprocessable Content` | `invalid_file_type` | File is not a PDF (wrong content type or extension) |
| `422 Unprocessable Content` | `invalid_filename` | Filename contains invalid characters (blank, reserved, path separators, control characters, or exceeds 255 chars) |

Error payloads are structured JSON:
```json
{
  "detail": {
    "code": "file_too_large",
    "message": "Upload content exceeds the 50 MB size limit"
  }
}
```

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
