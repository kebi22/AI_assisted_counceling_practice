"""CRUD operations for faculty reviews."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import ReviewStatus, SessionStatus
from app.db.models.faculty_review import FacultyReview
from app.db.models.simulation_session import SimulationSession


async def get_review_by_session_id(
    db: AsyncSession, session_id: uuid.UUID
) -> FacultyReview | None:
    result = await db.execute(
        select(FacultyReview).where(FacultyReview.session_id == session_id)
    )
    return result.scalar_one_or_none()


async def create_or_update_review(
    db: AsyncSession,
    *,
    session_id: uuid.UUID,
    faculty_id: uuid.UUID,
    comments: str,
    adjusted_score: float | None,
    review_status: ReviewStatus,
) -> FacultyReview:
    review = await get_review_by_session_id(db, session_id)
    if review is None:
        review = FacultyReview(session_id=session_id, faculty_id=faculty_id)
        db.add(review)

    review.faculty_id = faculty_id
    review.comments = comments
    review.adjusted_score = adjusted_score
    review.review_status = review_status
    if review_status == ReviewStatus.REVIEWED:
        review.reviewed_at = datetime.now(timezone.utc)
    await db.flush()
    return review


async def mark_session_reviewed(
    db: AsyncSession, session: SimulationSession
) -> SimulationSession:
    session.status = SessionStatus.REVIEWED
    await db.flush()
    return session
