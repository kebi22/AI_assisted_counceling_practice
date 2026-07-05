"""Immutable published scenario version model."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, JSONColumn, UUIDMixin

if TYPE_CHECKING:
    from app.db.models.scenario import Scenario


class ScenarioVersion(UUIDMixin, Base):
    __tablename__ = "scenario_versions"

    scenario_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("scenarios.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    template_key: Mapped[str] = mapped_column(String(120), nullable=False)
    template_version: Mapped[str] = mapped_column(String(64), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(64), nullable=False)
    rubric_version: Mapped[str] = mapped_column(String(64), nullable=False)
    output_schema_version: Mapped[str] = mapped_column(String(64), nullable=False)
    rendered_client_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    rendered_evaluator_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    authoring_snapshot: Mapped[dict[str, Any]] = mapped_column(JSONColumn, nullable=False)
    rubric_snapshot: Mapped[dict[str, Any]] = mapped_column(JSONColumn, nullable=False)
    safety_policy_snapshot: Mapped[dict[str, Any]] = mapped_column(JSONColumn, nullable=False)
    learning_objectives_snapshot: Mapped[list[Any]] = mapped_column(JSONColumn, nullable=False)
    published_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    scenario: Mapped["Scenario"] = relationship(foreign_keys=[scenario_id])
