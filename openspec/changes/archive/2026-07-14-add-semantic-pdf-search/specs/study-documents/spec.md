## ADDED Requirements

### Requirement: Upload selectable-text PDF study documents
The system SHALL allow clients to upload study documents when the uploaded file is a PDF intended for selectable-text extraction.

#### Scenario: Accepted PDF upload
- **GIVEN** a client has a valid selectable-text PDF file
- **WHEN** the client uploads the PDF as a study document
- **THEN** the system SHALL persist a new study document with `PENDING_PROCESSING` status
- **AND** the system SHALL return `202 Accepted` with the document identifier and current status

#### Scenario: Rejected non-PDF upload
- **GIVEN** a client has a file whose content type is not `application/pdf` or whose filename extension is not `.pdf`
- **WHEN** the client uploads the file as a study document
- **THEN** the system SHALL reject the upload with a validation error
- **AND** the system SHALL NOT create a study document
- **AND** the HTTP API SHALL return `422 Unprocessable Entity` for validation failures

#### Scenario: Rejected empty upload
- **GIVEN** a client has an empty PDF upload payload
- **WHEN** the client uploads the file as a study document
- **THEN** the system SHALL reject the upload with a validation error
- **AND** the system SHALL NOT create a study document
- **AND** the HTTP API SHALL return `422 Unprocessable Entity` for validation failures

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
- **THEN** the system SHALL return `FAILED` status and a safe failure reason

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
- **GIVEN** an uploaded PDF has no usable selectable text
- **WHEN** the worker attempts to process the document
- **THEN** the system SHALL mark the document as `FAILED`
- **AND** the system SHALL store a safe failure reason indicating that selectable text could not be extracted
- **AND** safe failure reasons SHALL be user-safe messages that do not expose stack traces, filesystem paths, model internals, broker connection details, or raw infrastructure exception text
- **AND** the system SHALL NOT attempt OCR
