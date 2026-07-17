## Why

Authenticated users currently cannot reliably recover their saved study spaces because uploaded documents may be persisted without ownership and study spaces do not represent the upload flow users actually perform. A document ingestion must always create an owned, non-orphaned document inside an owned study space so the user can later list spaces and interact semantically within one selected space.

## What Changes

- Change the document upload contract so the user provides a study space name together with the uploaded PDF.
- Create a new study space during document upload, using the provided study space name.
- Persist the uploaded document with both `owner_user_id` and `study_space_id`; neither may be null for newly ingested documents.
- Keep the original uploaded filename as the document filename, separate from the study space name.
- Ensure `GET /study-spaces` lists the authenticated user's study spaces as summaries with `id`, `name`, `document_count`, and `created_at`.
- Add a space-scoped document listing capability for a future detail view: `GET /study-spaces/{space_id}/documents` returns documents belonging to that owned space.
- Prepare semantic interaction to be scoped to a study space rather than all documents owned by the user.
- **BREAKING**: `POST /study-documents/upload` now requires a study space name in multipart form data.

## Capabilities

### New Capabilities

- `upload-created-study-spaces`: Uploading a document creates an owned study space and an owned document associated with that space.
- `study-space-document-listing`: Authenticated users can list documents inside one of their study spaces.
- `space-scoped-semantic-search`: Semantic search is scoped to a selected owned study space.

### Modified Capabilities

- None.

## Non-goals

- Do not support adding additional documents to an existing study space in this change.
- Do not support one document belonging to multiple study spaces.
- Do not return nested document details from `GET /study-spaces`; it remains a summary endpoint.
- Do not implement document sharing, collaborative spaces, or cross-user access.
- Do not migrate orphaned legacy documents into inferred spaces automatically without an explicit data decision.

## Impact

- Affected modules:
  - `study_documents`: upload use case, document entity/repository contracts, persistence model, migrations, HTTP upload controller.
  - `study_spaces`: study space entity/repository persistence, listing behavior, new document listing use case/controller.
  - `semantic_search`: search contract and repository filtering by study space.
  - `shared`: application factory dependency wiring and Alembic migrations.
- API impact:
  - `POST /study-documents/upload` requires `study_space_name` in addition to `file`.
  - `GET /study-spaces` returns owned study space summaries.
  - New detail endpoint for documents in a space is introduced.
  - Semantic search must accept or be exposed through a study-space-scoped route.
- Database impact:
  - `study_documents.owner_user_id` must become non-null for ingested documents.
  - `study_documents.study_space_id` must be added as a non-null association for ingested documents.
  - Foreign keys must prevent orphaned study documents and invalid space associations.
