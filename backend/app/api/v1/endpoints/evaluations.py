"""Evaluation endpoints. The POST endpoint is idempotent."""

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_student, get_db
from app.core.security import CurrentUser
from app.schemas.evaluation import EvaluationResponse
from app.services.evaluation_service import evaluation_service

router = APIRouter(prefix="/sessions", tags=["evaluations"])


@router.post("/{session_id}/evaluation", response_model=EvaluationResponse)
async def create_evaluation(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    student: CurrentUser = Depends(get_current_student),
) -> EvaluationResponse:
    """Evaluate a completed session.

    Idempotent: if an evaluation already exists it is returned unchanged.
    """
    return await evaluation_service.evaluate_session(db, student, session_id)


@router.get("/{session_id}/evaluation", response_model=EvaluationResponse)
async def get_evaluation(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    student: CurrentUser = Depends(get_current_student),
) -> EvaluationResponse:
    return await evaluation_service.get_evaluation(db, student, session_id)
