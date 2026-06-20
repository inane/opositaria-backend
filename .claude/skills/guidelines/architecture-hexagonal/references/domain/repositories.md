# Domain Repositories

## Repository Interface + InMemory Implementation

Repository interfaces and their InMemory implementations live together in `domain/repositories/`.

`Optional[T]` (or `T | None` in Python 3.12+) is the Python-native way to express nullable return values. Use `Optional[T]` for readability across the project.

```python
# src/orders/domain/repositories/order_repository.py
from typing import Optional, Protocol
from orders.domain.entities.order import Order
from orders.domain.value_objects.id import Id


# Interface
class OrderRepository(Protocol):
    async def save(self, order: Order) -> None: ...

    async def find_by_id(self, id: Id) -> Optional[Order]: ...

    async def find_by_customer(self, customer_id: Id) -> list[Order]: ...


# InMemory implementation (same file)
class InMemoryOrderRepository:
    def __init__(self, initial_orders: list[Order] | None = None) -> None:
        self._orders: dict[str, Order] = {}
        if initial_orders:
            for order in initial_orders:
                self._orders[order.id.to_primitives()] = order

    async def save(self, order: Order) -> None:
        self._orders[order.id.to_primitives()] = order

    async def find_by_id(self, id: Id) -> Optional[Order]:
        return self._orders.get(id.to_primitives())

    async def find_by_customer(self, customer_id: Id) -> list[Order]:
        return sorted(
            [o for o in self._orders.values()
             if o.customer_id.equals(customer_id)],
            key=lambda o: o.id.to_primitives(),
        )
```

## Repository Characteristics

- **Domain language**: Use domain terms, not database terms
- **Entity-centric**: Work with domain entities, not primitives or DTOs
- **No implementation details**: The interface does not reveal storage mechanism

```python
# WORSE - Database-oriented interface
class OrderRepository(Protocol):
    async def insert(self, order: dict) -> None: ...
    async def find_one(self, id: str) -> Optional[dict]: ...


# BETTER - Domain-oriented interface
class OrderRepository(Protocol):
    async def save(self, order: Order) -> None: ...
    async def find_by_id(self, id: Id) -> Optional[Order]: ...
```

## Real Adapter (Infrastructure)

Real adapters implement the repository interface with actual database logic. They live in `infrastructure/adapters/`.

```python
# src/orders/infrastructure/adapters/mongo_order_repository.py
from typing import Optional
from orders.domain.repositories.order_repository import OrderRepository
from orders.domain.entities.order import Order
from orders.domain.value_objects.id import Id


class MongoOrderRepository:
    def __init__(self, collection) -> None:
        self._collection = collection

    async def save(self, order: Order) -> None:
        document = self._to_document(order)
        await self._collection.update_one(
            {"_id": document["_id"]},
            {"$set": document},
            upsert=True,
        )

    async def find_by_id(self, id: Id) -> Optional[Order]:
        document = await self._collection.find_one({"_id": id.to_primitives()})
        if document is None:
            return None
        return self._to_domain(document)

    @staticmethod
    def _to_document(order: Order) -> dict:
        return {"_id": order.id.to_primitives(), **order.to_primitives()}

    @staticmethod
    def _to_domain(document: dict) -> Order:
        # Map MongoDB document to domain entity
        ...
```

## When to Use Each

| Context                  | Use                    |
|--------------------------|------------------------|
| UseCase unit tests       | InMemoryRepository     |
| Repository adapter tests | Real adapter + Real DB |
| E2E tests                | Real adapter + Real DB |
| Production               | Real adapter           |

## File Structure

```
src/orders/
├── domain/
│   └── repositories/
│       └── order_repository.py       # Interface + InMemory (same file)
└── infrastructure/
    └── adapters/
        └── mongo_order_repository.py  # Real adapter for production
```
