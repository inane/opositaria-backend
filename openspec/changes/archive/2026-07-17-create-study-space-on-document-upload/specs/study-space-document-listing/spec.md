## ADDED Requirements

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
