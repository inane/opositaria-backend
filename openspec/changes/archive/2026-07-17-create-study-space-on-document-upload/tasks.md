## 1. Domain Model Invariants

- [x] 1.1 RED write a `StudyDocument` domain unit test proving creation without `owner_user_id` fails with safe code `missing_owner` → GREEN ensure existing behavior passes → COMMIT `test: cover missing document owner invariant` → REFACTOR names and fixtures.
- [x] 1.2 RED write a `StudyDocument` domain unit test proving creation without `study_space_id` fails with safe code `missing_study_space` → GREEN add required `study_space_id` field and validation to `StudyDocument` → COMMIT `feat: require study space for study documents` → REFACTOR constructor/factory clarity.
- [x] 1.3 RED update `StudyDocument` domain unit tests proving valid documents expose both `owner_user_id` and `study_space_id` → GREEN adjust test builders and entity creation → COMMIT `test: cover owned spaced study documents` → REFACTOR duplicate document factory setup.
- [x] 1.4 RED write or update `StudySpace` domain unit tests proving a newly created space with one document has `document_count` 1 → GREEN keep or adjust `StudySpace.create` behavior → COMMIT `test: cover single document study space count` → REFACTOR naming.
- [x] 1.5 RED update all existing domain/unit test data builders that create `StudyDocument` without `study_space_id` → GREEN provide explicit IDs in test setup → COMMIT `test: update study document fixtures for spaces` → REFACTOR shared helpers only after duplication appears.

## 2. Repository Ports and InMemory Implementations

- [x] 2.1 RED write an InMemory `StudyDocumentRepository` unit test proving `find_by_study_space_id_and_owner` returns only documents for the requested space and owner → GREEN add the repository port method and InMemory implementation → COMMIT `feat: add study document lookup by space and owner` → REFACTOR method names for intention.
- [x] 2.2 RED write an InMemory `StudySpaceRepository` unit test proving `find_by_id_and_owner` returns an owned space and hides foreign spaces → GREEN add the repository port method and InMemory implementation → COMMIT `feat: add owned study space lookup` → REFACTOR duplicated ownership checks.
- [x] 2.3 RED update repository protocol type checks/usages to require `study_space_id` when saving documents → GREEN adjust signatures and entity mapping references → COMMIT `refactor: align repository ports with study spaces` → REFACTOR imports and typing.

## 3. Upload Application Use Case

- [x] 3.1 RED write an `UploadStudyDocumentUseCase` unit test proving a valid upload creates a study space with the provided name → GREEN inject `StudySpaceRepository` and create the space in the use case → COMMIT `feat: create study space during upload` → REFACTOR arrange helpers.
- [x] 3.2 RED write an upload use case unit test proving the created document has the authenticated owner ID and created study space ID → GREEN pass both IDs into `StudyDocument.create` → COMMIT `feat: associate uploaded document to created space` → REFACTOR variable names.
- [x] 3.3 RED write an upload use case unit test proving the original filename remains the document filename and not the study space name → GREEN preserve filename assignment → COMMIT `test: preserve uploaded filename separately from space name` → REFACTOR assertion readability.
- [x] 3.4 RED write an upload use case unit test proving blank `study_space_name` fails and persists no space, document, or job → GREEN validate via `StudySpace.create` before durable writes and avoid partial persistence → COMMIT `feat: reject blank upload study space names` → REFACTOR transaction ordering comments.
- [x] 3.5 RED write an upload use case unit test proving invalid file type still fails without persisting a space → GREEN ensure document validation happens before saving the space or before commit → COMMIT `fix: avoid spaces for invalid uploads` → REFACTOR setup.
- [x] 3.6 RED write an upload use case unit test proving upload response includes the created `study_space_id` if client navigation needs it → GREEN extend DTO response and use case return value → COMMIT `feat: return created study space from upload` → REFACTOR DTO naming.
- [x] 3.7 RED update existing upload use case tests to pass `study_space_name` and `StudySpaceRepository` → GREEN update all fixtures and stubs → COMMIT `test: update upload tests for space creation` → REFACTOR repeated use case construction.

## 4. Study Space Listing Application Use Cases

