## Context

The current backend has separate `study_documents`, `study_spaces`, and `semantic_search` modules. Uploading a document authenticates the user and passes `owner_user_id` into the upload use case, but the persistence model and migration still allow `owner_user_id` to be null and delete behavior can set it to null. Study spaces are persisted only as summaries (`owner_id`, `name`, `document_count`) and do not currently persist which document belongs to which space.

The product model is now explicit: after login, a user accesses study spaces; each study space is the semantic interaction boundary and is composed of documents. For this change, uploading one document creates one new study space. Adding more documents to an existing space is deliberately left for a future change.

Ownership is derived exclusively from the authenticated JWT. HTTP clients must not send `owner_id` or `owner_user_id` fields in study-space or document requests. Controllers validate the bearer token through the current user use case and pass the resolved `user.id` into application use cases.

Current intended flow:

```text
Authenticated user
  │
  ├─ POST /study-documents/upload
  │    multipart:
  │      file = original PDF
  │      study_space_name = user-visible space name
  │
  ▼
StudySpace(owner_id=user.id, name=study_space_name, document_count=1)
  │
  ▼
StudyDocument(owner_user_id=user.id, study_space_id=space.id, filename=file.filename)
  │
  ▼
DocumentProcessingJob(document_id=document.id)
```

## Goals / Non-Goals

**Goals:**

- Guarantee newly ingested study documents are never orphaned.
- Create a study space as part of the document upload transaction.
- Persist a one-space-per-document association using `study_documents.study_space_id`.
- Keep `GET /study-spaces` as a summary list for authenticated users.
- Add a dedicated endpoint for listing documents within an owned study space.
- Scope semantic search to a selected owned study space.
- Preserve hexagonal boundaries: domain rules in domain entities, orchestration in application use cases, HTTP/database details in infrastructure.

**Non-Goals:**

- Adding a document to an existing study space.
- Sharing spaces or documents across users.
- Allowing one document to belong to multiple spaces.
- Returning nested documents from `GET /study-spaces`.
- Inferring spaces for legacy orphaned documents without a data migration decision.

## Decisions

### Decision 1: Use `study_documents.study_space_id` for the one-space-per-document relationship

Add a non-null foreign key from `study_documents` to `study_spaces` for newly ingested documents.

**Rationale:** The requirement says each document belongs to one space for now. A direct FK is the simplest model that expresses this rule and supports efficient filtering by space for document listing and semantic search.

**Alternative considered: join table `study_space_documents`.** This would make future many-to-many easier, but it adds indirection and constraints not needed for the current rule. If many-to-many becomes required later, a migration can introduce the join table then.

**Alternative considered: store document IDs as JSON on `study_spaces`.** This would weaken referential integrity, complicate queries, and violate the persistence model's need to filter chunks/documents by space.

### Decision 2: Upload use case orchestrates study space creation and document creation atomically

Extend `UploadStudyDocumentUseCase` to accept `study_space_name` and a `StudySpaceRepository`. The use case creates a `StudySpace`, creates the `StudyDocument` with `owner_user_id` and `study_space_id`, creates the processing job, commits durable state, then publishes processing.

**Rationale:** The upload is the user's business action. It is the natural application boundary for creating the first space and its first document. The use case already coordinates document persistence, storage, job creation, and publication.

**Alternative considered: call `CreateStudySpaceUseCase` from upload.** Use cases must not call other use cases. Cross-module communication should use domain entities and repository ports, preserving the dependency rule.

**Alternative considered: create the space in the controller.** Controllers are infrastructure adapters and must not contain business orchestration.

### Decision 3: Keep domain ownership rules strict

`StudyDocument.create` must require `owner_user_id` and `study_space_id`. `StudySpace.create` continues to require an owner, non-blank name, and at least one document ID. The upload use case can create the space with the generated document ID so the space's `document_count` starts at 1.

**Rationale:** The business invariant belongs in the domain: ingested documents cannot be ownerless or spaceless.

**Alternative considered: validate only at database level.** Database constraints are necessary but insufficient; application and domain tests should catch violations before persistence.

### Decision 3b: Derive ownership from the JWT, never from request payloads

For `GET /study-spaces`, `POST /study-documents/upload`, `GET /study-spaces/{space_id}/documents`, and space-scoped semantic search, the controller obtains the bearer token, resolves the current user, and passes `user.id` as the owner identifier to the use case. Request bodies and query parameters must not be trusted as ownership sources.

**Rationale:** The frontend already sends the JWT. Extracting ownership server-side prevents spoofing, keeps authorization centralized, and matches the existing controller pattern.

**Alternative considered: accept `owner_id` from the frontend.** This is insecure because a client could request or create resources for another user.

### Decision 4: Preserve summary and detail endpoints separately

`GET /study-spaces` returns only summaries. Add `GET /study-spaces/{space_id}/documents` for the space detail view.

**Rationale:** The frontend needs a lightweight list after login, while documents belong in the space detail view. This avoids over-fetching and keeps response models clear.

**Alternative considered: embed documents in `GET /study-spaces`.** This would complicate pagination and response size later, and it contradicts the selected product direction.

### Decision 5: Expose semantic search through a space-scoped contract

