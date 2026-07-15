## ADDED Requirements

### Requirement: Publish processing work for uploaded documents
The system SHALL enqueue asynchronous processing work in RabbitMQ after a PDF study document is persisted.

#### Scenario: Publish processing message after upload
- **GIVEN** a study document has been persisted with `PENDING_PROCESSING` status
- **WHEN** the upload use case completes document persistence
- **THEN** the system SHALL create a processing job in PostgreSQL
- **AND** the system SHALL publish a RabbitMQ message containing the document identifier and job identifier

#### Scenario: Publishing fails after document persistence
- **GIVEN** a study document and processing job have been persisted
- **WHEN** RabbitMQ publishing fails
- **THEN** the system SHALL keep the document and job in a recoverable pending state
- **AND** the system SHALL return a safe error or recovery response without losing the document record
- **AND** the persisted study document and processing job SHALL be durably committed, or otherwise recoverable through a transactional outbox, before RabbitMQ publishing can cause the upload transaction to roll back

### Requirement: Process document jobs asynchronously
The system SHALL process RabbitMQ document processing messages through a worker process.

#### Scenario: Worker processes a pending job
- **GIVEN** RabbitMQ contains a message for a pending document processing job
- **WHEN** the worker consumes the message
- **THEN** the system SHALL mark the processing job as `RUNNING`
- **AND** the system SHALL mark the study document as `PROCESSING`
- **AND** the system SHALL extract text, chunk text, generate embeddings, persist chunks, and mark the document `READY`

#### Scenario: Worker completes a job
- **GIVEN** a worker successfully stores all chunks and embeddings for a document
- **WHEN** the processing transaction completes
- **THEN** the system SHALL mark the processing job as completed
- **AND** the system SHALL mark the document as `READY`
- **AND** the worker SHALL commit document, job, and chunk state before acknowledging the RabbitMQ message

#### Scenario: Worker fails a job safely
- **GIVEN** a worker cannot complete PDF extraction, chunking, embedding generation, or chunk persistence
- **WHEN** the failure is handled
- **THEN** the system SHALL mark the processing job as failed
- **AND** the system SHALL mark the document as `FAILED`
- **AND** the system SHALL store a safe failure reason associated with a stable failure code when the failure category is known
- **AND** safe failure reasons SHALL be user-safe messages that do not expose stack traces, filesystem paths, model internals, broker connection details, or raw infrastructure exception text
- **AND** the worker SHALL commit the failed document and job state before acknowledging or rejecting the RabbitMQ message

#### Scenario: Duplicate processing message
- **GIVEN** RabbitMQ delivers the same processing message more than once
- **WHEN** the worker receives a message for a job that is already completed
- **THEN** the system SHALL avoid duplicating chunks
- **AND** the system SHALL leave the ready document status and existing chunks unchanged when acknowledging a duplicate completed job message

### Requirement: Keep PostgreSQL as canonical processing state
The system SHALL store stable document and processing job state in PostgreSQL, not Redis.

#### Scenario: State survives broker restart
- **GIVEN** a document and processing job were persisted in PostgreSQL
- **WHEN** RabbitMQ restarts
- **THEN** the system SHALL retain the document and job state in PostgreSQL
- **AND** repository-backed document and job state SHALL be recoverable independently of RabbitMQ queue contents

#### Scenario: Redis is not required for processing state
- **GIVEN** the document processing flow is running
- **WHEN** the system updates document or job lifecycle state
- **THEN** the system SHALL write canonical state to PostgreSQL
- **AND** the system SHALL NOT require Redis to determine document readiness or failure

### Requirement: Generate embeddings locally
The system SHALL generate document chunk embeddings through a local embedding adapter behind an application port.

#### Scenario: Generate embeddings without cloud runtime dependency
- **GIVEN** the worker has extracted text chunks from a PDF
- **WHEN** it generates embeddings for the chunks
- **THEN** the system SHALL use a local embedding adapter
- **AND** the system SHALL NOT require an external cloud embedding API at runtime
- **AND** local development and test environments MAY use a deterministic local embedding adapter when it satisfies the configured embedding dimension and does not require external cloud APIs

#### Scenario: Reject invalid embedding dimensions
- **GIVEN** the local embedding adapter returns a vector whose dimension does not match configured storage dimension
- **WHEN** the worker validates the embedding
- **THEN** the system SHALL fail processing safely
- **AND** the system SHALL NOT persist invalid chunk embeddings

### Requirement: Use selectable-text PDF extraction only
The system SHALL extract text from PDFs that contain selectable text and SHALL NOT perform OCR.

#### Scenario: Extract text from selectable PDF
- **GIVEN** a PDF contains selectable text
- **WHEN** the worker extracts text
- **THEN** the system SHALL produce normalized text for chunking

#### Scenario: Do not perform OCR
- **GIVEN** a PDF page contains only scanned image content
- **WHEN** the worker extracts text
- **THEN** the system SHALL treat the page as having no extractable text
- **AND** the system SHALL classify the failure as `no_extractable_text`
- **AND** the system SHALL NOT invoke OCR

### Requirement: Classify PDF extraction failures safely
The system SHALL classify known PDF extraction failures into stable, safe failure categories.

#### Scenario: Unreadable PDF fails with safe reason
- **GIVEN** a persisted study document points to a PDF file that cannot be read by the PDF extraction adapter
- **WHEN** the worker processes the document
- **THEN** the system SHALL mark the document as `FAILED`
- **AND** the system SHALL mark the processing job as failed
- **AND** the system SHALL store a safe failure reason associated with code `pdf_cannot_be_read`
- **AND** the system SHALL NOT persist document chunks for that document
- **AND** the safe failure reason SHALL NOT expose raw parser errors, stack traces, filesystem paths, or library internals

#### Scenario: Encrypted PDF fails with safe reason
- **GIVEN** a persisted study document points to an encrypted or password-protected PDF
- **WHEN** the worker processes the document
- **THEN** the system SHALL mark the document as `FAILED`
- **AND** the system SHALL mark the processing job as failed
- **AND** the system SHALL store a safe failure reason associated with code `encrypted_pdf`
- **AND** the system SHALL NOT persist document chunks for that document
- **AND** the safe failure reason SHALL NOT expose raw parser errors, stack traces, filesystem paths, or library internals

#### Scenario: Selectable text cannot be extracted
- **GIVEN** a persisted study document points to a PDF with no usable selectable text
- **WHEN** the worker processes the document
- **THEN** the system SHALL mark the document as `FAILED`
- **AND** the system SHALL mark the processing job as failed
- **AND** the system SHALL store a safe failure reason associated with code `no_extractable_text`
- **AND** the system SHALL NOT persist document chunks for that document
- **AND** the system SHALL NOT attempt OCR

#### Scenario: Unknown processing failure remains safe
- **GIVEN** document processing fails for an unexpected technical reason
- **WHEN** the worker handles the failure
- **THEN** the system SHALL mark the document as `FAILED`
- **AND** the system SHALL mark the processing job as failed
- **AND** the system SHALL store a generic safe failure reason
- **AND** the generic safe failure reason SHALL NOT expose raw exception text or infrastructure details
