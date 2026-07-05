"""Scenario endpoints."""

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_student, get_db
from app.core.security import CurrentUser
from app.schemas.scenario import ScenarioDetailResponse, ScenarioSummaryResponse
from app.services import scenario_service

router = APIRouter(prefix="/scenarios", tags=["scenarios"])


@router.get("", response_model=list[ScenarioSummaryResponse])
async def list_scenarios(
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(get_current_student),
) -> list[ScenarioSummaryResponse]:
    return await scenario_service.list_scenarios(db)


@router.get("/{scenario_id}", response_model=ScenarioDetailResponse)
async def get_scenario(
    scenario_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(get_current_student),
) -> ScenarioDetailResponse:
    return await scenario_service.get_scenario(db, scenario_id)
