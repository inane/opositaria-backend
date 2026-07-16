"""FastAPI controllers for study space operations."""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from src.study_spaces.application.dtos import (
    CreateStudySpaceRequest,
    CreateStudySpaceResponse,
    StudySpaceSummary,
)
from src.study_spaces.application.use_cases import (
    CreateStudySpaceUseCase,
    ListStudySpacesUseCase,
)
from src.study_spaces.domain.entities import StudySpaceError
from src.users.application.use_cases import GetCurrentUserUseCase
from src.users.domain.entities import UserError
from src.users.infrastructure.controllers import (
    _get_current_user_use_case,
    get_bearer_token,
)

router = APIRouter(prefix="/study-spaces", tags=["study-spaces"])


async def _get_create_space_use_case() -> Any:
    """Placeholder - overridden by factory."""
    raise NotImplementedError


async def _get_list_spaces_use_case() -> Any:
    """Placeholder - overridden by factory."""
    raise NotImplementedError


@router.post("", status_code=status.HTTP_201_CREATED, response_model=CreateStudySpaceResponse)
async def create_study_space(
    body: CreateStudySpaceRequest,
    token: str = Depends(get_bearer_token),
    auth_use_case: GetCurrentUserUseCase = Depends(_get_current_user_use_case),
    use_case: Any = Depends(_get_create_space_use_case),
) -> CreateStudySpaceResponse:
    """Create a study space from ready owned documents."""
    try:
        user = await auth_use_case.execute(token=token)
        return await use_case.execute(
            owner_id=user.id,
            name=body.name,
            document_ids=body.document_ids,
        )
    except StudySpaceError as e:
        if e.code in ("invalid_name", "empty_documents"):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail={"code": e.code, "message": e.message},
            )
        if e.code == "document_not_found":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": e.code, "message": e.message},
            )
        if e.code == "document_not_ready":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"code": e.code, "message": e.message},
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": e.code, "message": e.message},
        )
    except UserError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": e.code, "message": e.message},
        )


@router.get("", response_model=list[StudySpaceSummary])
async def list_study_spaces(
    token: str = Depends(get_bearer_token),
    auth_use_case: GetCurrentUserUseCase = Depends(_get_current_user_use_case),
    use_case: Any = Depends(_get_list_spaces_use_case),
) -> list[StudySpaceSummary]:
    """List study spaces owned by the authenticated user."""
    try:
        user = await auth_use_case.execute(token=token)
        return await use_case.execute(owner_id=user.id)
    except UserError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": e.code, "message": e.message},
        )