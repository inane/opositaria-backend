## ADDED Requirements

### Requirement: Upload selectable-text PDF study documents
The system SHALL allow clients to upload study documents when the uploaded file is a PDF intended for selectable-text extraction and satisfies upload validation constraints (file type, size, and filename safety).

#### Scenario: Accepted PDF upload
- **GIVEN** a client has a valid selectable-text PDF file no larger than 50 MB whose filename is safe
- **WHEN** the client uploads the PDF as a study document
- **THEN** the system SHALL persist a new study document with `PENDING_PROCESSING` status
- **AND** the system SHALL return `202 Accepted` with the document identifier and current status
- **AND** the system SHALL save the uploaded file to durable storage
- **AND** the system SHALL create a processing job record and publish a processing message

#### Scenario: Rejected non-PDF upload
- **GIVEN** a client has a file whose content type is not `application/pdf` or whose filename extension is not `.pdf`
- **WHEN** the client uploads the file as a study document
- **THEN** the system SHALL reject the upload with code `invalid_file_type`
- **AND** the structured error SHALL include a stable `code` field and user-safe `message` field
- **AND** the system SHALL NOT create a study document or processing job
- **AND** the structured error SHALL NOT expose stack traces, filesystem paths, or raw exception text
- **AND** the HTTP API SHALL return `422 Unprocessable Entity`

#### Scenario: Rejected empty upload
- **GIVEN** a client has an empty PDF upload payload
- **WHEN** the client uploads the file as a study document
- **THEN** the system SHALL reject the upload with code `empty_upload`
- **AND** the structured error SHALL include a stable `code` field and user-safe `message` field
- **AND** the system SHALL NOT create a study document or processing job
- **AND** the HTTP API SHALL return `422 Unprocessable Entity`

#### Scenario: Rejected oversized upload
- **GIVEN** a client has a PDF upload payload larger than 50 MB
- **WHEN** the client uploads the file as a study document
- **THEN** the system SHALL reject the upload with code `file_too_large`
- **AND** the structured error SHALL include a stable `code` field and user-safe `message` field
- **AND** the system SHALL NOT create a study document or processing job
- **AND** the HTTP API SHALL return `413 Payload Too Large`

#### Scenario: Rejected unsafe filename
- **GIVEN** a client has a PDF upload whose filename is blank, `.`, `..`, contains path separators (`/` or `\\`), contains control characters, or exceeds the maximum filename length
- **WHEN** the client uploads the file as a study document
- **THEN** the system SHALL reject the upload with code `invalid_filename`
- **AND** the structured error SHALL include a stable `code` field and user-safe `message` field
- **AND** the system SHALL NOT create a study document or processing job
- **AND** the HTTP API SHALL return `422 Unprocessable Entity`

#### Scenario: Upload at maximum allowed size
- **GIVEN** a client has a valid selectable-text PDF upload at exactly the 50 MB limit
- **WHEN** the client uploads the PDF as a study document
- **THEN** the system SHALL accept the upload and proceed normally

### Requirement: Return structured upload errors
The system SHALL return stable structured error payloads for study document upload validation failures.

#### Scenario: Upload validation response shape
- **GIVEN** a study document upload fails validation
- **WHEN** the HTTP API returns the error response
- **THEN** the response body SHALL include a stable `code` field
- **AND** the response body SHALL include a user-safe `message` field
- **AND** the response body SHALL NOT expose stack traces, filesystem paths, storage paths, framework exception text, or raw infrastructure exception text

#### Scenario: Frontend can branch by upload error code
- **GIVEN** a frontend receives an upload validation error
- **WHEN** the frontend reads the response body
- **THEN** the frontend SHALL be able to determine the failure category from the stable `code` field without parsing the human-readable message

### Requirement: Preserve safe uploaded filename metadata
The system SHALL preserve valid uploaded filenames as metadata and SHALL NOT rely on user-controlled filenames for storage paths.

#### Scenario: Valid filename is preserved as metadata
- **GIVEN** a client uploads a valid PDF with a safe filename
- **WHEN** the system persists the study document
- **THEN** the system SHALL store the original filename as document metadata
- **AND** the storage path SHALL be generated independently from unsafe user-controlled path components

#### Scenario: Filename length limit is enforced
- **GIVEN** a client uploads a PDF whose filename exceeds the configured maximum filename length
- **WHEN** the client uploads the file as a study document
- **THEN** the system SHALL reject the upload with code `invalid_filename`
- **AND** the system SHALL NOT create a study document

### Requirement: Persist document lifecycle state
The system SHALL expose the stable lifecycle state of each uploaded study document from PostgreSQL.

#### Scenario: Retrieve pending document status
- **GIVEN** a study document was uploaded successfully
- **WHEN** a client asks for the document status before processing starts
- **THEN** the system SHALL return the document identifier, filename, and `PENDING_PROCESSING` status

#### Scenario: Retrieve processing document status
- **GIVEN** a worker has claimed a document for processing
- **WHEN** a client asks for the document status
- **THEN** the system SHALL return `PROCESSING` status for that document

#### Scenario: Retrieve ready document status
- **GIVEN** a document has been processed successfully
- **WHEN** a client asks for the document status
- **THEN** the system SHALL return `READY` status and the number of persisted chunks

#### Scenario: Retrieve failed document status
- **GIVEN** a document failed during processing
- **WHEN** a client asks for the document status
- **THEN** the system SHALL return `FAILED` status and the classified safe failure reason

#### Scenario: Missing document status
- **GIVEN** no study document exists for the requested identifier
- **WHEN** a client asks for the document status
- **THEN** the system SHALL return a not found error

### Requirement: Store chunks for processed study documents
The system SHALL persist extracted study document chunks with their parent document reference, sequence, optional page number, text, embedding vector, and embedding model metadata.

#### Scenario: Store chunks after successful processing
- **GIVEN** a selectable-text PDF contains extractable study content
- **WHEN** the document processing worker completes extraction, chunking, and embedding generation
- **THEN** the system SHALL persist one or more chunks for the document
- **AND** each chunk SHALL include text, sequence number, embedding vector, and embedding model metadata

#### Scenario: Preserve chunk order
- **GIVEN** a processed document produced multiple chunks
- **WHEN** the chunks are stored
- **THEN** the system SHALL store sequence numbers that preserve the processing order

#### Scenario: Replace chunks during reprocessing
- **GIVEN** a document already has persisted chunks
- **WHEN** the system reprocesses the document
- **THEN** the system SHALL replace the previous chunks with the newly generated chunks atomically

### Requirement: Exclude scanned PDFs from the MVP
The system SHALL fail processing for PDFs that do not yield usable selectable text.

#### Scenario: Uploaded PDF has no extractable text
- **GIVEN** an uploaded PDF has no usable selectable text (scanned, image-only, or blank PDF)
- **WHEN** the worker attempts to process the document
- **THEN** the system SHALL mark the document as `FAILED`
- **AND** the system SHALL store a safe failure reason associated with code `no_extractable_text`
- **AND** safe failure reasons SHALL be user-safe messages that do not expose stack traces, filesystem paths, model internals, broker connection details, or raw infrastructure exception text
- **AND** the system SHALL NOT attempt OCR
