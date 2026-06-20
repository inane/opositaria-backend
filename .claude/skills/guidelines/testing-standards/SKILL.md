---
name: testing-standards
description: This skill should be used when writing tests, reviewing test code, or working with test structure, naming, mocks, integration tests, or E2E tests, or when files match **/*_test.py, **/*_integration_test.py, **/*_e2e_test.py.
---

# Testing Standards

Standards for writing clear, maintainable tests across all layers.

## FIRST Principles

- **Fast**: Tests must run quickly. Slow tests break the feedback loop
- **Isolated**: Each test is independent. No shared state, no execution order dependency
- **Repeatable**: Same result every time, in any environment
- **Self-validating**: Clear pass/fail result. No manual inspection needed
- **Timely**: Written at the right time (before code in TDD)

## Test Pyramid

- **Many unit tests**: Fast, isolated, cover all edge cases
- **Some integration tests**: Real DB, real sandboxes
- **Few E2E tests**: Critical user journeys only

## Naming

- Names in English, representing business rules, not implementation details
- **Grouping**: Use test class names starting with `Test` to represent the subject (e.g., `TestInvoiceCalculator`)
- **Test functions**: Use domain language in snake_case ("calculates", "validates", "allows"), avoid technical verbs ("returns", "calls", "throws")

## Structure: AAA (Arrange-Act-Assert)

- **Arrange**: Prepare context and necessary data
- **Act**: Execute the action to test
- **Assert**: Verify the expected result
- Visually separate the three sections with blank lines

## Mocks Policy

- Use InMemoryRepositories for UseCase tests (see `guidelines/architecture-hexagonal`)
- Stubs and spies are allowed on application ports (EmailSender, TokenGenerator, OTPGenerator)
- Never use mocks on repositories — always use InMemory implementations
- Before proposing any other mock: consult the Tech Lead first

## Test Strategy by Layer

| Layer                     | Test Type   | Dependencies         | File Suffix               |
| ------------------------- | ----------- | -------------------- | ------------------------- |
| Domain (entities, VOs)    | Unit        | None                 | `_test.py`                |
| Domain Services           | Unit        | None                 | `_test.py`                |
| UseCases                  | Unit        | InMemoryRepository   | `_test.py`                |
| Repository Adapters       | Integration | Real DB              | `_integration_test.py`    |
| External Service Adapters | Integration | Real service/sandbox | `_integration_test.py`    |
| HTTP/Controllers          | E2E         | Full stack           | `_e2e_test.py`            |

## Test Location

Tests live inside each module:

```
src/[module-name]/tests/
├── unit/
├── integration/
└── e2e/
```

For full testing examples, integration test setup, and E2E patterns, see `references/testing-detail.md`.

## Non-Negotiable Rules

- Never delete an existing test; fix the implementation instead
- Never modify a test to make the implementation pass
- Never mock repositories in UseCase tests (use InMemory instead)
- Never use mocks without consulting the Tech Lead first
- Always use AAA structure with blank lines between sections
- Always name tests as business rules, not technical assertions
- Always use InMemoryRepositories for UseCase unit tests
- Always fix the implementation when a test fails, not the test
- Always use `uv run pytest` to run tests
