# Proposed spec updates for `add-semantic-pdf-search`

These are proposed clarifications only. Do not apply automatically.

## Cross-cutting review notes

- The implementation uses `RUNNING` for processing-job lifecycle state while documents use `PROCESSING`. The current spec says the worker marks "the job and document" as `PROCESSING`, which does not match the implemented job vocabulary.
- Several scenarios require a "safe" error or failure reason, but the spec does not define the allowed shape of safe messages or how HTTP adapters should map domain/application errors.
- Some durability/acknowledgement behavior is implied but not explicit enough to distinguish a recoverable implementation from one that loses messages or records during partial failures.

## Study Documents

### Clarify upload validation status codes

The current spec requires validation errors for rejected uploads but does not define the HTTP status expected by the API adapter.

Proposed addition under each rejected upload scenario:

- **AND** the HTTP API SHALL return `422 Unprocessable Content`/`422 Unprocessable Entity` for validation failures.

### Clarify filename/content-type validation precedence

The current non-PDF scenario says "content type or extension is not PDF". This can be interpreted as requiring rejection when either field is invalid, even if the other field looks valid.

Proposed replacement:

- **GIVEN** a client has a file whose content type is not `application/pdf` or whose filename extension is not `.pdf`
- **WHEN** the client uploads the file as a study document
- **THEN** the system SHALL reject the upload with a validation error

## Semantic Search

### Clarify safe service error mapping

The current spec requires a safe service error when query embedding generation fails, but does not define whether this is an application error type or an HTTP response status.

Proposed addition:

- **AND** the HTTP API SHALL map query embedding generation failures to a safe `5xx` service error response without exposing stack traces, model paths, or provider details.

### Clarify similarity score semantics

The current spec requires a similarity score but does not define whether it is cosine distance, `1 - distance`, or a normalized similarity value.

Proposed addition under "Result includes chunk and document metadata":

- **AND** the similarity score SHALL be a normalized similarity value where higher scores represent more similar chunks.

### Clarify status filtering coverage

The current "Ignore unprocessed documents" scenario lists `PENDING_PROCESSING`, `PROCESSING`, and `FAILED`, but the implementation enforces this through a single `READY` filter.

Proposed addition:

- **AND** the system SHALL return only chunks whose parent document status is exactly `READY`.

## Embedding adapter

### Clarify local development fallback

The implementation uses a deterministic local NumPy embedding adapter for development because the target transformer runtime is not available in the current Python 3.14 environment, while preserving the embedding port boundary and 384-dimensional vectors.

Proposed addition under "Generate embeddings locally":

- **AND** local development and test environments MAY use a deterministic local embedding adapter when it satisfies the configured embedding dimension and does not require external cloud APIs.

## Document Processing

### Align processing job lifecycle terminology

The implementation uses `DocumentProcessingJobStatus.RUNNING` once a worker claims a job, while document status remains `PROCESSING`. This appears to be an intentional domain distinction, but the spec currently says both job and document are marked `PROCESSING`.

Proposed replacement under "Worker processes a pending job":

- **THEN** the system SHALL mark the processing job as `RUNNING`
- **AND** the system SHALL mark the study document as `PROCESSING`
- **AND** the system SHALL extract text, chunk text, generate embeddings, persist chunks, and mark the document `READY`

### Define safe failure reason expectations

The current spec requires safe failure reasons but does not define what makes a reason safe.

Proposed addition under "Worker fails a job safely" and "Uploaded PDF has no extractable text":

- **AND** safe failure reasons SHALL be user-safe messages that do not expose stack traces, filesystem paths, model internals, broker connection details, or raw infrastructure exception text.

### Clarify durable persistence before publishing

The current spec says the study document and processing job are "persisted" before RabbitMQ publishing, but the implementation review surfaced that a database `flush()` is not durable if the request transaction rolls back after a publish failure.

Proposed addition under "Publishing fails after document persistence":

- **AND** the persisted study document and processing job SHALL be durably committed, or otherwise recoverable through a transactional outbox, before RabbitMQ publishing can cause the upload transaction to roll back.

### Clarify worker acknowledgement ordering

The current worker scenarios say processing transaction completes, but do not explicitly define RabbitMQ acknowledgement ordering.

Proposed addition under "Worker completes a job":

- **AND** the worker SHALL commit document, job, and chunk state before acknowledging the RabbitMQ message.

Proposed addition under "Worker fails a job safely":

- **AND** the worker SHALL commit the failed document and job state before acknowledging or rejecting the RabbitMQ message.

### Clarify duplicate-message idempotency

The current duplicate-message scenario says chunks must not be duplicated, but it does not define whether the already-ready document and existing chunks must remain unchanged.

Proposed addition under "Duplicate processing message":

- **AND** the system SHALL leave the ready document status and existing chunks unchanged when acknowledging a duplicate completed job message.

### Clarify broker restart verifiability

The current "State survives broker restart" scenario is operationally correct but hard to verify deterministically in unit tests.

Proposed addition:

- **AND** repository-backed document and job state SHALL be recoverable independently of RabbitMQ queue contents.
