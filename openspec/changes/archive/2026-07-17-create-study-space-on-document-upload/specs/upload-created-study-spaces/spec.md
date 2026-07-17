## ADDED Requirements

### Requirement: Upload creates owned study space
The system SHALL create a new study space owned by the authenticated user whenever the user uploads a study document with a valid study space name.

#### Scenario: Authenticated upload creates a space
- **GIVEN** an authenticated user provides a valid PDF file and a non-blank study space name
- **WHEN** the user uploads the document
- **THEN** the system creates a study space owned by that user with the provided study space name
- **AND** the study space summary has a document count of 1

#### Scenario: Uploaded filename remains document name
- **GIVEN** an authenticated user uploads `tema-1.pdf` with study space name `Derecho Administrativo`
- **WHEN** the upload succeeds
- **THEN** the created study space is named `Derecho Administrativo`
- **AND** the created document filename is `tema-1.pdf`

#### Scenario: Blank study space name is rejected
- **GIVEN** an authenticated user provides a valid PDF file and a blank study space name
- **WHEN** the user uploads the document
- **THEN** the system rejects the upload with a validation error
- **AND** no study space, document, or processing job is persisted

#### Scenario: Upload without authentication is rejected
- **GIVEN** a request without a valid bearer token
- **WHEN** the request uploads a document with a study space name
- **THEN** the system rejects the request as unauthorized
- **AND** no study space, document, or processing job is persisted

### Requirement: Uploaded document is owned and assigned to the created space
The system SHALL persist each newly ingested document with the authenticated user's identifier and the identifier of the study space created by the same upload.

#### Scenario: Successful upload creates non-orphaned document
- **GIVEN** an authenticated user provides a valid PDF file and a valid study space name
- **WHEN** the upload succeeds
- **THEN** the persisted document has `owner_user_id` equal to the authenticated user's ID
- **AND** the persisted document has `study_space_id` equal to the created study space ID

#### Scenario: Upload ownership comes from JWT
- **GIVEN** an authenticated upload request includes a valid JWT
- **WHEN** the upload succeeds
- **THEN** the created study space owner is resolved from the JWT subject/current user
- **AND** the created document owner is resolved from the JWT subject/current user
- **AND** the system does not require or trust any owner identifier from the request payload

#### Scenario: Domain rejects missing owner
- **GIVEN** document creation is attempted without an owner ID
- **WHEN** the document is created
- **THEN** the system rejects the document with a safe `missing_owner` error

#### Scenario: Domain rejects missing study space
- **GIVEN** document creation is attempted without a study space ID
- **WHEN** the document is created
- **THEN** the system rejects the document with a safe `missing_study_space` error

#### Scenario: Database prevents orphaned uploaded documents
- **GIVEN** application code attempts to persist a study document without an owner or study space
- **WHEN** the database write is flushed or committed
- **THEN** the database rejects the write through non-null and foreign-key constraints

### Requirement: Study spaces are recoverable after upload
The system SHALL include upload-created study spaces in `GET /study-spaces` responses for the authenticated owner.

#### Scenario: User lists space created by upload
- **GIVEN** an authenticated user has successfully uploaded a document with study space name `Derecho Administrativo`
- **WHEN** the user requests `GET /study-spaces`
- **THEN** the response contains a summary for `Derecho Administrativo`
- **AND** the summary includes `id`, `name`, `document_count`, and `created_at`
- **AND** `document_count` is 1

#### Scenario: Study space listing ownership comes from JWT
- **GIVEN** a request to `GET /study-spaces` includes a valid JWT
- **WHEN** the system resolves the current user from that JWT
- **THEN** the system lists only study spaces whose owner matches the resolved user ID
- **AND** the system does not accept an owner identifier from query parameters or request body

#### Scenario: User does not see another user's upload-created space
- **GIVEN** another user has uploaded a document that created a study space
- **WHEN** the authenticated user requests `GET /study-spaces`
- **THEN** the response does not contain the other user's study space
