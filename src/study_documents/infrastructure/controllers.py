"""FastAPI controllers for study document operations."""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from src.study_documents.application.dtos import (
    DocumentStatusResponse,
    UploadDocumentResponse,
)
from src.study_documents.domain.entities import StudyDocumentError

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
    use_case: Any = Depends(_get_upload_use_case),
) -> UploadDocumentResponse:
    """Upload a PDF study document for semantic processing."""
    try:
        content = await file.read()
        response = await use_case.execute(
            filename=file.filename or "untitled.pdf",
            content_type=file.content_type or "application/pdf",
            content=content,
        )
        return response
    except StudyDocumentError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        )


@router.get("/{document_id}/status", response_model=DocumentStatusResponse)
async def get_document_status(
    document_id: uuid.UUID,
    use_case: Any = Depends(_get_status_use_case),
) -> DocumentStatusResponse:
    """Get the processing status of a study document."""
    try:
        return await use_case.execute(document_id=document_id)
    except StudyDocumentError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
