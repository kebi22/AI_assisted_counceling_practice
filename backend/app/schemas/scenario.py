"""Scenario schemas."""

import uuid
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class ScenarioCreate(BaseModel):
    module_number: int = 1
    title: str
    slug: str
    description: str
    difficulty: str = "Easy"
    client_name: str
    client_profile: dict[str, Any] = Field(default_factory=dict)
    student_goal: str
    system_prompt: str
    rubric_json: dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True
    created_by: str | None = None


class ScenarioUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    difficulty: str | None = None
    student_goal: str | None = None
    system_prompt: str | None = None
    rubric_json: dict[str, Any] | None = None
    is_active: bool | None = None


class ScenarioSummaryResponse(ORMModel):
    id: uuid.UUID
    module_number: int
    template_key: str
    template_version: str
    current_version_id: uuid.UUID | None = None
    title: str
    slug: str
    difficulty: str
    client_name: str
    is_active: bool


class ScenarioDetailResponse(ORMModel):
    id: uuid.UUID
    module_number: int
    template_key: str
    template_version: str
    current_version_id: uuid.UUID | None = None
    title: str
    slug: str
    description: str
    difficulty: str
    client_name: str
    client_profile: dict[str, Any]
    student_goal: str
    rubric_json: dict[str, Any]
    is_active: bool
    # Note: ``system_prompt`` is intentionally excluded so it is never exposed.
