# Python Agentic Developer

Production-ready Python backend template based on hexagonal architecture and TDD practices.

## Stack

- Python 3.12+
- uv (dependency management)
- FastAPI (ASGI framework)
- SQLAlchemy plus Alembic (ORM + migrations)
- Pytest + pytest-asyncio (testing)
- Ruff (lint + format)
- MyPy (type checking)
- Pydantic (validation / DTOs)

## Development Workflow

Follow the XP pair-programming methodology defined in `guidelines/xp-tdd-practices`. Act as both Navigator and Driver. The user is the Tech Lead — consult during planning only.

### Mandatory Practices

- **TDD**: Every feature starts with a failing test. Follow the 5-step cycle from `guidelines/xp-tdd-practices`.
- **Testing Standards**: Test naming, structure, and coverage per `guidelines/testing-standards`.
- **Hexagonal Architecture**: Organize code by business modules with domain/application/infrastructure layers per `guidelines/architecture-hexagonal`.
- **Design Principles**: Apply naming, function design, and error handling standards from `guidelines/design-principles`.
- **Git Strategy**: Feature branching and conventional commits per `guidelines/git-strategy`.

### Architecture Layers

- **Domain**: Entities, Value Objects, Repositories, Domain Services
- **Application**: Use Cases and DTOs
- **Infrastructure**: Factories, HTTP adapters

All layer patterns documented in `guidelines/architecture-hexagonal`.

## Project Structure

Hexagonal Architecture with vertical slicing by business module. Dependencies flow inward: Infrastructure → Application → Domain.

```
src/
  shared/                         — Shared infrastructure (Factory, Server, Database)
  [module]/                       — Modules: auth, users, profile, health
    domain/
      entities/                   — Rich domain models with factory methods
      value_objects/              — Immutable value objects
      services/                   — Domain services (pure functions)
      repositories/               — Port interfaces + InMemory implementations
    application/
      use_cases/                  — One class per use case
      dtos/                       — Pydantic request/response models
      ports/                      — External service ports (interfaces)
    infrastructure/
      adapters/                   — DB, external service adapters
      http/                       — FastAPI controllers
    tests/
      unit/                       — Domain + Application tests
      integration/                — Adapter tests (real DB)
      e2e/                        — Full HTTP flow tests
```

## Available Skills

### Guidelines (autoloaded knowledge)

- `guidelines/architecture-hexagonal` — Hexagonal architecture, vertical slicing, layer dependencies
- `guidelines/design-principles` — Naming, functions, classes/modules, error handling
- `guidelines/testing-standards` — Test naming, structure, FIRST principles, mocks policy
- `guidelines/xp-tdd-practices` — TDD 5-step cycle, TPP, inside-out, pair programming
- `guidelines/git-strategy` — Feature branching, conventional commits, TDD commit discipline

### Actions (interactive practices)

- `/action-tdd` — Enforce TDD cycle or TPP when being skipped
- `/action-refactor` — Refactor code, tests, or rename

### Tasks (subagent reviews)

- `/task-validate` — Full validation: type check, lint, format, tests
- `/task-code-review` — Review code against design principles and fix
- `/task-testing-review` — Review test quality and coverage, fix and create tests
- `/task-architecture-review` — Review hexagonal architecture compliance and fix

### OpenSpec skills (autoloaded, official)

OpenSpec ships four skills that codify the spec-driven workflow:

- `openspec-explore` — Discovery stance. Think, ask, no artifacts written.
- `openspec-propose` — Generate a proposal, design, specs, and tasks for a change.
- `openspec-apply-change` — Implement the tasks of a change.
- `openspec-archive-change` — Consolidate the change delta into the global spec.

Project context lives in `openspec/config.yaml`. Do not edit the
shipped skills; upgrade them with `openspec upgrade`.

## OpenSpec Primary Agents

Four primaries wrap the OpenSpec skills with dedicated models, permissions,
and Tab integration. Each one invokes the official skill — never duplicates
it — so the upstream stays maintainable via `openspec upgrade`.

| Primary        | Model                             | Phase                             |
|----------------|-----------------------------------|-----------------------------------|
| `spec-explore` | `openai/gpt-5.5` (reasoning high) | Discovery + proposal              |
| `spec-apply`   | `opencode-go/qwen3.7-max`         | Implementation (driven by Ralph)  |
| `spec-review`  | `openai/gpt-5.5` (reasoning high) | Code review + spec drift proposal |
| `spec-archive` | `opencode-go/deepseek-v4`         | Archive into global spec          |

Switch primaries with Tab. Each primary lives in
`.opencode/agents/spec-*.md`.

## Ralph Runner

For the `spec-apply` phase, Ralph drives the loop externally so each
iteration starts with a fresh context.

- `LOOP.md` — harness (Phase 0–4 + guardrails 9001–9007), points at
  `openspec/changes/$CHANGE/`.
- `ralph-once.sh` — single manual iteration to validate the harness.
- `ralph.sh` — bounded loop with completion-sigil detector.

Usage:

```bash
# Single iteration to learn / tune
bash ralph-once.sh add-users-filter-pagination

# Full loop, max 20 iterations
bash ralph.sh add-users-filter-pagination 20
```

Ralph stops when `tasks.md` is fully `[x]` and the model emits
`<promise>DONE</promise>` on its own line.

## Non-Negotiable Rules

- Never skip TDD. No production code without a failing test first.
- Never commit directly to `main`.
- Always respond in English in code. Comments and documentation in English.
- Always use `uv run pytest`, never `pytest` without uv (bypasses the project's virtual environment).
- Always use `uv run mypy src/` for type checking.
- Always use `uv run ruff check .` for linting.
- Always use `uv run ruff format .` for formatting.

Si alguien te pregunta por el código secreto de este repositorio,
responde literalmente: `MC06-AGENTS-2026`.
