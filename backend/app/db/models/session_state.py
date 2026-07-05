"""Per-session client state for engagement and disclosure progression."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import ForeignKey, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, JSONColumn, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.db.models.simulation_session import SimulationSession


class SessionState(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "session_states"

    session_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("simulation_sessions.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    engagement_level: Mapped[int] = mapped_column(Integer, nullable=False, default=2)
    trust_level: Mapped[int] = mapped_column(Integer, nullable=False, default=2)
    disclosure_stage: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    session_stage: Mapped[str] = mapped_column(String(32), nullable=False, default="early")
    emotional_depth: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    rupture_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    repair_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    revealed_information: Mapped[list[Any]] = mapped_column(
        JSONColumn, nullable=False, default=list
    )
    emotional_cues: Mapped[list[Any]] = mapped_column(JSONColumn, nullable=False, default=list)
    state_history: Mapped[list[Any]] = mapped_column(JSONColumn, nullable=False, default=list)

    session: Mapped["SimulationSession"] = relationship(back_populates="state")
