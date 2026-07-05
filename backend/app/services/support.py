"""Shared service helpers: user resolution and response assembly."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import Speaker
from app.core.exceptions import ResourceNotFoundError
from app.core.security import CurrentUser
from app.crud import scenario as scenario_crud
from app.crud import user as user_crud
from app.db.models.simulation_session import SimulationSession
from app.db.models.user import User
from app.schemas.evaluation import EvaluationResponse
from app.schemas.message import MessageResponse
from app.schemas.session import SessionDetailResponse


async def resolve_user(db: AsyncSession, current_user: CurrentUser) -> User:
    """Resolve the mock ``CurrentUser`` to a persisted ``User`` row."""
    user = await user_crud.get_user_by_email(db, current_user.email)
    if user is None:
        raise ResourceNotFoundError(
            "The current user has not been provisioned. Run the seed script."
        )
    return user


def evaluation_to_response(session: SimulationSession) -> EvaluationResponse | None:
    if session.evaluation is None:
        return None
    return EvaluationResponse.model_validate(session.evaluation)


async def build_session_detail(
    db: AsyncSession,
    session: SimulationSession,
) -> SessionDetailResponse:
    """Assemble a full session detail response from an ORM session.

    The session must already have ``messages`` and ``evaluation`` loaded.
    """
    scenario = await scenario_crud.get_scenario_by_id(db, session.scenario_id)
    student = await user_crud.get_user_by_id(db, session.student_id)

    return SessionDetailResponse(
        id=session.id,
        student_id=session.student_id,
        scenario_id=session.scenario_id,
        scenario_version_id=session.scenario_version_id,
        status=session.status,
        student_message_count=session.student_message_count,
        started_at=session.started_at,
        ended_at=session.ended_at,
        created_at=session.created_at,
        scenario_title=scenario.title if scenario else "Unknown scenario",
        client_name=scenario.client_name if scenario else "Client",
        student_name=student.name if student else "Unknown student",
        messages=[MessageResponse.model_validate(m) for m in session.messages],
        evaluation=evaluation_to_response(session),
    )


def build_transcript(session: SimulationSession, *, client_name: str = "Client") -> str:
    """Render an ordered, labelled transcript for evaluation."""
    lines: list[str] = []
    for message in session.messages:
        if message.speaker == Speaker.STUDENT:
            label = "Counselor (student)"
        elif message.speaker == Speaker.CLIENT:
            label = f"Client ({client_name})"
        else:
            label = "System"
        lines.append(f"{label}: {message.content}")
    return "\n".join(lines)
