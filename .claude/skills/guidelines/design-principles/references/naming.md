# Naming Standards

## Rules

- Pronounceable in English, without technical abbreviations (abbreviations only allowed in lambda expressions with reduced scope)
- Avoid redundant prefixes/suffixes (`I`, `Impl`, `Abstract`)
- Concrete; avoid catch-all words (helper, util, manager) unless the domain requires it
- No type information; the IDE already shows it
- No aliases or synonyms for the same concept: one concept, one name
- Combine well with language grammar: `is_paid_invoice`, `sum_of_numbers_in(expression)`
- Prefer using "not" in the name over using the negation operator
- Distinguish nouns (classes, modules) from verbs (methods, functions)
- Allowed generic suffixes: DTO, Repository, Factory, Mapper, UseCase, Service
- Avoid comments if a self-explanatory name is possible
- Constants use camelCase, not SCREAMING_SNAKE_CASE
- Use underscore prefix for non-public members (Python convention)
- Avoid magic strings, prefer enums to represent fixed sets of values
- Prefer enums over literal types for better refactoring support

## Examples

```python
# WORSE
d = 42           # days
usr_ctrl = UsrCtrl()
i_user_repository = ...
fetch_user_info = ...

# BETTER
days_until_expiration = 42
user_authenticator = UserAuthenticator()
user_repository = ...
find_user = ...
```
