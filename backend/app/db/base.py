"""SQLAlchemy declarative base and shared column mixins.

This module also imports every model so that Alembic can discover the full
metadata via ``app.db.base``.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, JSON, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# JSON column that uses native JSONB on PostgreSQL and falls back to JSON
# elsewhere (e.g. SQLite during tests).
JSONColumn = JSON().with_variant(JSONB(), "postgresql")


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


class UUIDMixin:
    """Adds a UUID primary key."""

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )


class TimestampMixin:
    """Adds timezone-aware created/updated timestamps."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


# Import models so that ``Base.metadata`` is fully populated for Alembic.
# Imported at module end to avoid circular imports.
from app.db.models import (  # noqa: E402,F401
    evaluation,
    faculty_review,
    message,
    scenario,
    scenario_version,
    simulation_session,
    session_state,
    user,
)
