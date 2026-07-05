"""Evaluation schemas, including the structured Gemini output contract."""

import uuid
from datetime import datetime

from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator

from app.core.constants import AI_FEEDBACK_DISCLAIMER
from app.schemas.common import ORMModel

class TranscriptEvidence(BaseModel):
    quote: str
    feedback: str


class RubricCriterionScore(BaseModel):
    """Score for one scenario-specific rubric criterion."""

    score: int | None = Field(default=None, ge=1)
    max_score: int = Field(default=5, ge=1)
    label: str | None = None
    description: str | None = None
    feedback: str | None = None

    @model_validator(mode="after")
    def _score_not_above_max(self) -> "RubricCriterionScore":
        if self.score is not None and self.score > self.max_score:
            raise ValueError("score cannot exceed max_score")
        return self


def normalize_rubric_scores(
    value: dict[str, Any],
) -> dict[str, RubricCriterionScore]:
    """Accept current flexible scores and legacy integer score maps."""
    normalized: dict[str, RubricCriterionScore] = {}
    for key, item in value.items():
        if isinstance(item, RubricCriterionScore):
            normalized[key] = item
        elif isinstance(item, int):
            normalized[key] = RubricCriterionScore(score=item, max_score=5)
        elif isinstance(item, dict):
            normalized[key] = RubricCriterionScore.model_validate(item)
        else:
            raise ValueError(f"Invalid rubric score for {key}.")
    return normalized


class EvaluationResult(BaseModel):
    """Structured output the Gemini evaluator must return.

    This is also used to validate the model response before persistence.
    """

    overall_score: float = Field(..., ge=1, le=5)
    rubric_scores: dict[str, RubricCriterionScore]
    strengths: list[str] = Field(..., min_length=1)
    areas_for_growth: list[str] = Field(..., min_length=1)
    evidence_from_transcript: list[TranscriptEvidence] = Field(default_factory=list)
    suggested_improved_response: str
    faculty_review_recommended: bool = False
    specialized_analyses: dict[str, object] = Field(default_factory=dict)
    missed_opportunities: list[dict[str, object]] = Field(default_factory=list)

    @field_validator("strengths", "areas_for_growth")
    @classmethod
    def _no_blank_items(cls, value: list[str]) -> list[str]:
        cleaned = [item.strip() for item in value if item and item.strip()]
        if not cleaned:
            raise ValueError("List must contain at least one non-empty item.")
        return cleaned

    @field_validator("rubric_scores", mode="before")
    @classmethod
    def _normalize_scores(
        cls, value: dict[str, Any]
    ) -> dict[str, RubricCriterionScore]:
        return normalize_rubric_scores(value)


class EvaluationResponse(ORMModel):
    """Evaluation returned to the frontend. Excludes ``raw_response``."""

    id: uuid.UUID
    session_id: uuid.UUID
    scenario_version_id: uuid.UUID | None = None
    template_key: str | None = None
    template_version: str | None = None
    rubric_version: str | None = None
    output_schema_version: str | None = None
    overall_score: float
    rubric_scores: dict[str, RubricCriterionScore]
    strengths: list[str]
    areas_for_growth: list[str]
    evidence_from_transcript: list[TranscriptEvidence]
    suggested_improved_response: str
    specialized_analyses: dict[str, object] | None = None
    missed_opportunities: list[dict[str, object]] | None = None
    faculty_review_recommended: bool = False
    created_at: datetime
    disclaimer: str = AI_FEEDBACK_DISCLAIMER

    @field_validator("rubric_scores", mode="before")
    @classmethod
    def _normalize_scores(
        cls, value: dict[str, Any]
    ) -> dict[str, RubricCriterionScore]:
        return normalize_rubric_scores(value)
