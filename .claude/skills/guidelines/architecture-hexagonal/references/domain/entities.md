# Domain Entities

Entities are objects with **identity** and **lifecycle**. Two entities are equal if they have the same identity, regardless of their attributes.

## Characteristics

- **Identity**: Has a unique identifier (use `Id` value object)
- **Lifecycle**: Can change state over time while maintaining its identity
- **Behavior**: Encapsulates business logic related to itself
- **Consistency**: Protects its invariants (business rules that must always be true)
- **Serializable**: Provides `to_primitives()` method for serialization

## Structure

```python
from dataclasses import dataclass, field
from orders.domain.value_objects.id import Id
from orders.domain.entities.order_item import OrderItem
from orders.domain.value_objects.order_status import OrderStatus
from shared.domain.errors import DomainError


@dataclass
class Order:
    id: Id
    _items: list[OrderItem] = field(default_factory=list)
    _status: OrderStatus = field(default=OrderStatus.DRAFT)

    @classmethod
    def create(cls, id: Id) -> Order:
        return cls(id=id)

    def add_item(self, item: OrderItem) -> None:
        if self._status != OrderStatus.DRAFT:
            raise DomainError.validation("Cannot add items to a non-draft order")
        self._items = [*self._items, item]

    def confirm(self) -> None:
        if len(self._items) == 0:
            raise DomainError.validation("Cannot confirm an empty order")
        self._status = OrderStatus.CONFIRMED

    def to_primitives(self) -> dict:
        return {
            "id": self.id.to_primitives(),
            "items": [item.to_primitives() for item in self._items],
            "status": self._status.value,
        }
```

## Identity

Use the generic `Id` value object for all entity identifiers. Never use primitive types directly.

```python
# WORSE - Primitive identity
@dataclass
class Order:
    id: str  # Primitive string


# BETTER - Id value object
@dataclass
class Order:
    id: Id  # Value object
```

## to_primitives Method

Every entity must provide a `to_primitives()` method that returns a plain dict with only primitive types (str, int, float, bool, lists, nested dicts). This is the single serialization contract — UseCases call `to_primitives()` to build DTOs, and infrastructure adapters use it for persistence mapping. No coupling to specific DTO or document types.

## Invariants

Invariants are validated in factory methods, keeping constructors simple (assignment only).

```python
# GOOD - Validation in factory method, simple constructor
@dataclass
class Invoice:
    id: Id
    _line_items: list[LineItem] = field(default_factory=list)
    _total: Money = field(default_factory=lambda: Money.zero())
    _status: InvoiceStatus = field(default=InvoiceStatus.DRAFT)

    @classmethod
    def create(cls, id: Id, line_items: list[LineItem]) -> Invoice:
        if len(line_items) == 0:
            raise DomainError.validation("Invoice must have at least one line item")
        total = sum((item.amount for item in line_items), Money.zero())
        return cls(id=id, _line_items=line_items, _total=total, _status=InvoiceStatus.DRAFT)


# WORSE - Validation in constructor
@dataclass
class Invoice:
    id: Id
    _line_items: list[LineItem]

    def __post_init__(self) -> None:
        if len(self._line_items) == 0:
            raise DomainError.validation("Invoice must have at least one line item")
```

## Complete Objects (No Setters)

Entities must be complete at construction. No setters, no partial initialization. Encapsulate behavior.

```python
# WORSE - Anemic model with setters
@dataclass
class Order:
    id: Id
    status: str

    def set_status(self, status: str) -> None:
        self.status = status


# BETTER - Complete object with behavior
@dataclass
class Order:
    id: Id
    _status: OrderStatus = field(default=OrderStatus.DRAFT)

    @classmethod
    def create(cls, id: Id) -> Order:
        return cls(id=id)

    def confirm(self) -> None:
        if self._status != OrderStatus.DRAFT:
            raise DomainError.validation("Only draft orders can be confirmed")
        self._status = OrderStatus.CONFIRMED

    def to_primitives(self) -> dict:
        return {"id": self.id.to_primitives(), "status": self._status.value}
```
