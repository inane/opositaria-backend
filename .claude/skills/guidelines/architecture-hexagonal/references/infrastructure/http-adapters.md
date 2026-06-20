# HTTP API Design Detail

## Controller Structure

```python
from fastapi import APIRouter, HTTPException
from orders.application.create_order_use_case import CreateOrderUseCase
from orders.application.get_order_use_case import GetOrderUseCase
from shared.domain.errors import DomainError


class OrderController:
    def __init__(
        self,
        create_order_use_case: CreateOrderUseCase,
        get_order_use_case: GetOrderUseCase,
    ) -> None:
        self._create_order_use_case = create_order_use_case
        self._get_order_use_case = get_order_use_case

    async def create(self, request: CreateOrderRequest) -> dict:
        if request.product_id is None or not isinstance(request.product_id, str):
            raise HTTPException(status_code=400, detail="product_id is required")
        if not isinstance(request.quantity, int):
            raise HTTPException(status_code=400, detail="quantity must be an integer")

        try:
            order = await self._create_order_use_case.execute(
                request.product_id, request.quantity
            )
            return order
        except DomainError as error:
            raise self._handle_error(error)

    async def get_by_id(self, order_id: str) -> dict: ...
    async def list(self) -> list[dict]: ...

    @staticmethod
    def _handle_error(error: DomainError) -> HTTPException:
        status_map = {
            "not_found": 404,
            "validation": 422,
        }
        return HTTPException(
            status_code=status_map.get(error.type, 400),
            detail=str(error),
        )
```

## Input Validation

Validate only types and nulls in the Controller using Pydantic request models. Business rules are validated in the domain.

```python
# BAD - Duplicates domain validation
if request.quantity <= 0:
    raise HTTPException(status_code=422, detail="quantity must be positive")


# GOOD - Let PositiveNumber.create() validate this
# The UseCase will raise DomainError.validation() if invalid

# Pydantic handles type validation at the boundary
class CreateOrderRequest(BaseModel):
    product_id: str
    quantity: int
```

## Error Handling in Controllers

Map DomainError types to HTTP status codes.

```python
from fastapi import HTTPException
from shared.domain.errors import DomainError


class OrderController:
    @staticmethod
    def _handle_error(error: DomainError) -> HTTPException:
        status_map = {
            "not_found": 404,
            "validation": 422,
            "other": 400,
        }
        status = status_map.get(error.type, 500)
        if status == 500:
            # Technical error - log and return 500
            import logging
            logging.exception(error)
            return HTTPException(status_code=500, detail="Internal server error")
        return HTTPException(status_code=status, detail=str(error))
```

## Response Format

### Success: Return the resource directly

```python
# GET /orders/123
{
    "id": "123",
    "status": "confirmed",
    "total": 150.00,
    "items": [...]
}

# POST /orders (201 Created)
{
    "id": "456",
    "status": "draft",
    ...
}

# DELETE /orders/123 (204 No Content)
# No body
```

### Error: Return error message

```python
# 400, 404, 422, etc.
{
    "error": "Product prod-123 not found"
}
```

## FastAPI Router Setup

```python
from fastapi import APIRouter, Depends
from factory import Factory


def get_order_controller() -> OrderController:
    return Factory.create_order_controller()


router = APIRouter()


@router.post("/orders", status_code=201)
async def create_order(
    request: CreateOrderRequest,
    controller: OrderController = Depends(get_order_controller),
) -> dict:
    return await controller.create(request)


@router.get("/orders/{order_id}")
async def get_order(
    order_id: str,
    controller: OrderController = Depends(get_order_controller),
) -> dict:
    return await controller.get_by_id(order_id)
```
