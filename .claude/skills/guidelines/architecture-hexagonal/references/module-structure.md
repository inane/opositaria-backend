# Module Structure Details

## Full Directory Tree

```
src/
└── [module-name]/
    ├── domain/
    │   ├── entities/
    │   │   └── [entity].py
    │   ├── value_objects/
    │   │   └── [value_object].py
    │   ├── services/
    │   │   └── [domain_service].py
    │   └── repositories/
    │       └── [repository].py      # Interface + InMemory implementation
    ├── application/
    │   ├── [use_case].py
    │   ├── [request].py             # Request DTO (if >3 params)
    │   ├── [dto].py                 # Response DTO
    │   └── ports/
    │       └── [external_service].py # External service ports (driven)
    ├── infrastructure/
    │   ├── adapters/
    │   │   ├── [repository_impl].py
    │   │   └── [api_client].py
    │   └── http/
    │       └── [controller].py
    └── tests/
        ├── unit/
        │   ├── [entity]_test.py
        │   ├── [value_object]_test.py
        │   └── [use_case]_test.py
        ├── integration/
        │   └── [repository]_integration_test.py
        └── e2e/
            └── [controller]_e2e_test.py
```

## File Naming Examples

```python
# Domain - entities/
order.py  # Entity

# Domain - value_objects/
money.py  # Value Object
order_id.py  # Value Object (or use generic Id)
positive_number.py  # Value Object

# Domain - services/
pricing_service.py  # Domain Service (function module)

# Domain - repositories/
order_repository.py  # Interface + InMemory implementation

# Application
create_order_use_case.py
calculate_invoice_use_case.py
payment_gateway.py  # External service port (interface)
invoice_notifier.py  # External service port (interface)

# Infrastructure
mongo_order_repository.py  # Repository adapter
stripe_payment_adapter.py  # External service adapter
email_invoice_notifier.py  # External service adapter
order_controller.py  # HTTP controller
```

## Cross-Module Communication Rules

### Allowed imports from another module

```python
# GOOD - Importing domain and repositories from another module
from products.domain.entities.product import Product
from products.domain.repositories.product_repository import ProductRepository
```

### Forbidden imports from another module

```python
# BAD - Importing a UseCase from another module
from products.application.create_product_use_case import CreateProductUseCase
```

## Ports and Adapters Examples

### Repository (Domain)

```python
from typing import Optional, Protocol
from orders.domain.entities.order import Order
from orders.domain.value_objects.id import Id


class OrderRepository(Protocol):
    async def save(self, order: Order) -> None: ...

    async def find_by_id(self, id: Id) -> Optional[Order]: ...

    async def find_by_customer(self, customer_id: Id) -> list[Order]: ...


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
        return [o for o in self._orders.values() if o.customer_id.to_primitives() == customer_id.to_primitives()]
```

> **Note:** Backend repositories typically use `save()` (upsert pattern). Frontend repositories may use separate `create()` and `update()` methods when the adapter needs to distinguish between HTTP POST and PATCH.

### External Service Port (Application)

```python
# src/invoices/application/ports/invoice_notifier.py
from typing import Protocol
from invoices.domain.entities.invoice import Invoice
from invoices.domain.value_objects.id import Id


class InvoiceNotifier(Protocol):
    async def notify_invoice_created(self, invoice: Invoice) -> None: ...

    async def notify_payment_received(self, invoice_id: Id) -> None: ...
```

### Adapter (Infrastructure)

```python
# src/invoices/infrastructure/adapters/mongo_invoice_repository.py
from typing import Optional
from invoices.domain.repositories.invoice_repository import InvoiceRepository
from invoices.domain.entities.invoice import Invoice
from invoices.domain.value_objects.id import Id


class MongoInvoiceRepository:
    def __init__(self, collection) -> None:
        self._collection = collection

    async def save(self, invoice: Invoice) -> None:
        document = self._to_document(invoice)
        await self._collection.update_one(
            {"_id": document["_id"]},
            {"$set": document},
            upsert=True,
        )

    async def find_by_id(self, id: Id) -> Optional[Invoice]:
        document = await self._collection.find_one({"_id": id.to_primitives()})
        if document is None:
            return None
        return self._to_domain(document)

    def _to_document(self, invoice: Invoice) -> dict:
        return {"_id": invoice.id.to_primitives(), **invoice.to_primitives()}

    def _to_domain(self, document: dict) -> Invoice:
        # Map MongoDB document to domain entity
        ...
```
