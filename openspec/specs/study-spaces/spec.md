## ADDED Requirements — study-space-document-listing (2026-07-17)

### Requirement: User can list documents in an owned study space
The system SHALL provide a detail endpoint that lists documents belonging to a study space owned by the authenticated user.

#### Scenario: Owner lists documents inside a space
- **GIVEN** an authenticated user owns a study space containing one uploaded document
- **WHEN** the user requests `GET /study-spaces/{space_id}/documents`
- **THEN** the response contains that document
- **AND** each document summary includes `id`, `filename`, `status`, `chunks_count`, `created_at`, and `processed_at`

#### Scenario: Empty space document list is represented consistently
- **GIVEN** an authenticated user owns a study space with no associated documents due to legacy or recovery data
- **WHEN** the user requests `GET /study-spaces/{space_id}/documents`
- **THEN** the system returns an empty list

### Requirement: Document listing is restricted to the space owner
The system SHALL prevent users from listing documents in study spaces they do not own.

 #### Scenario: Space document listing ownership comes from JWT
- **GIVEN** a request to `GET /study-spaces/{space_id}/documents` includes a valid JWT
- **WHEN** the system resolves the current user from that JWT
- **THEN** the system authorizes access using the resolved user ID
- **AND** the system does not require or trust any owner identifier from the request payload

#### Scenario: Foreign user cannot list space documents
- **GIVEN** a study space belongs to another user
- **WHEN** the authenticated user requests `GET /study-spaces/{space_id}/documents`
- **THEN** the system responds as if the space was not found
- **AND** no document metadata from the foreign space is returned

#### Scenario: Missing space returns not found
- **GIVEN** no study space exists for the requested identifier
- **WHEN** an authenticated user requests `GET /study-spaces/{space_id}/documents`
- **THEN** the system returns a not found error

#### Scenario: Unauthenticated request is rejected
- **GIVEN** a request without a valid bearer token
- **WHEN** the request targets `GET /study-spaces/{space_id}/documents`
- **THEN** the system rejects the request as unauthorized

### Requirement: Study space summaries remain document-free
The system SHALL keep `GET /study-spaces` as a summary endpoint and MUST NOT include nested document details in that response.

#### Scenario: Study space list returns summaries only
- **GIVEN** an authenticated user owns a study space containing documents
- **WHEN** the user requests `GET /study-spaces`
- **THEN** each response item includes the study space summary fields
- **AND** each response item does not include a nested `documents` collection

--

## ADDED Requirements

### Requirement: Create study spaces from ready owned documents
The system SHALL allow an authenticated user to create a study space from one or more ready study documents owned by that user.

#### Scenario: Create study space from ready owned document
- **GIVEN** an authenticated user owns a study document with `READY` status
- **WHEN** the user creates a study space with a non-blank name and that document identifier
- **THEN** the system SHALL persist a study space owned by the user
- **AND** the response SHALL return `201 Created` with the study space identifier, name, document count, and creation timestamp

#### Scenario: Reject blank study space name
- **GIVEN** an authenticated user submits a blank or whitespace-only study space name
- **WHEN** the user creates a study space
- **THEN** the system SHALL reject the request with code `invalid_name`
- **AND** the HTTP API SHALL return `422 Unprocessable Entity`

#### Scenario: Reject empty document list
- **GIVEN** an authenticated user submits no document identifiers
- **WHEN** the user creates a study space
- **THEN** the system SHALL reject the request with code `empty_documents`
- **AND** the HTTP API SHALL return `422 Unprocessable Entity`

#### Scenario: Reject missing or foreign document
- **GIVEN** an authenticated user references a document that does not exist or is owned by another user
- **WHEN** the user creates a study space
- **THEN** the system SHALL reject the request with code `document_not_found`
- **AND** the HTTP API SHALL return `404 Not Found`

#### Scenario: Reject non-ready document
- **GIVEN** an authenticated user references an owned document whose status is not `READY`
- **WHEN** the user creates a study space
- **THEN** the system SHALL reject the request with code `document_not_ready`
- **AND** the HTTP API SHALL return `409 Conflict`

### Requirement: List owned study spaces
The system SHALL list only study spaces owned by the authenticated user.

#### Scenario: List study spaces for owner
- **GIVEN** an authenticated user has study spaces
- **WHEN** the user lists study spaces
- **THEN** the system SHALL return only spaces owned by that user
- **AND** the spaces SHALL be ordered newest first

#### Scenario: List study spaces for new user
- **GIVEN** an authenticated user has no study spaces
- **WHEN** the user lists study spaces
- **THEN** the system SHALL return an empty list

#### Scenario: Study space endpoints require authentication
- **GIVEN** a request has no valid bearer token
- **WHEN** the request creates or lists study spaces
- **THEN** the system SHALL reject the request with `401 Unauthorized`

### Requirement: Persist study-space document membership
The system SHALL preserve the association between a study space and the source study documents used to create it.

#### Scenario: Reload persisted study space with document identifiers
- **GIVEN** a study space was created from one or more study documents
- **WHEN** the system reloads the study space from PostgreSQL
- **THEN** the rehydrated domain object SHALL include the associated document identifiers
- **AND** the document count SHALL match the number of associated documents