# Factory Pattern Examples

Use a simple static Factory class instead of DI containers. Why: DI containers add magic (decorators, metadata reflection, runtime resolution) that obscures the dependency graph. A plain Factory makes all wiring explicit, visible, and debuggable — the dependency tree is readable code, not container configuration.

## Full Factory Structure

```python
from orders.application.create_order_use_case import CreateOrderUseCase
from orders.application.get_order_use_case import GetOrderUseCase
from orders.infrastructure.adapters.mongo_order_repository import MongoOrderRepository
from orders.infrastructure.adapters.mongo_product_repository import MongoProductRepository
from orders.infrastructure.http.order_controller import OrderController


class Factory:
    # Cached instances
    _order_repository: OrderRepository | None = None
    _product_repository: ProductRepository | None = None
    _mongo_client: MongoClient | None = None

    # --- Infrastructure (cached) ---

    @classmethod
    async def connect_to_mongo(cls) -> None:
        cls._mongo_client = MongoClient(...)

    @classmethod
    def _get_order_repository(cls) -> OrderRepository:
        if cls._order_repository is None:
            cls._order_repository = MongoOrderRepository(cls._mongo_client.db())
        return cls._order_repository

    @classmethod
    def _get_product_repository(cls) -> ProductRepository:
        if cls._product_repository is None:
            cls._product_repository = MongoProductRepository(cls._mongo_client.db())
        return cls._product_repository

    # --- Use Cases (new instance each time) ---

    @classmethod
    def create_create_order_use_case(cls) -> CreateOrderUseCase:
        return CreateOrderUseCase(
            cls._get_order_repository(),
            cls._get_product_repository(),
        )

    @classmethod
    def create_get_order_use_case(cls) -> GetOrderUseCase:
        return GetOrderUseCase(cls._get_order_repository())

    # --- Controllers (new instance each time) ---

    @classmethod
    def create_order_controller(cls) -> OrderController:
        return OrderController(
            cls.create_create_order_use_case(),
            cls.create_get_order_use_case(),
        )
```

## When to Use `get` vs `create`

### `_get_` (cached/singleton)

- Database connections
- Repository adapters
- External service adapters
- Anything expensive to create or stateful

### `create_` (new instance)

- UseCases
- Controllers
- Request-scoped objects
- Anything stateless or per-request

## File Location

```
src/
├── factory.py          # Main factory
├── orders/
│   ├── domain/
│   ├── application/
│   └── infrastructure/
└── products/
    └── ...
```

## Testing

For tests, create separate factory files that use InMemoryRepositories instead of real adapters.
