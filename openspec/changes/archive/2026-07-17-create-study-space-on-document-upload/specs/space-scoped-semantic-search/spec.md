## ADDED Requirements

### Requirement: Semantic search runs within an owned study space
The system SHALL execute semantic search only against READY documents that belong to the requested study space and are owned by the authenticated user.

#### Scenario: Search returns chunks from selected space
- **GIVEN** an authenticated user owns two study spaces with READY documents
- **AND** both spaces contain chunks relevant to the query
- **WHEN** the user searches within the first study space
- **THEN** the response contains matches only from documents assigned to the first study space
- **AND** no matches from the second study space are returned

#### Scenario: Search ignores processing documents in selected space
- **GIVEN** an authenticated user owns a study space with one READY document and one PROCESSING document
- **WHEN** the user searches within that study space
- **THEN** the response contains matches only from READY documents

#### Scenario: Search in empty ready set returns no results
- **GIVEN** an authenticated user owns a study space without READY documents
- **WHEN** the user searches within that study space
- **THEN** the system returns a successful response with an empty results list

### Requirement: Semantic search validates study space ownership
The system SHALL verify that the requested study space belongs to the authenticated user before returning semantic search results.

#### Scenario: Search ownership comes from JWT
- **GIVEN** a space-scoped semantic search request includes a valid JWT
- **WHEN** the system resolves the current user from that JWT
- **THEN** the system validates the requested study space against the resolved user ID
- **AND** the system does not require or trust any owner identifier from the request payload

#### Scenario: Foreign space search is hidden
- **GIVEN** a study space belongs to another user
- **WHEN** the authenticated user searches within that study space ID
- **THEN** the system responds as if the study space was not found
- **AND** no semantic results are returned

#### Scenario: Missing space search returns not found
- **GIVEN** no study space exists for the requested identifier
- **WHEN** an authenticated user searches within that study space ID
- **THEN** the system returns a not found error

#### Scenario: Unauthenticated search is rejected
- **GIVEN** a request without a valid bearer token
- **WHEN** the request searches within a study space
- **THEN** the system rejects the request as unauthorized

### Requirement: Search input validation remains enforced
The system SHALL validate semantic search query text and result limits for space-scoped searches.

#### Scenario: Blank query is rejected
- **GIVEN** an authenticated user owns a study space
- **WHEN** the user searches within that space using a blank query
- **THEN** the system rejects the request with a validation error

#### Scenario: Invalid limit is rejected
- **GIVEN** an authenticated user owns a study space
- **WHEN** the user searches within that space using a limit outside the accepted range
- **THEN** the system rejects the request with a validation error
