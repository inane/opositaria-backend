# DTOs & Boundaries

## Where DTOs Live

DTOs live in the Application layer, next to the UseCases that use them.

```
src/orders/
├── application/
│   ├── create_order_use_case.py
│   ├── get_order_use_case.py
│   ├── create_order_request.py   # Request DTO (if >3 params)
│   ├── order_dto.py             # Response DTO
│   └── ports/
└── ...
```

## Response DTOs

Use Pydantic `BaseModel` for DTOs. They are plain data containers with type validation at the boundary.

```python
from pydantic import BaseModel


class OrderItemDTO(BaseModel):
    product_id: str
    product_name: str
    quantity: int
    unit_price: float


class OrderDTO(BaseModel):
    id: str
    status: str
    total: float
    currency: str
    items: list[OrderItemDTO]
    created_at: str
```

### Mapping in UseCase

```python
class GetOrderUseCase:
    def __init__(self, order_repository: OrderRepository) -> None:
        self._order_repository = order_repository

    async def execute(self, order_id: str) -> OrderDTO:
        order = await self._order_repository.find_by_id(Id.create(order_id))
        if order is None:
            raise DomainError.not_found(f"Order {order_id} not found")
        return self._to_dto(order)

    @staticmethod
    def _to_dto(order: Order) -> OrderDTO:
        return OrderDTO(**order.to_primitives())
```

If the DTO needs a different structure:

```python
@staticmethod
def _to_dto(order: Order) -> OrderSummaryDTO:
    primitives = order.to_primitives()
    return OrderSummaryDTO(
        id=primitives["id"],
        total_amount=primitives["total"],
        item_count=len(primitives["items"]),
    )
```

## DTO Characteristics

- **Plain objects**: No methods, no behavior
- **Primitive types only**: str, int, float, bool, lists, nested DTOs
- **No domain types**: No Money, no Id, no entities
- **Serializable**: Can be JSON-serialized via `.model_dump()`

```python
# BAD - Contains domain types
class OrderDTO(BaseModel):
    id: Id          # Domain type
    total: Money    # Domain type

# GOOD - Only primitives
class OrderDTO(BaseModel):
    id: str
    total: float
    currency: str
```
