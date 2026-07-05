"""CRUD helpers for immutable scenario versions."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.scenario_version import ScenarioVersion


async def next_version_number(db: AsyncSession, scenario_id: uuid.UUID) -> int:
    result = await db.execute(
        select(func.coalesce(func.max(ScenarioVersion.version_number), 0)).where(
            ScenarioVersion.scenario_id == scenario_id
        )
    )
    return int(result.scalar_one()) + 1


async def create_scenario_version(db: AsyncSession, **fields: Any) -> ScenarioVersion:
    version = ScenarioVersion(**fields)
    db.add(version)
    await db.flush()
    return version


async def get_scenario_version_by_id(
    db: AsyncSession, version_id: uuid.UUID
) -> ScenarioVersion | None:
    return await db.get(ScenarioVersion, version_id)
