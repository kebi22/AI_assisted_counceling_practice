"""Evaluation workflow: validate, score via Gemini, persist."""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.evaluation_agent import EvaluationAgent, evaluation_agent
from app.ai.prompts.module1_evaluator import MODULE1_EVALUATOR_PROMPT_VERSION
from app.core.config import settings
from app.core.constants import SessionStatus
from app.core.exceptions import (
    AuthorizationError,
    MinimumMessagesError,
    ResourceNotFoundError,
    SessionStateError,
)
from app.core.logging import get_logger
from app.core.security import CurrentUser
from app.crud import evaluation as evaluation_crud
from app.crud import scenario_version as scenario_version_crud
from app.crud import simulation_session as session_crud
from app.db.models.simulation_session import SimulationSession
from app.schemas.evaluation import EvaluationResponse
from app.services import scenario_service
from app.services.evaluation_context import build_simulation_fidelity, compact_state_history
from app.services.support import build_transcript, resolve_user

logger = get_logger(__name__)


class EvaluationService:
    """Coordinates session evaluation, ensuring idempotency and valid output."""

    def __init__(self, agent: EvaluationAgent | None = None) -> None:
        self._agent = agent or evaluation_agent

    async def evaluate_session(
        self,
        db: AsyncSession,
        student: CurrentUser,
        session_id: uuid.UUID,
    ) -> EvaluationResponse:
        student_row = await resolve_user(db, student)
        session = await session_crud.get_session_with_messages(db, session_id)
        self._require_owned_session(session, student_row.id)
        assert session is not None

        # Idempotency: if an evaluation already exists, return it.
        if session.evaluation is not None:
            return EvaluationResponse.model_validate(session.evaluation)

        if session.student_message_count < settings.min_student_messages:
            raise MinimumMessagesError(
                f"At least {settings.min_student_messages} student messages are "
                "required before evaluation."
            )
        if session.status not in (SessionStatus.COMPLETED, SessionStatus.FAILED):
            raise SessionStateError("The session must be completed before evaluation.")

        scenario = await scenario_service.get_scenario_model(db, session.scenario_id)
        scenario_version = None
        if session.scenario_version_id is not None:
            scenario_version = await scenario_version_crud.get_scenario_version_by_id(
                db, session.scenario_version_id
            )
        template_metadata = {
            "template_key": (
                scenario_version.template_key if scenario_version else scenario.template_key
            ),
            "template_version": (
                scenario_version.template_version if scenario_version else scenario.template_version
            ),
            "rubric_version": scenario_version.rubric_version if scenario_version else "legacy",
            "output_schema_version": (
                scenario_version.output_schema_version if scenario_version else "1.0.0"
            ),
            "scenario_version_id": str(scenario_version.id) if scenario_version else None,
        }
        if scenario_version:
            template_metadata["competency_scale"] = scenario_version.authoring_snapshot.get(
                "competency_scale", []
            )
            template_metadata["evaluation_focus_sections"] = (
                scenario_version.authoring_snapshot.get("evaluation_focus_sections", [])
            )
            template_metadata["reflection_questions"] = scenario_version.authoring_snapshot.get(
                "reflection_questions", []
            )
        rubric = scenario_version.rubric_snapshot if scenario_version else scenario.rubric_json
        evaluator_prompt = (
            scenario_version.rendered_evaluator_prompt if scenario_version else None
        )
        learning_objectives = (
            scenario_version.learning_objectives_snapshot
            if scenario_version
            else scenario.learning_objectives or []
        )
        state_history = compact_state_history(
            session.state.state_history if session.state else []
        )
        simulation_fidelity = build_simulation_fidelity(
            state_history,
            progression_beats=(
                scenario_version.authoring_snapshot.get("progression_beats", [])
                if scenario_version
                else scenario.progression_beats or []
            ),
        )

        # Mark evaluating and commit so the state is visible if the AI call is slow.
        await session_crud.update_session_status(db, session, SessionStatus.EVALUATING)
        await db.commit()

        transcript = build_transcript(
            session,
            client_name=scenario.client_name or "Client",
        )
        try:
            result = await self._agent.evaluate(
                transcript=transcript,
                rubric=rubric,
                system_prompt=evaluator_prompt,
                template_metadata=template_metadata,
                learning_objectives=learning_objectives,
                state_history=state_history,
                simulation_fidelity=simulation_fidelity,
                session_id=str(session.id),
            )
        except Exception:
            # Return the session to completed so evaluation can be retried.
            await session_crud.update_session_status(db, session, SessionStatus.COMPLETED)
            await db.commit()
            logger.exception("Evaluation failed for session_id=%s", session.id)
            raise

        result.specialized_analyses = {
            **result.specialized_analyses,
            "simulation_fidelity": simulation_fidelity,
        }

        evaluation = await evaluation_crud.create_evaluation(
            db,
            session_id=session.id,
            scenario_version_id=session.scenario_version_id,
            template_key=template_metadata["template_key"],
            template_version=template_metadata["template_version"],
            rubric_version=template_metadata["rubric_version"],
            output_schema_version=template_metadata["output_schema_version"],
            overall_score=result.overall_score,
            rubric_scores={
                key: score.model_dump() for key, score in result.rubric_scores.items()
            },
            strengths=result.strengths,
            areas_for_growth=result.areas_for_growth,
            evidence_from_transcript=[e.model_dump() for e in result.evidence_from_transcript],
            suggested_improved_response=result.suggested_improved_response,
            specialized_analyses=result.specialized_analyses,
            missed_opportunities=result.missed_opportunities,
            faculty_review_recommended=result.faculty_review_recommended,
            model_name=settings.gemini_evaluator_model,
            prompt_version=(
                scenario_version.prompt_version
                if scenario_version
                else MODULE1_EVALUATOR_PROMPT_VERSION
            ),
            raw_response=result.model_dump(),
        )
        await session_crud.update_session_status(db, session, SessionStatus.EVALUATED)
        await db.commit()
        await db.refresh(evaluation)

        return EvaluationResponse.model_validate(evaluation)

    async def get_evaluation(
        self,
        db: AsyncSession,
        student: CurrentUser,
        session_id: uuid.UUID,
    ) -> EvaluationResponse:
        student_row = await resolve_user(db, student)
        session = await session_crud.get_session_by_id(db, session_id)
        self._require_owned_session(session, student_row.id)

        evaluation = await evaluation_crud.get_evaluation_by_session_id(db, session_id)
        if evaluation is None:
            raise ResourceNotFoundError("No evaluation exists for this session yet.")
        return EvaluationResponse.model_validate(evaluation)

    @staticmethod
    def _require_owned_session(
        session: SimulationSession | None, student_id: uuid.UUID
    ) -> None:
        if session is None:
            raise ResourceNotFoundError("Session not found.")
        if session.student_id != student_id:
            raise AuthorizationError("You do not have access to this session.")


evaluation_service = EvaluationService()
