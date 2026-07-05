"""Central Version 1 API router."""

from fastapi import APIRouter

from app.api.v1.endpoints import (
    evaluations,
    faculty,
    faculty_scenarios,
    health,
    scenarios,
    sessions,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(scenarios.router)
api_router.include_router(sessions.router)
api_router.include_router(evaluations.router)
api_router.include_router(faculty.router)
api_router.include_router(faculty_scenarios.router)
api_router.include_router(faculty_scenarios.templates_router)