Semantic search must require an owned `study_space_id` and search only READY documents in that space. The preferred HTTP shape is `POST /study-spaces/{space_id}/semantic-search`, delegating to the semantic search use case with both `owner_id` and `study_space_id`.

**Rationale:** Users semantically interact inside a study space, not globally across all owned documents. The URL expresses the aggregate boundary clearly.

**Alternative considered: keep `/semantic-search/search` with an optional `study_space_id` query parameter.** Optional parameters preserve compatibility but allow ambiguous global searches. A space-scoped route better reflects the business rule.

### Decision 6: Enforce persistence constraints with Alembic migrations

Add `study_space_id` to `study_documents`, enforce non-null for new ingested documents, update `owner_user_id` to non-null, and change FK delete behavior away from `SET NULL` for ownership. The deployment must account for existing rows before making constraints strict.

**Rationale:** The database must protect invariants even if a future code path bypasses the domain.

**Alternative considered: leave nullable columns and rely on code.** This is the source of the current orphan bug and is not acceptable for ownership-sensitive data.

## Hexagonal Layer Mapping

### `study_documents` module

- **Domain**
  - `StudyDocument` requires `owner_user_id` and `study_space_id` at creation.
  - `StudyDocumentRepository` exposes owner- and space-aware query methods as needed by use cases.
- **Application**
  - `UploadStudyDocumentUseCase` orchestrates creation of a space, document, processing job, storage, and publication.
  - Upload DTOs include the document ID, status, and created study space ID if useful to the client.
- **Infrastructure**
  - HTTP controller reads `study_space_name` from multipart form data.
  - PostgreSQL repository persists and maps `study_space_id`.
  - Alembic migration updates schema and constraints.

### `study_spaces` module

- **Domain**
  - `StudySpace` remains the aggregate for an owned named semantic boundary.
  - Repository port adds methods needed to verify ownership and list space documents through application use cases, or collaborates with `StudyDocumentRepository` for document listing.
- **Application**
  - `ListStudySpacesUseCase` remains responsible for summaries.
  - Add `ListStudySpaceDocumentsUseCase` to retrieve documents for one owned space.
- **Infrastructure**
  - HTTP controller adds `GET /study-spaces/{space_id}/documents`.
  - HTTP controller extracts ownership from the authenticated JWT and never from request payloads.
  - PostgreSQL adapter maps persisted spaces and queries document counts accurately.

### `semantic_search` module

- **Domain/Application**
  - Search use case accepts `study_space_id` and `owner_id`.
  - Repository port supports nearest-chunk lookup by owner and study space.
- **Infrastructure**
  - Search SQL joins chunks to documents and filters by `owner_user_id`, `study_space_id`, and `READY` status.
  - HTTP route is exposed under a space-scoped path or accepts a mandatory space identifier.

### `shared` module

- **Infrastructure**
  - Factory wiring provides `StudySpaceRepository` to upload and document listing use cases.
  - Migrations live under shared infrastructure migrations.

## Risks / Trade-offs

- Existing orphaned documents may block strict NOT NULL migrations → Add an explicit migration strategy: fail fast with a clear data cleanup requirement or quarantine legacy rows before constraints are applied.
- Creating a space before storing the file can leave an empty space if storage fails → Orchestrate storage before final commit and keep all database writes in one transaction; do not commit the space/document/job until storage path is known.
- Publishing after commit can fail and leave a pending document without a queued job → Preserve current durable-before-publish behavior, and rely on job persistence/retry mechanisms rather than rolling back committed data after publication errors.
- Direct `study_space_id` FK may require migration work if many-to-many is needed later → Accept the trade-off because the current business rule is one document per space.
- Space `document_count` can drift if denormalized → For this change, creating one document with one space keeps it simple; future add-document behavior should update count transactionally or compute count from documents.
- Space-scoped search changes clients that call global search → Mark as API contract change and update E2E tests to encode the new space boundary.

## Migration Plan

1. Add nullable `study_space_id` column and FK to `study_documents` in an Alembic migration.
2. Decide how to handle existing rows before enforcing non-null:
   - preferred for production safety: migration detects orphaned or spaceless rows and aborts with an actionable message;
   - local/dev alternative: allow a one-time cleanup script outside the migration.
3. Backfill or remove invalid local data as an operational step.
4. Alter `study_documents.owner_user_id` and `study_documents.study_space_id` to non-null.
5. Replace `owner_user_id` FK `ON DELETE SET NULL` with behavior that cannot create orphaned documents, preferably cascade delete or restrict according to user deletion policy.
6. Deploy application code that writes both owner and space associations before enforcing constraints in environments with existing valid data, or deploy migration and code together in non-production.

Rollback strategy:

- Roll back application code to the previous upload contract only if the migration has not made columns non-null.
- Once non-null constraints are applied, rollback requires preserving `study_space_id` data or a dedicated reverse migration that accepts potential loss of the new association.

## Open Questions

- Should deleting a user cascade delete their study spaces and documents, or should deletion be restricted while owned study data exists?
- Should upload response include the created `study_space_id` so the frontend can navigate directly to the new space?
- Should semantic search replace the current `/semantic-search/search` route, or should the old route remain temporarily deprecated for compatibility?
