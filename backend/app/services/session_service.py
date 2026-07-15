"""Simulation session workflows: start, message exchange, completion."""

from __future__ import annotations

import base64
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.output_models import ConversationMessage
from app.ai.scenario_agent import ScenarioAgent, scenario_agent
from app.ai.skill_classifier_agent import SkillClassifierAgent, skill_classifier_agent
from app.ai.speech import SpeechAdapter, speech_adapter
from app.core.config import settings
from app.core.constants import Modality, SessionStatus, Speaker
from app.core.exceptions import (
    AuthorizationError,
    MessageLimitError,
    ResourceNotFoundError,
    SessionStateError,
    ValidationError,
)
from app.core.logging import get_logger
from app.core.security import CurrentUser
from app.crud import message as message_crud
from app.crud import session_state as session_state_crud
from app.crud import simulation_session as session_crud
from app.db.models.message import Message
from app.db.models.simulation_session import SimulationSession
from app.crud import scenario as scenario_crud
from app.schemas.audio import SendAudioMessageResponse
from app.schemas.message import MessageResponse, SendMessageResponse
from app.schemas.session import SessionDetailResponse, StudentSessionSummary
from app.services.turn_pipeline_service import TurnPipelineResult
from app.services import scenario_service
from app.services.scenario_authoring_service import ScenarioAuthoringService
from app.services.state_transition_service import (
    StateTransitionService,
    state_transition_service,
)
from app.services.turn_pipeline_service import TurnPipelineService
from app.services.support import build_session_detail, resolve_user
from app.scenario_templates import get_template

logger = get_logger(__name__)


