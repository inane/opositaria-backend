---
name: design-principles
description: This skill should be used when writing or reviewing code, refactoring, or when the user asks about "naming", "functions", "classes", "comments", "error handling", or "code design".
---

# Design Principles

Code design standards cover naming, functions, classes/modules, comments, and error handling.

## Naming

- Pronounceable in English, no technical abbreviations
- Avoid redundant prefixes/suffixes (`I`, `Impl`, `Abstract`)
- Concrete names; avoid catch-all words (helper, util, manager)
- No type information in names; the IDE shows it
- One concept, one name; no aliases or synonyms
- Combine well with grammar: `is_paid_invoice`, `sum_of_numbers_in(expression)`
- Prefer "not" in the name over the negation operator
- Distinguish nouns (classes, modules) from verbs (methods, functions)
- Allowed generic suffixes: DTO, Repository, Factory, Mapper, UseCase, Service
- Constants use camelCase, not SCREAMING_SNAKE_CASE
- Use underscore prefix for non-public members (Python convention)
- Prefer enums over literal types for fixed sets of values

For full naming rules with examples, see `references/naming.md`.

## Functions

1. **Single responsibility**: Each function does exactly what its name indicates
2. **Impeccable naming**: Function names are verbs describing the action
3. **Minimum arity**: 0–3 parameters; group in a dataclass/dict if exceeded
4. **No boolean flags**: Prefer specific functions (`show()/hide()`)
5. **Guard clauses**: Exit early for edge cases; reduce indentation
6. **Separate control flow and logic**: Extract iterations/branches
7. **Declarative style**: Use comprehensions/generators when it improves readability
8. **Pure functions**: Avoid side effects when possible
9. **CQS**: Commands mutate state (`None`), queries return values (no mutation). Don't mix it.
10. **No comments on functions**: No docstrings, no parameter descriptions
11. **Prioritize Immutable collections**: Avoid `.append()`, `.pop()`, `.insert()`
12. **Constants close to usage**: Define inside the function that uses them
13. **Use Optional types for return values**: Never return `None` without a type annotation; use `T | None`

For full function rules with code examples, see `references/functions.md`.

## Classes and Modules

1. **Minimum scope, maximum cohesion**: Keep things close to where they are used
2. **Simple constructors**: Move validation to factory methods; keep `__init__` as an assignment
3. **Class organization**: `__init__`, then factory `@classmethod`, then public API, then non-public methods
4. **Encapsulation by default**: Use underscore prefix for non-public methods; do not export unless necessary
5. **Law of Demeter / Tell, Don't Ask**: Avoid long call chains
6. **Rich models**: Classes encapsulate behavior; no anemic models
7. **Complete objects at construction**: No partial initialization
8. **No `@property` decorators**: Use explicit methods (`calculate_total()`, `uptime()`)
9. **Use underscore prefix for non-public members** (Python convention)
10. **No singletons**: Manage global state through the factory module
11. **Composition over inheritance**
12. **Domain-specific types**: Build classes with behavior

For full rules with code examples, see `references/classes-modules.md`.

## Comments and Formatting

- Code must be self-explanatory; comments indicate unclear code
- Only comment WHY, never WHAT
- No docstrings, no parameter descriptions
- Delete commented-out code; version control exists
- Let the formatter handle formatting (Ruff)
- No blank lines inside functions/methods; blank lines only between functions

## Error Handling

Use a single `DomainError` class with factory methods:

| Factory Method        | Type       | Use                   |
|-----------------------|------------|-----------------------|
| `create_not_found()`  | notFound   | Entity does not exist |
| `create_validation()` | validation | Invariant violated    |
| `create()`            | other      | Other domain errors   |

- Raise for invariant violations, entity not found, invalid state transitions
- Return `None` for optional values (properly typed with `T | None`); return an empty list for no results
- Include relevant context in error messages (IDs, values)
- Never expose stack traces, DB table names, or file paths
- Distinguish domain errors from technical errors; let technical errors bubble up

For the full DomainError pattern with code examples, see `references/error-handling.md`.

## Non-Negotiable Rules

- Never write production code without self-explanatory names
- Never use generic variable names (x, data, temp, info)
- Never use boolean flags that change function behavior
- Never expose internal collections directly
- Never use `@property` decorators; use explicit methods
- Never expose stack traces or internal details in error messages
- Always use factory methods for DomainError
- Always follow CQS: commands mutate (`None`), queries return (no mutation)
- Always prefer composition to inheritance
