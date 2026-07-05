"""Scenario model.

Two concerns live on this table:

* **Student-facing fields** (``system_prompt``, ``client_name``,
  ``client_profile``, ``student_goal``, ``rubric_json`` ...) drive the
  simulation and evaluation pipelines. These are populated when a scenario is
  published.
* **Faculty authoring fields** (the structured JSON columns + ``status`` +
  ``generated_prompt``) capture the human-entered source of truth so prompts can
  be regenerated without losing faculty input.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.constants import ScenarioStatus
from app.db.base import Base, JSONColumn, TimestampMixin, UUIDMixin


class Scenario(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "scenarios"

    module_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    difficulty: Mapped[str] = mapped_column(String(32), nullable=False, default="easy")
    client_name: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    client_profile: Mapped[dict[str, Any]] = mapped_column(JSONColumn, nullable=False, default=dict)
    student_goal: Mapped[str] = mapped_column(Text, nullable=False, default="")
    system_prompt: Mapped[str] = mapped_column(Text, nullable=False, default="")
    rubric_json: Mapped[dict[str, Any]] = mapped_column(JSONColumn, nullable=False, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_by: Mapped[str | None] = mapped_column(String(255), nullable=True)

    template_key: Mapped[str] = mapped_column(
        String(120), nullable=False, default="microskills_progressive_disclosure"
    )
    template_version: Mapped[str] = mapped_column(String(64), nullable=False, default="1.0.0")
    current_version_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("scenario_versions.id"), nullable=True
    )

    # -- Authoring lifecycle ------------------------------------------------
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=ScenarioStatus.DRAFT, index=True
    )
    estimated_turns: Mapped[int | None] = mapped_column(Integer, nullable=True)
    opening_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # -- Structured faculty input (canonical source of truth) ---------------
    client_identity: Mapped[dict[str, Any] | None] = mapped_column(JSONColumn, nullable=True)
    presenting_concern: Mapped[dict[str, Any] | None] = mapped_column(JSONColumn, nullable=True)
    cultural_considerations: Mapped[dict[str, Any] | None] = mapped_column(JSONColumn, nullable=True)
    resistance_configuration: Mapped[dict[str, Any] | None] = mapped_column(JSONColumn, nullable=True)
    engagement_levels: Mapped[list[Any] | None] = mapped_column(JSONColumn, nullable=True)
    engagement_increase_rules: Mapped[list[Any] | None] = mapped_column(JSONColumn, nullable=True)
    engagement_decrease_rules: Mapped[list[Any] | None] = mapped_column(JSONColumn, nullable=True)
    disclosure_rules: Mapped[dict[str, Any] | None] = mapped_column(JSONColumn, nullable=True)
    progression_beats: Mapped[list[Any] | None] = mapped_column(JSONColumn, nullable=True)
    emotional_cue_progression: Mapped[list[Any] | None] = mapped_column(JSONColumn, nullable=True)
    silence_response_rules: Mapped[list[Any] | None] = mapped_column(JSONColumn, nullable=True)
    counselor_skill_detection: Mapped[list[Any] | None] = mapped_column(JSONColumn, nullable=True)
    session_success_indicators: Mapped[list[Any] | None] = mapped_column(JSONColumn, nullable=True)
    emotional_tone: Mapped[dict[str, Any] | None] = mapped_column(JSONColumn, nullable=True)
    hidden_information: Mapped[list[Any] | None] = mapped_column(JSONColumn, nullable=True)
    learning_objectives: Mapped[list[Any] | None] = mapped_column(JSONColumn, nullable=True)
    rubric_items: Mapped[list[Any] | None] = mapped_column(JSONColumn, nullable=True)
    competency_scale: Mapped[list[Any] | None] = mapped_column(JSONColumn, nullable=True)
    evaluation_focus_sections: Mapped[list[Any] | None] = mapped_column(JSONColumn, nullable=True)
    reflection_questions: Mapped[list[Any] | None] = mapped_column(JSONColumn, nullable=True)
    safety_rules: Mapped[dict[str, Any] | None] = mapped_column(JSONColumn, nullable=True)

    # -- Generated prompt (derived; kept separate from structured input) ----
    generated_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    prompt_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    prompt_generated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    published_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
