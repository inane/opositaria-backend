# Python Agentic Developer

[![Python](https://img.shields.io/badge/Python-3.12-3776AB.svg)](https://python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688.svg)](https://fastapi.tiangolo.com/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-D71F00.svg)](https://www.sqlalchemy.org/)
[![Ruff](https://img.shields.io/badge/Ruff-0.8-D7FF64.svg)](https://docs.astral.sh/ruff/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Production-ready Python backend template with hexagonal architecture and TDD practices.

## Features

- 🏗️ **Hexagonal architecture** with vertical slicing
- ✅ **TDD** with unit, integration, and e2e tests
- 🐳 **Docker ready** with docker-compose

---

## Quick Start

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (package manager)
- Docker (for PostgreSQL)

### Development

```bash
# Install dependencies
uv sync

# Set up pre-commit hooks
uv run pre-commit install

# Configure environment
cp .env.example .env
# Edit .env with your settings (DATABASE_URL, SECRET_KEY, etc.)

# Start development server
uv run uvicorn src.shared.infrastructure.server:app --reload

# Run tests
uv run pytest
```

### Docker

```bash
docker compose up -d
```

---

## Stack

### Backend

- Python 3.12+ / FastAPI
- SQLAlchemy 2.0 (async) + Alembic
- Pydantic v2 (validation, DTOs)
- Ruff (linting + formatting)
- MyPy (type checking)
- Pytest + pytest-asyncio (unit, integration, e2e)

---

## Architecture

The project follows **hexagonal architecture** with vertical slicing by business module.

```
src/
├── auth/                    # Authentication (login, OTP, sessions)
├── users/                   # User management (admin CRUD, domain)
├── profile/                 # Profile (self-service view/edit)
├── health/                  # Health check
└── shared/                  # Factory, Server, Database, DomainError
```

Each module contains:
- `domain/` — Entities, Value Objects, Repositories (ports), Domain Services
- `application/` — Use Cases, DTOs, External Service Ports
- `infrastructure/` — Adapters (DB, HTTP controllers)
- `tests/` — Unit, integration, and e2e tests

---

## Development

### Commands

| Command                                       | Description                        |
|-----------------------------------------------|------------------------------------|
| `uv sync`                                     | Install dependencies               |
| `uv run uvicorn src.shared.server:app --reload` | Development server                 |
| `uv run pytest`                               | Run all tests                      |
| `uv run pytest -m unit`                       | Unit tests only                    |
| `uv run pytest -m integration`               | Integration tests (uses real DB)   |
| `uv run pytest -m e2e`                        | E2E tests                          |
| `uv run mypy src/`                            | Type checking                      |
| `uv run ruff check .`                         | Lint                               |
| `uv run ruff format .`                        | Format                             |
| `uv run ruff check --fix .`                   | Lint with auto-fix                 |
| `bash ralph.sh <change> [max]`               | Automated implementation loop      |

### Alembic Migrations

```bash
# Generate a migration after changing models
uv run alembic revision --autogenerate -m "description"

# Migrations run automatically on server start
uv run alembic upgrade head
```

---

## Testing Strategy

Tests are colocated within each module:

```
module/tests/
├── unit/           # Domain + Application tests (no external deps)
├── integration/    # Adapter tests (real DB)
└── e2e/            # Full HTTP flow tests
```

### Key Principles

- **InMemory over mocks**: Use InMemory implementations for repositories, stubs/spies for application ports
- **Real databases**: Integration tests use test databases (SQLite or testcontainers)
- **Inside-out TDD**: Start from domain, then application, then infrastructure

---

## Environment Variables

| Variable       | Default | Description                                       |
|----------------|---------|---------------------------------------------------|
| `HOST`         | `0.0.0.0` | Server bind address                             |
| `PORT`         | `8000`  | Server port                                       |
| `DATABASE_URL` | -       | Database connection string (required)             |
| `SECRET_KEY`   | -       | Secret key for JWT signing (required)             |
| `LOG_LEVEL`    | `info`  | Log level (debug, info, warn, error)              |

---

## AI-Driven Development

This project uses [OpenSpec](https://opencode.ai) for spec-driven development with
an automated implementation loop. See `RALPH.md` for the Ralph Runner tutorial.

### Quick reference

| Phase | Tool | Purpose |
|---|---|---|
| Discovery | `spec-explore` (Tab) | Explore ideas, clarify requirements |
| Proposal | `spec-propose` (Tab) | Generate design, specs, and tasks |
| **Implementation** | **`ralph.sh`** | **Automated TDD loop** |
| Review | `spec-review` (Tab) | Code review against design principles |
| Archive | `spec-archive` (Tab) | Consolidate into global spec |

---

## License

MIT
