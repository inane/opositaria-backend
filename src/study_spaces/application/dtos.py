"""Application DTOs for study space responses."""

import uuid
from datetime import datetime

from pydantic import BaseModel


class StudySpaceSummary(BaseModel):
    """Summary of a study space for the dashboard list."""

    id: uuid.UUID
    name: str
    document_count: int
    created_at: datetime


class CreateStudySpaceResponse(BaseModel):
    """Response after creating a study space."""

    id: uuid.UUID
    name: str
    document_count: int
    created_at: datetime


class CreateStudySpaceRequest(BaseModel):
    """Request to create a study space."""

    name: str
    document_ids: list[uuid.UUID]