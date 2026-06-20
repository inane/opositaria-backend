---
name: architecture-hexagonal
description: This skill should be used when creating modules, organizing code by layers, working with "hexagonal architecture", "ports and adapters", domain entities, value objects, repositories, use cases, DTOs, factory modules, HTTP controllers, or when deciding where code belongs, or when files match **/domain/**, **/application/**, **/infrastructure/**, **/*.py.
---

# Hexagonal Architecture

Code is organized by business modules (vertical slicing), not by technical layer. The directory structure "screams" the
business domain — folders named after business concepts (orders, invoices), not technical layers (controllers,
services).

## Module Structure

```
src/
└── [module-name]/
    ├── domain/           # Business core (no external dependencies)
    │   ├── entities/
    │   ├── value_objects/
    │   ├── services/
    │   └── repositories/     # Interface + InMemory implementation
    ├── application/      # Use cases and ports for external services
    │   ├── [use_case].py
    │   └── ports/
    ├── infrastructure/   # Adapters (concrete implementations)
    │   ├── adapters/
    │   └── http/             # Primary port (driver)
    └── tests/
        ├── unit/
        ├── integration/
        └── e2e/
```

## Layers and Responsibilities

### 1. Domain (Center of the Hexagon)

- **Entities**: Objects with identity and lifecycle
- **Value Objects**: Immutable objects defined by attributes
- **Domain Services**: Logic that does not belong to a specific entity
- **Repositories**: Interfaces plus InMemory implementations
- **DomainError**: Single error class with factory methods (see `guidelines/design-principles`)
- No dependencies towards application or infrastructure
- No frameworks or external libraries

### 2. Application (Use Cases)

- **Use Cases**: Orchestrate business logic
- **External Service Ports**: Interfaces for external services
- Depends only on Domain

### 3. Infrastructure (Adapters)

- **Adapters**: Concrete implementations of ports
- **Controllers/Handlers**: HTTP entry points, CLI, events
- Depends on Application and Domain
- Frameworks and libraries live here

## Dependency Rule

```
Infrastructure -> Application -> Domain
```

- Dependencies always point towards the center
- Domain never imports from Application or Infrastructure
- Application never imports from Infrastructure

## Ports and Adapters

**Repositories** (in Domain): Define contracts and include InMemory implementations in the same file. Why: InMemory is
the default test double, co-locating it eliminates the need for mocks in UseCase tests. See
`references/domain/repositories.md` for details.

**External Service Ports** (in Application): Interfaces for external services (email, payments, notifications).

**Adapters** (in Infrastructure): Concrete implementations of ports. See `references/infrastructure/factory.md` for
details.

## Cross-Module Communication

### Can import from another module:

- Domain entities and value objects
- Ports (interfaces)

### Cannot import from another module:

- UseCases (a UseCase must never call another UseCase)

## Naming Conventions

| Layer          | Allowed Suffixes                                          |
|----------------|-----------------------------------------------------------|
| Domain         | Entity (implicit), ValueObject, DomainService, Repository |
| Application    | UseCase, Service, DTO, Port                               |
| Infrastructure | Repository (impl), Adapter, Controller, Handler, Client   |

- One file per class
- File name follows PascalCase for classes, snake_case for modules

## Detailed Patterns by Layer

- **Domain**: `references/domain/entities.md`, `references/domain/value-objects.md`,
  `references/domain/repositories.md`, `references/domain/domain-services.md`
- **Application**: `references/application/usecases.md`, `references/application/dtos.md`
- **Infrastructure**: `references/infrastructure/factory.md`, `references/infrastructure/http-adapters.md`
- **Structure**: `references/module-structure.md`

## Non-Negotiable Rules

- Never import frameworks or libraries in Domain
- Never import from Application or Infrastructure in Domain
- Never import from Infrastructure in Application
- Never import a UseCase from another module
- Never put business logic in Infrastructure
- Never create "God" classes (OrderManager, ProductHelper)
- Always create a port (interface) before its adapter
- Always keep Domain free of external dependencies
- Always validate the dependency rule on every import
- Always group code by business module, not by technical layer
- Always consult the Tech Lead before creating a new module
