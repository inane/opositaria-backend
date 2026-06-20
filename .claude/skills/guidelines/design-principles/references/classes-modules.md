# Classes and Modules Standards

## Rules

1. **Minimum scope for maximum cohesion**. If a method or function only uses a constant and nobody else uses it, put it inside the function

2. **Simple constructors**. If they have validation logic at creation, move it to a `@classmethod` factory and keep `__init__` simple. If there is no complex validation, do not create unnecessary factory methods

3. **Class organization**: `__init__` first, followed by factory `@classmethod`, then public API, finally non-public methods. Attributes can be declared in `__init__`

4. **Encapsulation by default**. Use underscore prefix for non-public methods and do not export functions unless necessary. Limit accessibility

5. **Apply Law of Demeter and Tell, Don't Ask**

6. **Avoid anemic models**. Classes should encapsulate behavior, except at application boundaries where DTOs are used

7. **Complete objects at construction**. Objects should be fully initialized when created

8. **Never use `@property` decorators**. No `@property` syntax. Use explicit methods instead (`calculate_total()`, `uptime()`)

9. **Use underscore prefix for non-public members** (Python convention). Mark internal attributes and methods with a leading underscore: `_role`, `_name`

10. **Never use singletons**. If an instance has global state, manage it through the application factory module

11. **Composition over inheritance**. Avoid inheritance, prioritize composition

12. **Domain-specific types**. Build classes with behavior, especially in the application domain

## Examples

```python
# Tell, Don't Ask and Law of Demeter:
# WORSE - Ask (we ask and decide outside)
if order.customer().address().city() == 'Madrid':
    order.apply_discount(10)

# BETTER - Tell (we tell it what to do)
order.apply_discount_for_city('Madrid', 10)

# WORSE - Law of Demeter violation (long chain)
city = user.account().settings().location().city()

# BETTER - Law of Demeter (single dot)
city = user.city()

# Anemic Model vs Rich Model:
# WORSE - Anemic model
@dataclass
class Order:
    items: list[Item]
    total: float

# Logic outside
total = sum(item.price for item in order.items)

# BETTER - Rich model
class Order:
    def __init__(self, items: list[Item]) -> None:
        self._items = items

    def calculate_total(self) -> float:
        return sum(item.price for item in self._items)

# @property decorator:
# WORSE - @property decorator
class User:
    def __init__(self, role: UserRole) -> None:
        self._role = role

    @property
    def role(self) -> UserRole:
        return self._role

# BETTER - explicit method
class User:
    def __init__(self, role: UserRole) -> None:
        self._role = role

    def get_role(self) -> UserRole:
        return self._role
```
