# Proposed spec update: clarify space-scoped semantic search HTTP shape

This proposal does **not** modify the official spec files. It captures review findings where the implemented API shape is more precise than the current wording.

## Target file

`openspec/changes/create-study-space-on-document-upload/specs/space-scoped-semantic-search/spec.md`

## Proposed clarification

### Requirement: Semantic search validates study space ownership

Current scenario text says the system does not trust an owner identifier from the request payload. The implemented route is `GET /study-spaces/{space_id}/semantic-search` and receives the search text and limit through query parameters, not a request body.

Suggested wording:

```md
#### Scenario: Search ownership comes from JWT
- **GIVEN** a request to `GET /study-spaces/{space_id}/semantic-search` includes a valid JWT
- **WHEN** the system resolves the current user from that JWT
- **THEN** the system validates the requested study space against the resolved user ID
- **AND** the system does not require or trust any owner identifier from request body, query parameters, or path parameters other than the authenticated JWT subject/current user
```

## Rationale

- The path parameter identifies the requested study space, not the owner.
- The current implementation derives `owner_id` from the authenticated user and passes it to the semantic search use case.
- This removes ambiguity introduced by the word “payload” for a `GET` endpoint.

## No proposed behavior change

The review confirmed the spec expectation that foreign or missing spaces return not found. Implementation was adjusted to return `404` with `space_not_found` for those cases.
