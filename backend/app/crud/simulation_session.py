"""CRUD operations for simulation sessions."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.constants import SessionStatus
from app.db.models.simulation_session import SimulationSession


async def create_session(
    db: AsyncSession,
    *,
    student_id: uuid.UUID,
    scenario_id: uuid.UUID,
    scenario_version_id: uuid.UUID | None = None,
) -> SimulationSession:
    session = SimulationSession(
        student_id=student_id,
        scenario_id=scenario_id,
        scenario_version_id=scenario_version_id,
        status=SessionStatus.ACTIVE,
        student_message_count=0,
        started_at=datetime.now(timezone.utc),
    )
    db.add(session)
    await db.flush()
    return session


async def get_session_by_id(
    db: AsyncSession, session_id: uuid.UUID
) -> SimulationSession | None:
    return await db.get(SimulationSession, session_id)


async def get_session_with_messages(
    db: AsyncSession, session_id: uuid.UUID
) -> SimulationSession | None:
    result = await db.execute(
        select(SimulationSession)
        .where(SimulationSession.id == session_id)
        .options(
            selectinload(SimulationSession.messages),
            selectinload(SimulationSession.evaluation),
            selectinload(SimulationSession.faculty_review),
            selectinload(SimulationSession.state),
        )
    )
    return result.scalar_one_or_none()


async def list_student_sessions(
    db: AsyncSession, student_id: uuid.UUID
) -> list[SimulationSession]:
    result = await db.execute(
        select(SimulationSession)
        .where(SimulationSession.student_id == student_id)
        .order_by(SimulationSession.created_at.desc())
        .options(selectinload(SimulationSession.evaluation))
    )
    return list(result.scalars().all())


async def list_completed_sessions(
    db: AsyncSession, statuses: tuple[SessionStatus, ...]
) -> list[SimulationSession]:
    result = await db.execute(
        select(SimulationSession)
        .where(SimulationSession.status.in_(statuses))
        .order_by(SimulationSession.ended_at.desc().nullslast())
        .options(
            selectinload(SimulationSession.evaluation),
            selectinload(SimulationSession.faculty_review),
        )
    )
    return list(result.scalars().all())


async def update_session_status(
    db: AsyncSession,
    session: SimulationSession,
    status: SessionStatus,
    *,
    set_ended_at: bool = False,
) -> SimulationSession:
    session.status = status
    if set_ended_at and session.ended_at is None:
        session.ended_at = datetime.now(timezone.utc)
    await db.flush()
    return session


async def increment_student_message_count(
    db: AsyncSession, session: SimulationSession
) -> SimulationSession:
    session.student_message_count += 1
    await db.flush()
    return session
