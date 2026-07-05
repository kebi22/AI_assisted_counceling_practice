"""Faculty scenario authoring endpoints. All require a faculty principal."""

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_faculty, get_db
from app.core.security import CurrentUser
from app.schemas.scenario_authoring import (
    FacultyScenarioDetail,
    FacultyScenarioSummary,
    ScenarioAuthoringInput,
    ScenarioPreviewResponse,
    ScenarioPublishResponse,
    ScenarioTestMessageRequest,
    ScenarioTestMessageResponse,
    ScenarioTemplateResponse,
)
from app.services.scenario_authoring_service import scenario_authoring_service

router = APIRouter(prefix="/faculty/scenarios", tags=["faculty-scenarios"])
templates_router = APIRouter(prefix="/faculty/scenario-templates", tags=["faculty-scenarios"])


@templates_router.get("", response_model=list[ScenarioTemplateResponse])
async def list_scenario_templates(
    _: CurrentUser = Depends(get_current_faculty),
) -> list[ScenarioTemplateResponse]:
    return await scenario_authoring_service.list_templates()


@router.get("", response_model=list[FacultyScenarioSummary])
async def list_scenarios(
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(get_current_faculty),
) -> list[FacultyScenarioSummary]:
    return await scenario_authoring_service.list_scenarios(db)


@router.post("", response_model=FacultyScenarioDetail, status_code=status.HTTP_201_CREATED)
async def create_scenario(
    payload: ScenarioAuthoringInput,
    db: AsyncSession = Depends(get_db),
    faculty: CurrentUser = Depends(get_current_faculty),
) -> FacultyScenarioDetail:
    return await scenario_authoring_service.create_draft(db, faculty, payload)


@router.get("/{scenario_id}", response_model=FacultyScenarioDetail)
async def get_scenario(
    scenario_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(get_current_faculty),
) -> FacultyScenarioDetail:
    return await scenario_authoring_service.get_scenario(db, scenario_id)


@router.patch("/{scenario_id}", response_model=FacultyScenarioDetail)
async def update_scenario(
    scenario_id: uuid.UUID,
    payload: ScenarioAuthoringInput,
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(get_current_faculty),
) -> FacultyScenarioDetail:
    return await scenario_authoring_service.update_draft(db, scenario_id, payload)


@router.post("/{scenario_id}/generate-preview", response_model=ScenarioPreviewResponse)
async def generate_preview(
    scenario_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(get_current_faculty),
) -> ScenarioPreviewResponse:
    return await scenario_authoring_service.generate_preview(db, scenario_id)


@router.post("/{scenario_id}/test-message", response_model=ScenarioTestMessageResponse)
async def test_message(
    scenario_id: uuid.UUID,
    payload: ScenarioTestMessageRequest,
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(get_current_faculty),
) -> ScenarioTestMessageResponse:
    return await scenario_authoring_service.test_message(db, scenario_id, payload)


@router.post("/{scenario_id}/publish", response_model=ScenarioPublishResponse)
async def publish_scenario(
    scenario_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    faculty: CurrentUser = Depends(get_current_faculty),
) -> ScenarioPublishResponse:
    return await scenario_authoring_service.publish_scenario(db, faculty, scenario_id)


@router.post("/{scenario_id}/duplicate", response_model=FacultyScenarioDetail)
async def duplicate_scenario(
    scenario_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    faculty: CurrentUser = Depends(get_current_faculty),
) -> FacultyScenarioDetail:
    return await scenario_authoring_service.duplicate_scenario(db, faculty, scenario_id)


@router.post("/{scenario_id}/deactivate", response_model=FacultyScenarioDetail)
async def deactivate_scenario(
    scenario_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(get_current_faculty),
) -> FacultyScenarioDetail:
    return await scenario_authoring_service.deactivate_scenario(db, scenario_id)
