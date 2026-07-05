"""Message schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.core.config import settings
from app.core.constants import Speaker
from app.schemas.common import ORMModel


class MessageCreate(BaseModel):
    content: str = Field(
        ...,
        min_length=settings.student_message_min_length,
        max_length=settings.student_message_max_length,
    )

    @field_validator("content")
    @classmethod
    def _strip_and_validate(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Message content cannot be empty.")
        return stripped


class MessageResponse(ORMModel):
    id: uuid.UUID
    speaker: Speaker
    content: str
    sequence_number: int
    created_at: datetime


class SendMessageResponse(BaseModel):
    """Response returned after a student message produces an AI-client reply."""

    session_id: uuid.UUID
    message: MessageResponse
