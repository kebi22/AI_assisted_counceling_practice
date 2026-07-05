"""CRUD operations for messages."""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import Speaker
from app.db.models.message import Message


async def get_next_sequence_number(db: AsyncSession, session_id: uuid.UUID) -> int:
    result = await db.execute(
        select(func.coalesce(func.max(Message.sequence_number), 0)).where(
            Message.session_id == session_id
        )
    )
    current_max = result.scalar_one()
    return int(current_max) + 1


async def create_message(
    db: AsyncSession,
    *,
    session_id: uuid.UUID,
    speaker: Speaker,
    content: str,
    sequence_number: int,
) -> Message:
    message = Message(
        session_id=session_id,
        speaker=speaker,
        content=content,
        sequence_number=sequence_number,
    )
    db.add(message)
    await db.flush()
    return message


async def list_session_messages(db: AsyncSession, session_id: uuid.UUID) -> list[Message]:
    result = await db.execute(
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.sequence_number)
    )
    return list(result.scalars().all())
