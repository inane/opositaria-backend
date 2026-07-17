"""FastAPI controllers for study document operations."""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from src.study_documents.application.dtos import (
    DocumentStatusResponse,
    UploadDocumentResponse,
    UploadError,
)
from src.study_documents.domain.entities import StudyDocumentError
from src.study_spaces.domain.entities import StudySpaceError
from src.users.domain.entities import UserError
from src.users.infrastructure.controllers import (
    _get_current_user_use_case,
    get_bearer_token,
)
from src.users.application.use_cases import GetCurrentUserUseCase

router = APIRouter(prefix="/study-documents", tags=["study-documents"])


async def _get_upload_use_case() -> Any:
    """Placeholder - overridden by factory."""
    raise NotImplementedError


async def _get_status_use_case() -> Any:
    """Placeholder - overridden by factory."""
    raise NotImplementedError


@router.post(
    "/upload",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=UploadDocumentResponse,
)
async def upload_document(
    file: UploadFile = File(...),
    study_space_name: str = File(..., description="Name of the study space to create"),
    use_case: Any = Depends(_get_upload_use_case),
    token: str = Depends(get_bearer_token),
    auth_use_case: GetCurrentUserUseCase = Depends(_get_current_user_use_case),
) -> UploadDocumentResponse:
    """Upload a PDF study document and create a study space with the given name."""
    try:
        user = await auth_use_case.execute(token=token)
        content = await file.read()
        response = await use_case.execute(
            filename=file.filename or "untitled.pdf",
            content_type=file.content_type or "application/pdf",
            content=content,
            owner_user_id=user.id,
            study_space_name=study_space_name,
        )
        return response
    except StudyDocumentError as e:
        error_payload = UploadError(code=e.code, message=e.message).__dict__
        if e.code == "file_too_large":
            raise HTTPException(
                status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                detail=error_payload,
            )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=error_payload,
        )
    except StudySpaceError as e:
        if e.code == "invalid_name":
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
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


@router.get("/{document_id}/status", response_model=DocumentStatusResponse)
async def get_document_status(
    document_id: uuid.UUID,
    use_case: Any = Depends(_get_status_use_case),
    token: str = Depends(get_bearer_token),
    auth_use_case: GetCurrentUserUseCase = Depends(_get_current_user_use_case),
) -> DocumentStatusResponse:
    """Get the processing status of a study document."""
    try:
        user = await auth_use_case.execute(token=token)
        return await use_case.execute(document_id=document_id, owner_id=user.id)
    except StudyDocumentError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except UserError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": e.code, "message": e.message},
        )
