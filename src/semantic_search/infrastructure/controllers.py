"""FastAPI controller for semantic search."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.semantic_search.application.dtos import SemanticSearchResponse
from src.semantic_search.domain.value_objects import SemanticSearchError

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
    use_case: Any = Depends(_get_search_use_case),
) -> SemanticSearchResponse:
    """Search processed study documents semantically."""
    try:
        return await use_case.execute(query_text=query, limit=limit)
    except SemanticSearchError as e:
        status_code = (
            status.HTTP_503_SERVICE_UNAVAILABLE
            if e.error_type == SemanticSearchError.SERVICE
            else status.HTTP_422_UNPROCESSABLE_ENTITY
        )
        raise HTTPException(status_code=status_code, detail=str(e))