- [x] 4.1 RED write a `ListStudySpacesUseCase` unit test proving upload-created spaces are returned newest-first as summaries with `document_count` → GREEN keep or adjust summary mapping → COMMIT `test: cover upload-created space summaries` → REFACTOR test builders.
- [x] 4.2 RED write a `ListStudySpaceDocumentsUseCase` unit test proving an owner can list documents for one owned space → GREEN implement the use case using owned space lookup and document lookup by space/owner → COMMIT `feat: list documents in owned study space` → REFACTOR response mapping.
- [x] 4.3 RED write a `ListStudySpaceDocumentsUseCase` unit test proving foreign spaces are hidden as not found → GREEN raise a safe `StudySpaceError` with `space_not_found` or equivalent → COMMIT `feat: hide foreign study space documents` → REFACTOR error factory/naming.
- [x] 4.4 RED write a `ListStudySpaceDocumentsUseCase` unit test proving missing spaces return not found → GREEN use the same safe error path → COMMIT `test: cover missing study space document listing` → REFACTOR duplication with foreign-space case.
- [x] 4.5 RED write a `ListStudySpaceDocumentsUseCase` unit test proving legacy empty spaces return an empty document list → GREEN return an empty list when owned space exists without documents → COMMIT `feat: allow empty owned space document listing` → REFACTOR DTO helpers.

## 5. Semantic Search Application Behavior

- [x] 5.1 RED write a `SemanticSearchUseCase` unit test proving search receives both `owner_id` and `study_space_id` → GREEN extend use case signature and repository port call → COMMIT `feat: scope semantic search to study space` → REFACTOR type conversions.
- [x] 5.2 RED write a semantic search use case unit test proving missing or foreign study space is rejected before chunk search → GREEN inject `StudySpaceRepository` or ownership-verification port and enforce ownership → COMMIT `feat: validate space ownership before semantic search` → REFACTOR error naming.
- [x] 5.3 RED write a semantic search use case unit test proving blank queries remain rejected → GREEN preserve existing query validation → COMMIT `test: preserve space scoped search query validation` → REFACTOR assertion clarity.
- [x] 5.4 RED write a semantic search use case unit test proving invalid limits remain rejected → GREEN preserve limit validation → COMMIT `test: preserve space scoped search limit validation` → REFACTOR shared setup.

## 6. Database Models and Migrations

- [x] 6.1 Create an Alembic migration adding `study_documents.study_space_id` with a foreign key to `study_spaces.id`.
- [x] 6.2 Create migration logic or a precondition that prevents applying strict constraints while legacy documents have null `owner_user_id` or null `study_space_id`.
- [x] 6.5 Replace the `owner_user_id` foreign key behavior that can set ownership to null with delete behavior that cannot create orphaned documents.
- [x] 6.6 Update SQLAlchemy `StudyDocumentModel` to include non-null `study_space_id` and non-null `owner_user_id` mappings.
- [x] 6.7 Update SQLAlchemy relationships between `StudySpaceModel` and `StudyDocumentModel` if useful without violating module boundaries.
- [x] 6.8 RED write PostgreSQL repository integration test proving saving and loading a document preserves `study_space_id` → GREEN update `PostgresStudyDocumentRepository.save` and mapping → COMMIT `feat: persist study document study space` → REFACTOR SQL mapping helpers.
- [x] 6.9 RED write PostgreSQL repository integration test proving database rejects null `owner_user_id` and null `study_space_id` → GREEN ensure migration/model constraints enforce this → COMMIT `feat: enforce non orphaned study documents` → REFACTOR integration setup.
- [x] 6.10 RED write PostgreSQL repository integration test proving `find_by_study_space_id_and_owner` excludes foreign documents and other spaces → GREEN implement SQL query → COMMIT `feat: query study documents by owned space` → REFACTOR domain mapping duplication.
- [x] 6.11 RED write PostgreSQL study space repository integration test proving `find_by_id_and_owner` hides foreign spaces → GREEN implement SQL query → COMMIT `feat: query owned study spaces` → REFACTOR repository mapping.

## 7. HTTP API and Factory Wiring

