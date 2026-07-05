"""Evaluation model."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, JSONColumn, UUIDMixin

if TYPE_CHECKING:
    from app.db.models.simulation_session import SimulationSession


class Evaluation(UUIDMixin, Base):
    __tablename__ = "evaluations"

    session_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("simulation_sessions.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    scenario_version_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("scenario_versions.id"), nullable=True, index=True
    )
    template_key: Mapped[str | None] = mapped_column(String(120), nullable=True)
    template_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    rubric_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    output_schema_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    overall_score: Mapped[float] = mapped_column(Float, nullable=False)
    rubric_scores: Mapped[dict[str, Any]] = mapped_column(JSONColumn, nullable=False)
    strengths: Mapped[list[str]] = mapped_column(JSONColumn, nullable=False)
    areas_for_growth: Mapped[list[str]] = mapped_column(JSONColumn, nullable=False)
    evidence_from_transcript: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONColumn, nullable=False
    )
    suggested_improved_response: Mapped[str] = mapped_column(Text, nullable=False)
    specialized_analyses: Mapped[dict[str, Any] | None] = mapped_column(
        JSONColumn, nullable=True
    )
    missed_opportunities: Mapped[list[dict[str, Any]] | None] = mapped_column(
        JSONColumn, nullable=True
    )
    faculty_review_recommended: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    model_name: Mapped[str] = mapped_column(String(120), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(32), nullable=False)
    # Raw model output retained for auditing. Never exposed to students.
    raw_response: Mapped[dict[str, Any] | None] = mapped_column(JSONColumn, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    session: Mapped["SimulationSession"] = relationship(back_populates="evaluation")