class SessionService:
    """Coordinates the student simulation lifecycle."""

    def __init__(
        self,
        agent: ScenarioAgent | None = None,
        classifier: SkillClassifierAgent | None = None,
        transition_service: StateTransitionService | None = None,
        turn_pipeline: TurnPipelineService | None = None,
        speech: SpeechAdapter | None = None,
    ) -> None:
        self._agent = agent or scenario_agent
        self._classifier = classifier or skill_classifier_agent
        self._transition_service = transition_service or state_transition_service
        self._turn_pipeline = turn_pipeline or TurnPipelineService(
            agent=self._agent,
            classifier=self._classifier,
            transition_service=self._transition_service,
        )
        self._speech = speech or speech_adapter

    async def start_session(
        self,
        db: AsyncSession,
        student: CurrentUser,
        scenario_id: uuid.UUID,
        modality: Modality = Modality.TEXT,
    ) -> SessionDetailResponse:
        """Create a session and seed the first AI-client message."""
        student_row = await resolve_user(db, student)
        scenario = await scenario_service.get_scenario_model(db, scenario_id)

        session = await session_crud.create_session(
            db,
            student_id=student_row.id,
            scenario_id=scenario.id,
            scenario_version_id=scenario.current_version_id,
            modality=modality,
        )
        template = get_template(scenario.template_key)
        state = await session_state_crud.create_session_state(
            db,
            session_id=session.id,
            initial_state=template.initial_state(
                ScenarioAuthoringService._authoring_from_row(scenario)
            ),
        )

        first_message = scenario.client_profile.get("first_client_message")
        if first_message:
            self._turn_pipeline.initialize_opening_state(
                state=state,
                scenario=ScenarioAuthoringService._authoring_from_row(scenario),
                opening_message=first_message,
            )
            await message_crud.create_message(
                db,
                session_id=session.id,
                speaker=Speaker.CLIENT,
                content=first_message,
                sequence_number=1,
            )

        await db.commit()

        loaded = await session_crud.get_session_with_messages(db, session.id)
        assert loaded is not None
        return await build_session_detail(db, loaded)

    async def send_student_message(
        self,
        db: AsyncSession,
        student: CurrentUser,
        session_id: uuid.UUID,
        content: str,
    ) -> SendMessageResponse:
        """Persist the student text message, generate and persist the client reply."""
        student_row = await resolve_user(db, student)
        session = await session_crud.get_session_with_messages(db, session_id)
        self._require_owned_active_session(session, student_row.id)
        assert session is not None
        self._require_room_for_turn(session)

        client_message, _ = await self._exchange_turn(db, session=session, content=content)
        return SendMessageResponse(
            session_id=session.id,
            message=MessageResponse.model_validate(client_message),
        )

    async def send_student_audio_message(
        self,
        db: AsyncSession,
        student: CurrentUser,
        session_id: uuid.UUID,
        audio_bytes: bytes,
        mime_type: str,
    ) -> SendAudioMessageResponse:
        """Transcribe a spoken student turn, run the SAME text pipeline, speak the reply.

        Speech is only an I/O layer here: the audio is transcribed to text at the
        edge, the deterministic turn pipeline runs unchanged, and the client's
        text reply is synthesized back to audio.
        """
        student_row = await resolve_user(db, student)
        session = await session_crud.get_session_with_messages(db, session_id)
        self._require_owned_active_session(session, student_row.id)
        assert session is not None
        if session.modality not in (Modality.AUDIO, Modality.VIDEO):
            raise ValidationError("This session is not an audio or video session.")
        self._require_room_for_turn(session)

        if not audio_bytes:
            raise ValidationError("No audio was received.")
        if len(audio_bytes) > settings.audio_turn_max_bytes:
            raise ValidationError("The audio clip is too large.")

        transcript = await self._speech.transcribe(
            audio_bytes=audio_bytes,
            mime_type=mime_type,
            session_id=str(session.id),
        )
        transcript = transcript.strip()
        if not transcript:
            raise ValidationError("Could not detect any speech in the audio.")

        client_message, pipeline_result = await self._exchange_turn(
            db, session=session, content=transcript
        )

        speech = await self._speech.synthesize(
            text=pipeline_result.client_text,
            session_id=str(session.id),
        )
        return SendAudioMessageResponse(
            session_id=session.id,
            transcript=transcript,
            message=MessageResponse.model_validate(client_message),
            audio_base64=base64.b64encode(speech.wav_bytes).decode("ascii"),
            audio_mime_type="audio/wav",
        )

    async def _exchange_turn(
        self,
        db: AsyncSession,
        *,
        session: SimulationSession,
        content: str,
    ) -> tuple[Message, TurnPipelineResult]:
        """Shared core turn: persist student text, run pipeline, persist client reply.

        Modality-agnostic. Text and audio both funnel through here so the state
        engine, disclosure gating, and validation behave identically.
        """
        scenario = await scenario_service.get_scenario_model(db, session.scenario_id)

        # 1. Save the student message.
        student_seq = await message_crud.get_next_sequence_number(db, session.id)
        await message_crud.create_message(
            db,
            session_id=session.id,
            speaker=Speaker.STUDENT,
            content=content,
            sequence_number=student_seq,
        )
        await session_crud.increment_student_message_count(db, session)

        # 2. Build ordered conversation history (including the new student turn).
        history = await message_crud.list_session_messages(db, session.id)
        conversation = [
            ConversationMessage(speaker=m.speaker, content=m.content) for m in history
        ]

        # 3. Load deterministic state for the analyzed client-turn pipeline.
        scenario_profile = ScenarioAuthoringService._authoring_from_row(scenario)
        state = session.state or await session_state_crud.get_session_state(db, session.id)
        if state is None:
            template = get_template(scenario.template_key)
            state = await session_state_crud.create_session_state(
                db,
                session_id=session.id,
                initial_state=template.initial_state(scenario_profile),
            )
        pipeline_result = await self._turn_pipeline.run_turn(
            db,
            state=state,
            scenario=scenario_profile,
            template_key=scenario.template_key,
            student_content=content,
            conversation=conversation,
            student_turn_count=session.student_message_count,
            client_name=scenario.client_name or "the client",
            session_id=str(session.id),
        )

        # 4. Save the validated AI-client message.
        client_seq = await message_crud.get_next_sequence_number(db, session.id)
        client_message = await message_crud.create_message(
            db,
            session_id=session.id,
            speaker=Speaker.CLIENT,
            content=pipeline_result.client_text,
            sequence_number=client_seq,
        )

        # 5. Commit the message, transition, response plan, and validation atomically.
        await db.commit()
        await db.refresh(client_message)
        return client_message, pipeline_result

    @staticmethod
    def _require_room_for_turn(session: SimulationSession) -> None:
        if session.student_message_count >= settings.max_session_messages:
            raise MessageLimitError("This session has reached its message limit.")

    async def complete_session(
        self,
        db: AsyncSession,
        student: CurrentUser,
        session_id: uuid.UUID,
        nonverbal_summary: dict | None = None,
    ) -> SessionDetailResponse:
        """Mark an active session as completed.

        For video sessions the frontend attaches an aggregated nonverbal
        metrics summary (computed in-browser via MediaPipe); it is stored on
        the session and later fed to the evaluator. Raw video never reaches
        the server.
        """
        student_row = await resolve_user(db, student)
        session = await session_crud.get_session_with_messages(db, session_id)
        self._require_owned_session(session, student_row.id)
        assert session is not None

        if session.status not in (SessionStatus.ACTIVE,):
            raise SessionStateError("Only an active session can be completed.")

        if nonverbal_summary is not None:
            if session.modality != Modality.VIDEO:
                raise ValidationError(
                    "Nonverbal metrics are only accepted for video sessions."
                )
            await session_crud.set_nonverbal_summary(db, session, nonverbal_summary)

        await session_crud.update_session_status(
            db, session, SessionStatus.COMPLETED, set_ended_at=True
        )
        await db.commit()

        loaded = await session_crud.get_session_with_messages(db, session.id)
        assert loaded is not None
        return await build_session_detail(db, loaded)

    async def list_my_sessions(
        self,
        db: AsyncSession,
        student: CurrentUser,
    ) -> list[StudentSessionSummary]:
        """List the current student's sessions, newest first."""
        student_row = await resolve_user(db, student)
        sessions = await session_crud.list_student_sessions(db, student_row.id)
        summaries: list[StudentSessionSummary] = []
        for session in sessions:
            scenario = await scenario_crud.get_scenario_by_id(db, session.scenario_id)
            summaries.append(
                StudentSessionSummary(
                    session_id=session.id,
                    scenario_title=scenario.title if scenario else "Unknown scenario",
                    status=session.status,
                    overall_score=(
                        session.evaluation.overall_score if session.evaluation else None
                    ),
                    created_at=session.created_at,
                    completed_at=session.ended_at,
                )
            )
        return summaries

    async def get_student_session(
        self,
        db: AsyncSession,
        student: CurrentUser,
        session_id: uuid.UUID,
    ) -> SessionDetailResponse:
        student_row = await resolve_user(db, student)
        session = await session_crud.get_session_with_messages(db, session_id)
        self._require_owned_session(session, student_row.id)
        assert session is not None
        return await build_session_detail(db, session)

    @staticmethod
    def _require_owned_session(
        session: SimulationSession | None, student_id: uuid.UUID
    ) -> None:
        if session is None:
            raise ResourceNotFoundError("Session not found.")
        if session.student_id != student_id:
            raise AuthorizationError("You do not have access to this session.")

    def _require_owned_active_session(
        self, session: SimulationSession | None, student_id: uuid.UUID
    ) -> None:
        self._require_owned_session(session, student_id)
        assert session is not None
        if session.status != SessionStatus.ACTIVE:
            raise SessionStateError("This session is no longer active.")


session_service = SessionService()
