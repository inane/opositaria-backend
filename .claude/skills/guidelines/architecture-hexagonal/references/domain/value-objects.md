# Value Objects

Value Objects are **immutable** objects defined by their **attributes**, not by identity.

## The Id Value Object

Use a single generic `Id` value object for all entity identifiers instead of separate `OrderId`, `ProductId` types. Why: in this architecture, identifiers share identical behavior (create, generate, equals, to_primitives) — separate types add boilerplate without meaningful type safety, since cross-entity ID comparisons are caught by the domain logic, not the type system.

```python
from dataclasses import dataclass
from uuid import uuid4
from shared.domain.errors import DomainError


@dataclass(frozen=True)
class Id:
    value: str

    @staticmethod
    def create(value: str) -> Id:
        if not value or value.strip() == "":
            raise DomainError.validation("Id cannot be empty")
        return Id(value=value)

    @staticmethod
    def generate() -> Id:
        return Id(value=str(uuid4()))

    def equals(self, other: Id) -> bool:
        return self.value == other.value

    def to_primitives(self) -> str:
        return self.value
```

## Structure

```python
from dataclasses import dataclass
from shared.domain.errors import DomainError


@dataclass(frozen=True)
class Money:
    amount: float
    currency: str

    @staticmethod
    def create(amount: float, currency: str) -> Money:
        if amount < 0:
            raise DomainError.validation("Amount cannot be negative")
        return Money(amount=amount, currency=currency)

    @staticmethod
    def zero(currency: str = "EUR") -> Money:
        return Money(amount=0.0, currency=currency)

    def add(self, other: Money) -> Money:
        if self.currency != other.currency:
            raise DomainError.validation("Cannot add money with different currencies")
        return Money(amount=self.amount + other.amount, currency=self.currency)

    def equals(self, other: Money) -> bool:
        return self.amount == other.amount and self.currency == other.currency

    def to_primitives(self) -> dict:
        return {"amount": self.amount, "currency": self.currency}
```

## Immutability

Operations must return new instances, never mutate the original.

```python
# WORSE - Mutating the value object
@dataclass(frozen=True)
class Money:
    amount: float
    currency: str

    def add(self, other: Money) -> None:
        self.amount += other.amount  # Will raise FrozenInstanceError


# BETTER - Returning a new instance
@dataclass(frozen=True)
class Money:
    amount: float
    currency: str

    def add(self, other: Money) -> Money:
        if self.currency != other.currency:
            raise DomainError.validation("Cannot add money with different currencies")
        return Money(amount=self.amount + other.amount, currency=self.currency)
```

> **Note:** `@dataclass(frozen=True)` prevents mutation at runtime — any attempt to set an attribute raises `FrozenInstanceError`. This enforces immutability by contract.

## Self-Validation

Value objects validate constraints in factory methods, keeping constructors simple.

```python
from dataclasses import dataclass
from shared.domain.errors import DomainError


@dataclass(frozen=True)
class Email:
    value: str

    @staticmethod
    def create(value: str) -> Email:
        if "@" not in value:
            raise DomainError.validation("Invalid email format")
        return Email(value=value)

    def equals(self, other: Email) -> bool:
        return self.value == other.value

    def to_primitives(self) -> str:
        return self.value
```

## Common Value Objects

- **Identifier**: `Id` (single generic identifier for all entities)
- **Money**: `Money`, `Price`, `Amount`
- **Dates**: `DateRange`, `Period`
- **Contact**: `Email`, `PhoneNumber`, `Address`
- **Quantities**: `Quantity`, `Percentage`
