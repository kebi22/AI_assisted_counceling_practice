"""CRUD operations for evaluations."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.evaluation import Evaluation


async def create_evaluation(db: AsyncSession, **fields: Any) -> Evaluation:
    evaluation = Evaluation(**fields)
    db.add(evaluation)
    await db.flush()
    return evaluation


async def get_evaluation_by_session_id(
    db: AsyncSession, session_id: uuid.UUID
) -> Evaluation | None:
    result = await db.execute(
        select(Evaluation).where(Evaluation.session_id == session_id)
    )
    return result.scalar_one_or_none()


async def evaluation_exists_for_session(db: AsyncSession, session_id: uuid.UUID) -> bool:
    result = await db.execute(
        select(Evaluation.id).where(Evaluation.session_id == session_id).limit(1)
    )
    return result.scalar_one_or_none() is not None
