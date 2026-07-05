"""CRUD operations for scenarios."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import ScenarioStatus
from app.db.models.scenario import Scenario
from app.db.models.simulation_session import SimulationSession


async def get_scenario_by_id(db: AsyncSession, scenario_id: uuid.UUID) -> Scenario | None:
    return await db.get(Scenario, scenario_id)


async def get_scenario_by_slug(db: AsyncSession, slug: str) -> Scenario | None:
    result = await db.execute(select(Scenario).where(Scenario.slug == slug))
    return result.scalar_one_or_none()


async def list_active_scenarios(db: AsyncSession) -> list[Scenario]:
    result = await db.execute(
        select(Scenario).where(Scenario.is_active.is_(True)).order_by(Scenario.module_number)
    )
    return list(result.scalars().all())


async def list_published_scenarios(db: AsyncSession) -> list[Scenario]:
    result = await db.execute(
        select(Scenario)
        .where(Scenario.status == ScenarioStatus.PUBLISHED)
        .order_by(Scenario.module_number)
    )
    return list(result.scalars().all())


async def list_all_scenarios(db: AsyncSession) -> list[Scenario]:
    """All scenarios (any status) for faculty authoring, newest activity first."""
    result = await db.execute(select(Scenario).order_by(Scenario.updated_at.desc()))
    return list(result.scalars().all())


async def count_sessions_for_scenario(db: AsyncSession, scenario_id: uuid.UUID) -> int:
    result = await db.execute(
        select(func.count())
        .select_from(SimulationSession)
        .where(SimulationSession.scenario_id == scenario_id)
    )
    return int(result.scalar_one())


async def create_scenario(db: AsyncSession, **fields: Any) -> Scenario:
    scenario = Scenario(**fields)
    db.add(scenario)
    await db.flush()
    return scenario


async def update_scenario(db: AsyncSession, scenario: Scenario, **fields: Any) -> Scenario:
    """Set the provided fields. Unlike most CRUD helpers, ``None`` is written
    through so authoring can clear optional structured sections."""
    for key, value in fields.items():
        setattr(scenario, key, value)
    await db.flush()
    return scenario
