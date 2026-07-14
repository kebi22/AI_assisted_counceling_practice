"""Faculty workflows: list sessions, view detail, submit reviews."""

from __future__ import annotations

from typing import Any
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.evaluation_agent import EvaluationAgent
from app.ai.output_models import ConversationMessage
from app.ai.runtime_context_builder import build_runtime_client_context
from app.ai.scenario_agent import ScenarioAgent
from app.core.constants import FACULTY_VISIBLE_STATUSES, ReviewStatus, Speaker
from app.core.exceptions import ResourceNotFoundError
from app.core.security import CurrentUser
from app.crud import faculty_review as review_crud
from app.crud import scenario as scenario_crud
from app.crud import scenario_version as scenario_version_crud
from app.crud import simulation_session as session_crud
from app.crud import user as user_crud
from app.db.models.session_state import SessionState
from app.db.models.simulation_session import SimulationSession
from app.schemas.faculty_review import FacultyReviewCreate, FacultyReviewResponse
from app.schemas.session import FacultySessionDetail, FacultySessionSummary
from app.services.evaluation_context import build_simulation_fidelity, compact_state_history
from app.services.support import build_session_detail, resolve_user


class FacultyService:
    """Coordinates faculty review workflows."""

    async def list_sessions_for_faculty(
        self, db: AsyncSession
    ) -> list[FacultySessionSummary]:
        sessions = await session_crud.list_completed_sessions(db, FACULTY_VISIBLE_STATUSES)
        summaries: list[FacultySessionSummary] = []
        for session in sessions:
            scenario = await scenario_crud.get_scenario_by_id(db, session.scenario_id)
            student = await user_crud.get_user_by_id(db, session.student_id)
            summaries.append(
                FacultySessionSummary(
                    session_id=session.id,
                    student_name=student.name if student else "Unknown student",
                    scenario_title=scenario.title if scenario else "Unknown scenario",
                    status=session.status,
                    overall_score=(
                        session.evaluation.overall_score if session.evaluation else None
                    ),
                    completed_at=session.ended_at,
                    review_status=(
                        session.faculty_review.review_status
                        if session.faculty_review
                        else None
                    ),
                )
            )
        return summaries

    async def get_session_for_faculty(
        self, db: AsyncSession, session_id: uuid.UUID
    ) -> FacultySessionDetail:
        session = await session_crud.get_session_with_messages(db, session_id)
        if session is None:
            raise ResourceNotFoundError("Session not found.")

        detail = await build_session_detail(db, session)
        review = session.faculty_review
        return FacultySessionDetail(
            **detail.model_dump(),
            faculty_comment=review.comments if review else "",
            review_status=review.review_status if review else None,
            adjusted_score=review.adjusted_score if review else None,
            prompt_trace=await self._build_prompt_trace(db, session),
        )

    async def review_session(
        self,
        db: AsyncSession,
        faculty: CurrentUser,
        session_id: uuid.UUID,
        payload: FacultyReviewCreate,
    ) -> FacultyReviewResponse:
        faculty_row = await resolve_user(db, faculty)
        session = await session_crud.get_session_by_id(db, session_id)
        if session is None:
            raise ResourceNotFoundError("Session not found.")

        review = await review_crud.create_or_update_review(
            db,
            session_id=session.id,
            faculty_id=faculty_row.id,
            comments=payload.comments,
            adjusted_score=payload.adjusted_score,
            review_status=payload.review_status,
        )
        if payload.review_status == ReviewStatus.REVIEWED:
            await review_crud.mark_session_reviewed(db, session)

        await db.commit()
        await db.refresh(review)
        return FacultyReviewResponse.model_validate(review)

    async def _build_prompt_trace(
        self, db: AsyncSession, session: SimulationSession
    ) -> dict[str, Any] | None:
        scenario = await scenario_crud.get_scenario_by_id(db, session.scenario_id)
        if scenario is None:
            return None

        scenario_version = None
        if session.scenario_version_id is not None:
            scenario_version = await scenario_version_crud.get_scenario_version_by_id(
                db, session.scenario_version_id
            )
        base_client_prompt = (
            scenario_version.rendered_client_prompt
            if scenario_version
            else scenario.system_prompt
        )
        if not base_client_prompt:
            return None

        client_name = scenario.client_name or "Client"
        state_history = session.state.state_history if session.state else []
        if state_history and state_history[-1].get("client_persona_prompt_text"):
            base_client_prompt = state_history[-1]["client_persona_prompt_text"]
        turn_traces: list[dict[str, Any]] = []
        student_turn_index = 0
        for message in session.messages:
            if message.speaker != Speaker.STUDENT:
                continue
            student_turn_index += 1
            event = self._state_event_for_turn(state_history, student_turn_index)
            runtime_state = self._session_state_from_event(event)
            allowed_disclosures = list(event.get("allowed_disclosures") or [])
            runtime_context = event.get("runtime_context_text") or build_runtime_client_context(
                state=runtime_state, allowed_disclosures=allowed_disclosures
            )
            conversation = [
                ConversationMessage(speaker=m.speaker, content=m.content)
                for m in session.messages
                if m.sequence_number <= message.sequence_number
            ]
            turn_traces.append(
                {
                    "student_turn_count": student_turn_index,
                    "student_message": message.content,
                    "detected_behaviors": event.get("detected_behaviors", []),
                    "counselor_analysis": event.get("counselor_analysis"),
                    "cue_response_analysis": event.get("cue_response_analysis"),
                    "expected_client_reactions": event.get(
                        "expected_client_reactions", []
                    ),
                    "engagement_delta": event.get("engagement_delta", 0),
                    "trust_delta": event.get("trust_delta", 0),
                    "engagement_level": runtime_state.engagement_level,
                    "trust_level": runtime_state.trust_level,
                    "disclosure_stage": runtime_state.disclosure_stage,
                    "session_stage": runtime_state.session_stage,
                    "stage_gate": event.get("stage_gate"),
                    "allowed_disclosures": allowed_disclosures,
                    "response_plan": event.get("response_plan"),
                    "validation": event.get("validation"),
                    "generation_attempts": event.get("generation_attempts", []),
                    "revealed_information": event.get("revealed_information", []),
                    "emotional_cues": event.get("emotional_cues", []),
                    "beat_states": event.get("beat_states", []),
                    "runtime_context_text": runtime_context,
                    "client_stateful_system_prompt_text": event.get(
                        "client_stateful_system_prompt_text"
                    ) or f"{base_client_prompt.rstrip()}\n\n{runtime_context}",
                    "client_conversation_prompt_text": event.get(
                        "client_conversation_prompt_text"
                    ) or ScenarioAgent._build_prompt(conversation, client_name=client_name),
                }
            )

        final_event = state_history[-1] if state_history else {}
        final_state = self._session_state_from_event(final_event)
        final_runtime_context = final_event.get(
            "runtime_context_text"
        ) or build_runtime_client_context(
            state=final_state,
            allowed_disclosures=list(final_event.get("allowed_disclosures") or []),
        )
        final_conversation = [
            ConversationMessage(speaker=m.speaker, content=m.content)
            for m in session.messages
        ]
        evaluator_system_prompt = (
            scenario_version.rendered_evaluator_prompt
            if scenario_version
            else ""
        )
        rubric_snapshot = (
            scenario_version.rubric_snapshot
            if scenario_version
            else scenario.rubric_json
        )
        learning_objectives = (
            scenario_version.learning_objectives_snapshot
            if scenario_version
            else scenario.learning_objectives or []
        )
        template_metadata = {
            "template_key": (
                scenario_version.template_key
                if scenario_version
                else scenario.template_key
            ),
            "template_version": (
                scenario_version.template_version
                if scenario_version
                else scenario.template_version
            ),
            "rubric_version": (
                scenario_version.rubric_version if scenario_version else "legacy"
            ),
            "output_schema_version": (
                scenario_version.output_schema_version if scenario_version else "1.0.0"
            ),
            "scenario_version_id": str(scenario_version.id) if scenario_version else None,
        }
        if scenario_version:
            template_metadata["competency_scale"] = (
                scenario_version.authoring_snapshot.get("competency_scale", [])
            )
            template_metadata["evaluation_focus_sections"] = (
                scenario_version.authoring_snapshot.get(
                    "evaluation_focus_sections", []
                )
            )
            template_metadata["reflection_questions"] = (
                scenario_version.authoring_snapshot.get("reflection_questions", [])
            )
        transcript = self._conversation_transcript(
            final_conversation,
            client_name=client_name,
        )
        simulation_fidelity = build_simulation_fidelity(
            compact_state_history(state_history),
            progression_beats=(
                scenario_version.authoring_snapshot.get("progression_beats", [])
                if scenario_version
                else scenario.progression_beats or []
            ),
        )
        evaluator_user_prompt = EvaluationAgent._build_prompt(
            transcript=transcript,
            rubric=rubric_snapshot,
            template_metadata=template_metadata,
            learning_objectives=learning_objectives,
            state_history=compact_state_history(state_history),
            simulation_fidelity=simulation_fidelity,
        )
        return {
            "base_client_prompt_text": base_client_prompt,
            "latest_runtime_context_text": final_runtime_context,
            "latest_client_stateful_system_prompt_text": (
                final_event.get("client_stateful_system_prompt_text")
                or f"{base_client_prompt.rstrip()}\n\n{final_runtime_context}"
            ),
            "latest_client_conversation_prompt_text": final_event.get(
                "client_conversation_prompt_text"
            ) or ScenarioAgent._build_prompt(final_conversation, client_name=client_name),
            "evaluation_transcript_text": transcript,
            "evaluator_system_prompt_text": evaluator_system_prompt,
            "evaluator_user_prompt_text": evaluator_user_prompt,
            "final_evaluation_prompt_text": (
                evaluator_system_prompt.strip()
                + "\n\nEVALUATOR USER PROMPT\n"
                + evaluator_user_prompt
            ),
            "state_history": state_history,
            "simulation_fidelity": simulation_fidelity,
            "turn_traces": turn_traces,
        }

    @staticmethod
    def _state_event_for_turn(
        state_history: list[dict[str, Any]], student_turn_index: int
    ) -> dict[str, Any]:
        for event in state_history:
            if event.get("turn") == student_turn_index:
                return event
        return state_history[-1] if state_history else {}

    @staticmethod
    def _session_state_from_event(event: dict[str, Any]) -> SessionState:
        state_after = event.get("state_after") or {}
        return SessionState(
            engagement_level=int(
                state_after.get("engagement_level") or event.get("engagement_level") or 1
            ),
            trust_level=int(state_after.get("trust_level") or event.get("trust_level") or 1),
            disclosure_stage=int(
                state_after.get("disclosure_stage") or event.get("disclosure_stage") or 1
            ),
            session_stage=str(
                state_after.get("session_stage") or event.get("session_stage") or "early"
            ),
            revealed_information=list(
                state_after.get("revealed_information")
                or event.get("revealed_information")
                or []
            ),
            emotional_cues=list(
                state_after.get("emotional_cues") or event.get("emotional_cues") or []
            ),
            beat_states=list(
                state_after.get("beat_states") or event.get("beat_states") or []
            ),
            emotional_depth=int(
                state_after.get("emotional_depth") or event.get("emotional_depth") or 1
            ),
            rupture_count=int(
                state_after.get("rupture_count") or event.get("rupture_count") or 0
            ),
            repair_count=int(
                state_after.get("repair_count") or event.get("repair_count") or 0
            ),
            state_history=[],
        )

    @staticmethod
    def _conversation_transcript(
        conversation: list[ConversationMessage],
        *,
        client_name: str,
    ) -> str:
        lines: list[str] = []
        for turn in conversation:
            if turn.speaker == Speaker.STUDENT:
                label = "Counselor (student)"
            elif turn.speaker == Speaker.CLIENT:
                label = f"Client ({client_name})"
            else:
                label = "System"
            lines.append(f"{label}: {turn.content}")
        return "\n".join(lines)


faculty_service = FacultyService()
