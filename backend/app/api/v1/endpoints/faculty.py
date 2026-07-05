"""Faculty endpoints. All require a faculty principal."""

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_faculty, get_db
from app.core.security import CurrentUser
from app.schemas.faculty_review import FacultyReviewCreate, FacultyReviewResponse
from app.schemas.session import FacultySessionDetail, FacultySessionSummary
from app.services.faculty_service import faculty_service

router = APIRouter(prefix="/faculty", tags=["faculty"])


@router.get("/sessions", response_model=list[FacultySessionSummary])
async def list_faculty_sessions(
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(get_current_faculty),
) -> list[FacultySessionSummary]:
    return await faculty_service.list_sessions_for_faculty(db)


@router.get("/sessions/{session_id}", response_model=FacultySessionDetail)
async def get_faculty_session(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(get_current_faculty),
) -> FacultySessionDetail:
    return await faculty_service.get_session_for_faculty(db, session_id)


@router.post("/sessions/{session_id}/review", response_model=FacultyReviewResponse)
async def review_faculty_session(
    session_id: uuid.UUID,
    payload: FacultyReviewCreate,
    db: AsyncSession = Depends(get_db),
    faculty: CurrentUser = Depends(get_current_faculty),
) -> FacultyReviewResponse:
    return await faculty_service.review_session(db, faculty, session_id, payload)
