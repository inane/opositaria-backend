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