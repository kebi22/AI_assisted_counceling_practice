"""Scenario application workflows."""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import ScenarioStatus
from app.crud import scenario as scenario_crud
from app.core.exceptions import ResourceNotFoundError
from app.db.models.scenario import Scenario
from app.schemas.scenario import ScenarioDetailResponse, ScenarioSummaryResponse


async def list_scenarios(db: AsyncSession) -> list[ScenarioSummaryResponse]:
    scenarios = await scenario_crud.list_published_scenarios(db)
    return [ScenarioSummaryResponse.model_validate(s) for s in scenarios]


async def get_scenario(db: AsyncSession, scenario_id: uuid.UUID) -> ScenarioDetailResponse:
    return ScenarioDetailResponse.model_validate(
        await get_scenario_model(db, scenario_id)
    )


async def get_scenario_model(db: AsyncSession, scenario_id: uuid.UUID) -> Scenario:
    """Return the ORM scenario, raising if missing/unpublished. For internal use."""
    scenario = await scenario_crud.get_scenario_by_id(db, scenario_id)
    if scenario is None or scenario.status != ScenarioStatus.PUBLISHED:
        raise ResourceNotFoundError("Scenario not found.")
    return scenario
