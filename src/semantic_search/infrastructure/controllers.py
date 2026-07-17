"""FastAPI controller for semantic search."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.semantic_search.application.dtos import SemanticSearchResponse
from src.semantic_search.domain.value_objects import SemanticSearchError
from src.users.application.use_cases import GetCurrentUserUseCase
from src.users.domain.entities import UserError
from src.users.infrastructure.controllers import (
    _get_current_user_use_case,
    get_bearer_token,
)

router = APIRouter(prefix="/semantic-search", tags=["semantic-search"])


async def _get_search_use_case() -> Any:
    """Placeholder - overridden by factory."""
    raise NotImplementedError


@router.post("/search", response_model=SemanticSearchResponse)
async def search_documents(
    query: str = Query(..., min_length=1, description="Semantic search query text"),
    limit: int | None = Query(
        None, ge=1, le=50, description="Maximum number of results"
    ),
    token: str = Depends(get_bearer_token),
    auth_use_case: GetCurrentUserUseCase = Depends(_get_current_user_use_case),
    use_case: Any = Depends(_get_search_use_case),
) -> SemanticSearchResponse:
    """Search processed study documents semantically.

    Results are scoped to the authenticated user's owned documents.
    """
    try:
        user = await auth_use_case.execute(token=token)
        return await use_case.execute(
            query_text=query,
            limit=limit,
            owner_id=user.id,
        )
    except UserError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": e.code, "message": e.message},
        )
    except SemanticSearchError as e:
        status_code = (
            status.HTTP_503_SERVICE_UNAVAILABLE
            if e.error_type == SemanticSearchError.SERVICE
            else status.HTTP_422_UNPROCESSABLE_CONTENT
        )
        raise HTTPException(status_code=status_code, detail=str(e))
