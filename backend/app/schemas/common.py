"""Shared schema primitives."""

from pydantic import BaseModel, ConfigDict


class ORMModel(BaseModel):
    """Base schema for responses derived from ORM objects."""

    model_config = ConfigDict(from_attributes=True)


class HealthResponse(BaseModel):
    status: str = "healthy"


class MessageDetail(BaseModel):
    """Generic informational message payload."""

    detail: str