- [x] 7.1 RED write E2E test proving `POST /study-documents/upload` with `file` and `study_space_name` returns 202 and creates a listable study space → GREEN read `study_space_name` from multipart form data and wire repositories → COMMIT `feat: create listable space from upload api` → REFACTOR E2E helpers.
- [x] 7.1a RED write E2E test proving upload ownership is derived from the JWT/current user and ignores any client-provided owner field → GREEN ensure controller passes only authenticated `user.id` to the use case → COMMIT `test: derive upload ownership from jwt` → REFACTOR auth setup helpers.
- [x] 7.2 RED write E2E test proving upload without `study_space_name` returns validation error and creates no space → GREEN enforce required form field → COMMIT `feat: require study space name on upload api` → REFACTOR error expectations.
- [x] 7.3 RED write E2E test proving blank `study_space_name` returns safe validation error → GREEN map domain error to HTTP 422 → COMMIT `feat: validate upload study space name api` → REFACTOR error payload helper.
- [x] 7.4 RED update existing upload E2E tests to include `study_space_name` where upload should succeed → GREEN update tests and API contract → COMMIT `test: update upload e2e for space name` → REFACTOR duplicated multipart setup.
- [x] 7.5 RED write E2E test proving `GET /study-spaces` returns summaries only and does not include nested documents → GREEN ensure response DTO remains summary-only → COMMIT `test: keep study space list summary only` → REFACTOR response assertions.
- [x] 7.5a RED write E2E test proving `GET /study-spaces` derives ownership from the JWT/current user and ignores owner query/body data → GREEN ensure controller uses `GetCurrentUserUseCase` result for `owner_id` → COMMIT `test: derive study space listing ownership from jwt` → REFACTOR auth helpers.
- [x] 7.6 RED write E2E test proving `GET /study-spaces/{space_id}/documents` returns owned document summaries → GREEN add controller route, DTOs, use case wiring → COMMIT `feat: list study space documents api` → REFACTOR route naming.
- [x] 7.7 RED write E2E test proving foreign `GET /study-spaces/{space_id}/documents` returns 404 → GREEN map safe not found error to HTTP 404 → COMMIT `feat: hide foreign space documents api` → REFACTOR auth helpers.
- [x] 7.8 RED write E2E test proving unauthenticated `GET /study-spaces/{space_id}/documents` returns 401 → GREEN reuse bearer auth dependency → COMMIT `test: protect space document listing auth` → REFACTOR repeated unauthorized tests only if warranted.
- [x] 7.9 Update `shared.infrastructure.factory` to inject `PostgresStudySpaceRepository` into upload, document listing, and space-scoped search use cases.

## 8. Space-Scoped Semantic Search Infrastructure

- [x] 8.1 RED write repository integration test proving nearest chunk search filters by `study_space_id`, `owner_user_id`, and READY status → GREEN update `SemanticChunkSearchRepository` port and PostgreSQL SQL query → COMMIT `feat: filter semantic chunks by study space` → REFACTOR query construction.
- [x] 8.2 RED write E2E test proving searching one space does not return chunks from another owned space → GREEN expose or update space-scoped search route → COMMIT `feat: add space scoped semantic search api` → REFACTOR E2E data builders.
- [x] 8.3 RED write E2E test proving searching a foreign space returns 404 with no results → GREEN validate space ownership before searching → COMMIT `feat: hide foreign semantic search spaces` → REFACTOR error mapping.
- [x] 8.4 RED write E2E test proving a space with no READY documents returns an empty successful result list → GREEN preserve READY-only filter and empty result behavior → COMMIT `test: cover empty ready space search` → REFACTOR response helper.
- [x] 8.5 RED write E2E test proving unauthenticated space-scoped search returns 401 → GREEN reuse auth dependency → COMMIT `test: protect space scoped semantic search auth` → REFACTOR unauthorized helper if duplication reaches rule of three.
- [x] 8.6 Decide during implementation whether to deprecate or keep the old global `/semantic-search/search` route, then update tests and docs consistently with the chosen contract.

## 9. Backward Compatibility and Cleanup

- [x] 9.1 Update all unit, integration, and E2E test builders that create `StudyDocument` rows to provide valid `owner_user_id` and `study_space_id`.
- [x] 9.2 Update any worker or document-processing paths that load and save `StudyDocument` so `study_space_id` is preserved during status transitions.
- [x] 9.3 Verify repository `ON CONFLICT DO UPDATE` clauses do not accidentally drop or fail to preserve `owner_user_id` and `study_space_id`.
- [x] 9.4 Update application DTOs and imports to maintain strict typing under `uv run mypy src/`.
- [x] 9.5 Remove obsolete assumptions in tests or helper apps that uploads create documents without spaces.

## 10. Validation and Review

- [x] 10.1 Run targeted unit tests with `uv run pytest src/study_documents/tests/unit src/study_spaces/tests/unit src/semantic_search/tests/unit` and fix failures.
- [x] 10.2 Run targeted integration tests with `uv run pytest src/study_documents/tests/integration src/study_spaces/tests/integration src/semantic_search/tests/integration` and fix failures.
- [x] 10.3 Run targeted E2E tests with `uv run pytest src/study_documents/tests/e2e src/study_spaces/tests/e2e src/semantic_search/tests/e2e` and fix failures.
- [x] 10.4 Run `uv run ruff format .`.
- [x] 10.5 Run `uv run ruff check .` and fix lint errors.
- [x] 10.6 Run `uv run mypy src/` and fix typing errors.
- [x] 10.7 Run full `uv run pytest` and fix failures.
- [x] 10.8 Run `/task-validate` and address findings.
- [x] 10.9 Run `/task-code-review` and address design-principle findings.
- [x] 10.10 Run `/task-architecture-review` and address hexagonal boundary findings.
- [x] 10.11 Run `/task-testing-review` and address test quality or coverage findings.
- [x] 10.12 Commit all changes with a conventional commit message, for example `feat: create study spaces during document upload`.
