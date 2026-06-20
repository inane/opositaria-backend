# Function Design Standards

## Rules

1. **Contained size and single responsibility (SRP)**. Each function must "do exactly what its name indicates". Functions of 10-15 lines are a metric to detect if they have more than one responsibility; if they only have one responsibility, size does not matter

2. **Impeccable naming**. Function names must be verbs that precisely describe the action

3. **Minimum necessary signature**. Reduce arity (0-3 parameters is ideal). If exceeded, group them in a dataclass or dict with proper name and typing

4. **Avoid configuration parameters**. No boolean flags that change behaviors. Prefer specific functions (`show()/hide()`, `switch_to_read_mode()/switch_to_write_mode()`)

5. **Optional parameters in moderation**. Maximum one; if avoidable, better

6. **Simple control flow**. Use guard clauses for edge cases and exit early; reduce indentation and cyclomatic complexity

7. **Readable conditions**: Abstract combined boolean expressions into explanatory variables or functions (`is_on_sale = ...`). Prioritize affirmative conditions. Avoid using else

8. **Separate control flow and business logic**. Extract iterations and branches; delegate calculations/mutations to dedicated functions or objects. Avoid using for

9. **Prefer declarative style when it improves readability**. Use comprehensions, generators, and built-in functions with judgment; it is not dogma

10. **Encourage pure functions and referential transparency**. Avoid side effects when possible

11. **Apply CQS (Command-Query Separation)**: Commands mutate state and return `None`. Queries return value and do not mutate state. Know justified exceptions (e.g., create and return `Id` when inserting)

12. **Balance performance-readability**. Optimize only when necessary. Prioritize readability

13. **No comments on functions**

14. **Immutable collections**. Avoid `.append()`, `.pop()`, `.insert()`, `.remove()`. Prefer immutable operations that return new collections

15. **Constants close to usage**. Define constants inside the function that uses them

16. **Use Optional types for optional values**. Never return `None` without a type annotation. Use `T | None` to represent presence/absence of values

## Examples

```python
# Constants closer to usage:
# WORSE
maximumRetries = 3
timeoutMs = 5000

def fetch_with_retry(url: str) -> None:
    ...  # uses maximumRetries far from definition

# BETTER
def fetch_with_retry(url: str) -> None:
    maximum_retries = 3
    timeout_ms = 5000
    ...  # uses constants right here

# Boolean parameters:
# WORSE
def render(show_details: bool) -> None:
    if show_details:
        ...
    else:
        ...

# BETTER
def render_with_details() -> None:
    ...

def render_summary() -> None:
    ...

# CQS (Command-Query Separation):
# WORSE - Query that mutates state
def total_with_discount(self, percentage: float) -> float:
    self.applied_discount = percentage
    return self.total * (1 - percentage / 100)

# BETTER - Command and Query separated
def apply_discount(self, percentage: float) -> None:
    self.applied_discount = percentage

def calculate_total(self) -> float:
    return self.base_total * (1 - self.applied_discount / 100)
```
