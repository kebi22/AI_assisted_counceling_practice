"""CRUD helpers for per-session client state."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.session_state import SessionState


async def create_session_state(
    db: AsyncSession, *, session_id: uuid.UUID, initial_state: dict[str, Any]
) -> SessionState:
    state = SessionState(
        session_id=session_id,
        engagement_level=initial_state.get("engagement_level", 2),
        trust_level=initial_state.get("trust_level", 2),
        disclosure_stage=initial_state.get("disclosure_stage", 1),
        session_stage=initial_state.get("session_stage", "early"),
        emotional_depth=initial_state.get("emotional_depth", 1),
        rupture_count=initial_state.get("rupture_count", 0),
        repair_count=initial_state.get("repair_count", 0),
        revealed_information=initial_state.get("revealed_information", []),
        emotional_cues=initial_state.get("emotional_cues", []),
        beat_states=initial_state.get("beat_states", []),
        state_history=initial_state.get("state_history", []),
    )
    db.add(state)
    await db.flush()
    return state


async def get_session_state(
    db: AsyncSession, session_id: uuid.UUID
) -> SessionState | None:
    result = await db.execute(
        select(SessionState).where(SessionState.session_id == session_id)
    )
    return result.scalar_one_or_none()
