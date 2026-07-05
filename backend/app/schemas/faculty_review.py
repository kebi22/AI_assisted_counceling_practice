"""Faculty review schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.core.constants import ReviewStatus
from app.schemas.common import ORMModel


class FacultyReviewCreate(BaseModel):
    comments: str = Field(default="", max_length=5000)
    adjusted_score: float | None = Field(default=None, ge=1, le=5)
    review_status: ReviewStatus = ReviewStatus.REVIEWED


class FacultyReviewResponse(ORMModel):
    id: uuid.UUID
    session_id: uuid.UUID
    faculty_id: uuid.UUID
    comments: str
    adjusted_score: float | None
    review_status: ReviewStatus
    reviewed_at: datetime | None
