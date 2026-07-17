## ADDED Requirements — space-scoped-semantic-search (2026-07-17)

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
- **GIVEN** a request to `GET /study-spaces/{space_id}/semantic-search` includes a valid JWT
- **WHEN** the system resolves the current user from that JWT
- **THEN** the system validates the requested study space against the resolved user ID
- **AND** the system does not require or trust any owner identifier from request body, query parameters, or path parameters other than the authenticated JWT subject/current user

#### Scenario: Foreign space search is hidden
- **GIVEN** a study space belongs to another user
- **WHEN** the authenticated user searches within that study space ID
- **THEN** the system responds as if the study space was not found (HTTP 404)
- **AND** no semantic results are returned

#### Scenario: Missing space search returns not found
- **GIVEN** no study space exists for the requested identifier
- **WHEN** an authenticated user searches within that study space ID
- **THEN** the system returns a not found error (HTTP 404)

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

---

## ADDED Requirements

### Requirement: Search processed study documents semantically
The system SHALL allow clients to search ready study document chunks by semantic similarity to a query.

#### Scenario: Search ready document chunks
- **GIVEN** one or more study documents are `READY` and have persisted chunk embeddings
- **WHEN** a client submits a semantic search query
- **THEN** the system SHALL generate a local embedding for the query
- **AND** the system SHALL return chunks ordered by cosine similarity
- **AND** the similarity score SHALL be a normalized similarity value where higher scores represent more similar chunks

#### Scenario: Ignore unprocessed documents
- **GIVEN** some study documents are `PENDING_PROCESSING`, `PROCESSING`, or `FAILED`
- **WHEN** a client submits a semantic search query
- **THEN** the system SHALL NOT return chunks from those documents
- **AND** the system SHALL return only chunks whose parent document status is exactly `READY`

#### Scenario: Empty query is rejected
- **GIVEN** a client submits an empty or blank semantic search query
- **WHEN** the semantic search request is validated
- **THEN** the system SHALL reject the request with a validation error

#### Scenario: No matching chunks exist
- **GIVEN** no ready document chunks are available for semantic search
- **WHEN** a client submits a valid semantic search query
- **THEN** the system SHALL return an empty results list

### Requirement: Return chunks and parent documents
The system SHALL return semantic search results containing matched chunk details and parent study document metadata.

#### Scenario: Result includes chunk and document metadata
- **GIVEN** a semantic search query matches a stored document chunk
- **WHEN** the system returns the result
- **THEN** the result SHALL include the chunk identifier, chunk text, similarity score, sequence number, optional page number, parent document identifier, and parent document filename

#### Scenario: Multiple chunks from one document
- **GIVEN** a semantic search query matches multiple chunks from the same document
- **WHEN** the system returns the results
- **THEN** each matching chunk SHALL include its parent document metadata
- **AND** the system SHALL preserve similarity ordering across all returned chunks

### Requirement: Limit semantic search result count
The system SHALL enforce a result limit for semantic search requests.

#### Scenario: Client provides valid limit
- **GIVEN** a client submits a semantic search query with a valid result limit
- **WHEN** the system searches matching chunks
- **THEN** the system SHALL return no more than the requested number of results

#### Scenario: Client omits limit
- **GIVEN** a client submits a semantic search query without a result limit
- **WHEN** the system searches matching chunks
- **THEN** the system SHALL apply the default result limit

#### Scenario: Client provides invalid limit
- **GIVEN** a client submits a semantic search query with a limit below the minimum or above the maximum
- **WHEN** the semantic search request is validated
- **THEN** the system SHALL reject the request with a validation error

### Requirement: Use pgvector cosine similarity
The system SHALL use pgvector cosine similarity for semantic chunk retrieval.

#### Scenario: Retrieve nearest chunks by cosine distance
- **GIVEN** ready document chunks have persisted embeddings
- **WHEN** the semantic search adapter queries PostgreSQL
- **THEN** the system SHALL order results by cosine distance between the query embedding and chunk embeddings

#### Scenario: Vector index exists for chunk search
- **GIVEN** database migrations have been applied
- **WHEN** the system stores and searches document chunk embeddings
- **THEN** PostgreSQL SHALL have a pgvector index suitable for cosine similarity search over chunk embeddings

### Requirement: Fail safely when query embedding generation fails
The system SHALL return a safe error when semantic search cannot generate a query embedding.

#### Scenario: Local embedding adapter fails during search
- **GIVEN** a client submits a valid semantic search query
- **WHEN** the local embedding adapter fails to generate a query embedding
- **THEN** the system SHALL return a safe service error
- **AND** the system SHALL NOT expose internal stack traces, model paths, or provider details
- **AND** the HTTP API SHALL map query embedding generation failures to a safe `5xx` service error response without exposing stack traces, model paths, or provider details

### Requirement: Scope semantic search to authenticated owner
The system SHALL return semantic search results only from documents owned by the authenticated user.

#### Scenario: Search excludes foreign ready documents
- **GIVEN** ready study documents with chunk embeddings exist for multiple users
- **WHEN** an authenticated user submits a semantic search query
- **THEN** the system SHALL return only chunks whose parent document is owned by that user
- **AND** the system SHALL NOT return chunks from another user's ready documents

#### Scenario: Semantic search requires authentication
- **GIVEN** a request has no valid bearer token
- **WHEN** the request submits a semantic search query
- **THEN** the system SHALL reject the request with `401 Unauthorized`
