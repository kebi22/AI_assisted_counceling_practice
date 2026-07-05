"""Faculty scenario authoring workflows.

Owns the lifecycle of faculty-authored scenarios: draft -> preview/generate ->
test -> publish. Structured faculty input is the source of truth; the generated
prompt is derived from it via the deterministic ``ScenarioPromptBuilder``.

On publish, the structured data is projected onto the legacy student-facing
columns (``system_prompt``, ``client_name``, ``client_profile``, ...) so the
existing simulation and evaluation pipelines run unchanged.
"""

from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.output_models import ConversationMessage
from app.ai.skill_classifier_agent import SUPPORTED_RUNTIME_BEHAVIOR_KEYS
from app.ai.evaluation_agent import EvaluationAgent
from app.ai.prompt_builder import ScenarioPromptBuilder, scenario_prompt_builder
from app.ai.prompts.module1_evaluator import MODULE1_RUBRIC
from app.ai.runtime_context_builder import build_runtime_client_context
from app.ai.scenario_agent import ScenarioAgent, scenario_agent
from app.core.constants import ScenarioStatus, Speaker
from app.core.exceptions import (
    ConflictError,
    ResourceNotFoundError,
    ValidationError,
)
from app.core.logging import get_logger
from app.core.security import CurrentUser
from app.crud import scenario as scenario_crud
from app.crud import scenario_version as scenario_version_crud
from app.db.models.scenario import Scenario
from app.db.models.session_state import SessionState
from app.schemas.scenario_authoring import (
    FacultyScenarioDetail,
    FacultyScenarioSummary,
    ScenarioAuthoringData,
    ScenarioPreviewResponse,
    ScenarioPublishResponse,
    ScenarioTestMessageRequest,
    ScenarioTestMessageResponse,
)
from app.scenario_templates import DEFAULT_TEMPLATE_KEY, get_template
from app.scenario_templates.registry import SCENARIO_TEMPLATE_REGISTRY
from app.services.evaluation_context import compact_state_history
from app.services.turn_pipeline_service import PreparedClientTurn, TurnPipelineService

logger = get_logger(__name__)

_SLUG_RE = re.compile(r"[^a-z0-9]+")
_EDITABLE_STATUSES = (
    ScenarioStatus.DRAFT,
    ScenarioStatus.READY_FOR_TESTING,
    ScenarioStatus.INACTIVE,
)


class ScenarioAuthoringService:
    def __init__(
        self,
        builder: ScenarioPromptBuilder | None = None,
        agent: ScenarioAgent | None = None,
    ) -> None:
        self._builder = builder or scenario_prompt_builder
        self._agent = agent or scenario_agent
        self._turn_pipeline = TurnPipelineService(agent=self._agent)

    # -- Reads --------------------------------------------------------------

    async def list_scenarios(self, db: AsyncSession) -> list[FacultyScenarioSummary]:
        rows = await scenario_crud.list_all_scenarios(db)
        return [FacultyScenarioSummary.model_validate(r) for r in rows]

    async def list_templates(self) -> list[dict]:
        templates = []
        for template in SCENARIO_TEMPLATE_REGISTRY.values():
            templates.append(
                {
                    "key": template.key,
                    "version": template.version,
                    "display_name": template.display_name,
                    "supported_modalities": template.supported_modalities,
                    "output_schema_version": template.output_schema_version,
                    "default_rubric": template.default_rubric(),
                    "default_safety_policy": template.default_safety_policy(),
                    "content": template.template_content(),
                }
            )
        return templates

    async def get_scenario(
        self, db: AsyncSession, scenario_id: uuid.UUID
    ) -> FacultyScenarioDetail:
        row = await self._get_or_404(db, scenario_id)
        return FacultyScenarioDetail.model_validate(row)

    # -- Draft create / update ---------------------------------------------

    async def create_draft(
        self, db: AsyncSession, faculty: CurrentUser, data: ScenarioAuthoringData
    ) -> FacultyScenarioDetail:
        slug = await self._unique_slug(db, data.title)
        row = await scenario_crud.create_scenario(
            db,
            slug=slug,
            status=ScenarioStatus.DRAFT,
            is_active=False,
            created_by=faculty.email,
            template_key=DEFAULT_TEMPLATE_KEY,
            template_version=get_template(DEFAULT_TEMPLATE_KEY).version,
            client_name=data.client_identity.name,
            description=data.description or "",
            student_goal=self._derive_student_goal(data),
            **self._structured_fields(data),
        )
        await db.commit()
        await db.refresh(row)
        return FacultyScenarioDetail.model_validate(row)

    async def update_draft(
        self,
        db: AsyncSession,
        scenario_id: uuid.UUID,
        data: ScenarioAuthoringData,
    ) -> FacultyScenarioDetail:
        row = await self._get_or_404(db, scenario_id)
        self._require_editable(row)
        # Structured data changed: the prior generated prompt is now stale.
        await scenario_crud.update_scenario(
            db,
            row,
            status=ScenarioStatus.DRAFT,
            client_name=data.client_identity.name,
            description=data.description or "",
            student_goal=self._derive_student_goal(data),
            generated_prompt=None,
            prompt_version=None,
            prompt_generated_at=None,
            **self._structured_fields(data),
        )
        await db.commit()
        await db.refresh(row)
        return FacultyScenarioDetail.model_validate(row)

    # -- Prompt generation / preview ---------------------------------------

    async def generate_preview(
        self, db: AsyncSession, scenario_id: uuid.UUID
    ) -> ScenarioPreviewResponse:
        row = await self._get_or_404(db, scenario_id)
        data = self._authoring_from_row(row)
        generated = self._builder.build_client_prompt(data)
        template = get_template(row.template_key)
        rubric_snapshot = self._build_rubric_snapshot(data)
        evaluator_prompt = self._build_evaluator_preview_prompt(
            template.build_evaluator_prompt(
                [item.model_dump() for item in data.rubric],
                [objective.model_dump() for objective in data.learning_objectives],
            ),
            rubric_snapshot=rubric_snapshot,
            data=data,
            row=row,
        )

        new_status = row.status
        if row.status in (ScenarioStatus.DRAFT, ScenarioStatus.READY_FOR_TESTING):
            new_status = ScenarioStatus.READY_FOR_TESTING

        await scenario_crud.update_scenario(
            db,
            row,
            generated_prompt=generated.prompt_text,
            prompt_version=generated.prompt_version,
            prompt_generated_at=datetime.now(timezone.utc),
            status=new_status,
        )
        await db.commit()
        return ScenarioPreviewResponse(
            status=new_status,
            prompt_text=generated.prompt_text,
            evaluator_prompt_text=evaluator_prompt,
            prompt_version=generated.prompt_version,
            warnings=generated.warnings,
        )

    # -- Test conversation --------------------------------------------------

    async def test_message(
        self,
        db: AsyncSession,
        scenario_id: uuid.UUID,
        payload: ScenarioTestMessageRequest,
    ) -> ScenarioTestMessageResponse:
        row = await self._get_or_404(db, scenario_id)
        data = self._authoring_from_row(row)
        conversation = [
            ConversationMessage(
                speaker=Speaker.STUDENT if t.speaker == "student" else Speaker.CLIENT,
                content=t.content,
            )
            for t in payload.history
        ]
        conversation.append(
            ConversationMessage(speaker=Speaker.STUDENT, content=payload.content)
        )
        trace, prepared, state = await self._build_test_trace(
            row=row,
            data=data,
            conversation=conversation,
            client_name=row.client_name or "the client",
        )
        pipeline_result = await self._turn_pipeline.generate_prepared_turn(
            prepared=prepared,
            scenario=data,
            conversation=conversation,
            client_name=row.client_name or "the client",
            session_id=f"test-{scenario_id}",
        )
        reply = pipeline_result.client_text
        latest_event = state.state_history[-1]
        trace["state_history"] = state.state_history
        trace["latest_runtime_context_text"] = latest_event["runtime_context_text"]
        trace["latest_client_stateful_system_prompt_text"] = latest_event[
            "client_stateful_system_prompt_text"
        ]
        trace["latest_client_conversation_prompt_text"] = latest_event[
            "client_conversation_prompt_text"
        ]
        trace["turn_traces"][-1] = self._turn_trace(
            prepared=prepared,
            event=latest_event,
            student_message=payload.content,
        )
        trace["debug_state"] = self._debug_state(row=row, state=state, event=latest_event)
        debug_state = trace["debug_state"]
        evaluation_conversation = [
            *conversation,
            ConversationMessage(speaker=Speaker.CLIENT, content=reply),
        ]
        trace.update(
            self._build_test_evaluation_trace(
                row=row,
                data=data,
                conversation=evaluation_conversation,
                state_history=trace["state_history"],
            )
        )
        return ScenarioTestMessageResponse(
            reply=reply,
            debug_state=debug_state,
            trace=trace,
        )

    # -- Publish / duplicate / deactivate ----------------------------------

    async def publish_scenario(
        self, db: AsyncSession, faculty: CurrentUser, scenario_id: uuid.UUID
    ) -> ScenarioPublishResponse:
        row = await self._get_or_404(db, scenario_id)
        data = self._authoring_from_row(row)
        self._validate_for_publish(row, data)

        now = datetime.now(timezone.utc)
        template = get_template(row.template_key)
        rubric_snapshot = self._build_rubric_snapshot(data)
        version = await scenario_version_crud.create_scenario_version(
            db,
            scenario_id=row.id,
            version_number=await scenario_version_crud.next_version_number(db, row.id),
            template_key=template.key,
            template_version=template.version,
            prompt_version=row.prompt_version or template.version,
            rubric_version="2.0.0",
            output_schema_version=template.output_schema_version,
            rendered_client_prompt=row.generated_prompt or "",
            rendered_evaluator_prompt=template.build_evaluator_prompt(
                [], [o.model_dump() for o in data.learning_objectives]
            ),
            authoring_snapshot=data.model_dump(),
            rubric_snapshot=rubric_snapshot,
            safety_policy_snapshot=data.safety_rules.model_dump(),
            learning_objectives_snapshot=[
                o.model_dump() for o in data.learning_objectives
            ],
            published_by=faculty.email,
            published_at=now,
        )
        await scenario_crud.update_scenario(
            db,
            row,
            status=ScenarioStatus.PUBLISHED,
            is_active=True,
            template_key=template.key,
            template_version=template.version,
            current_version_id=version.id,
            published_by=faculty.email,
            published_at=now,
            system_prompt=row.generated_prompt,
            client_name=data.client_identity.name,
            description=data.description or row.description or "",
            student_goal=self._derive_student_goal(data),
            client_profile=self._build_client_profile(data),
            # Module 1 evaluation rubric stays fixed regardless of authoring.
            rubric_json=rubric_snapshot,
        )
        await db.commit()
        await db.refresh(row)
        return ScenarioPublishResponse(
            id=row.id,
            status=row.status,
            slug=row.slug,
            prompt_version=row.prompt_version,
            scenario_version_id=version.id,
            template_key=template.key,
            template_version=template.version,
        )

    async def duplicate_scenario(
        self, db: AsyncSession, faculty: CurrentUser, scenario_id: uuid.UUID
    ) -> FacultyScenarioDetail:
        row = await self._get_or_404(db, scenario_id)
        data = self._authoring_from_row(row)
        data.title = f"{row.title} (copy)"
        new_row = await scenario_crud.create_scenario(
            db,
            slug=await self._unique_slug(db, data.title),
            status=ScenarioStatus.DRAFT,
            is_active=False,
            created_by=faculty.email,
            client_name=data.client_identity.name,
            description=data.description or "",
            student_goal=self._derive_student_goal(data),
            **self._structured_fields(data),
        )
        await db.commit()
        await db.refresh(new_row)
        return FacultyScenarioDetail.model_validate(new_row)

    async def deactivate_scenario(
        self, db: AsyncSession, scenario_id: uuid.UUID
    ) -> FacultyScenarioDetail:
        row = await self._get_or_404(db, scenario_id)
        await scenario_crud.update_scenario(
            db, row, status=ScenarioStatus.INACTIVE, is_active=False
        )
        await db.commit()
        await db.refresh(row)
        return FacultyScenarioDetail.model_validate(row)

    # -- Helpers ------------------------------------------------------------

    async def _get_or_404(self, db: AsyncSession, scenario_id: uuid.UUID) -> Scenario:
        row = await scenario_crud.get_scenario_by_id(db, scenario_id)
        if row is None:
            raise ResourceNotFoundError("Scenario not found.")
        return row

    def _require_editable(self, row: Scenario) -> None:
        if row.status == ScenarioStatus.PUBLISHED:
            raise ConflictError(
                "This scenario is published. Duplicate it to make changes so "
                "existing student attempts stay tied to the original."
            )
        if row.status not in _EDITABLE_STATUSES:
            raise ConflictError("This scenario cannot be edited in its current state.")

    @staticmethod
    def _structured_fields(data: ScenarioAuthoringData) -> dict:
        return {
            "module_number": data.module_number,
            "title": data.title,
            "difficulty": data.difficulty,
            "estimated_turns": data.estimated_turns,
            "opening_message": data.opening_message,
            "client_identity": data.client_identity.model_dump(),
            "presenting_concern": data.presenting_concern.model_dump(),
            "cultural_considerations": data.cultural_considerations.model_dump(),
            "resistance_configuration": data.resistance_configuration.model_dump(),
            "engagement_levels": [item.model_dump() for item in data.engagement_levels],
            "engagement_increase_rules": [
                item.model_dump() for item in data.engagement_increase_rules
            ],
            "engagement_decrease_rules": [
                item.model_dump() for item in data.engagement_decrease_rules
            ],
            "disclosure_rules": data.disclosure_rules.model_dump(),
            "progression_beats": [item.model_dump() for item in data.progression_beats],
            "emotional_cue_progression": [
                item.model_dump() for item in data.emotional_cue_progression
            ],
            "silence_response_rules": [
                item.model_dump() for item in data.silence_response_rules
            ],
            "counselor_skill_detection": [
                item.model_dump() for item in data.counselor_skill_detection
            ],
            "session_success_indicators": [
                item.model_dump() for item in data.session_success_indicators
            ],
            "emotional_tone": data.emotional_tone.model_dump(),
            "hidden_information": list(data.hidden_information),
            "learning_objectives": [o.model_dump() for o in data.learning_objectives],
            "rubric_items": [r.model_dump() for r in data.rubric],
            "competency_scale": [item.model_dump() for item in data.competency_scale],
            "evaluation_focus_sections": [
                item.model_dump() for item in data.evaluation_focus_sections
            ],
            "reflection_questions": list(data.reflection_questions),
            "safety_rules": data.safety_rules.model_dump(),
        }

    @staticmethod
    def _derive_student_goal(data: ScenarioAuthoringData) -> str:
        names = [o.name for o in data.learning_objectives if o.name]
        if names:
            return "Practice and demonstrate: " + ", ".join(names) + "."
        return "Practice foundational counseling microskills with this client."

    @staticmethod
    def _build_client_profile(data: ScenarioAuthoringData) -> dict:
        identity = data.client_identity
        concern = data.presenting_concern
        first_message = data.opening_message or (
            f"I suppose I'm here because of {concern.primary_concern.rstrip('.').lower()}. "
            "I'm not really sure where to start."
        )
        return {
            "age": identity.age,
            "occupation": identity.occupation,
            "presenting_concern": concern.primary_concern,
            "disposition": data.emotional_tone.starting_tone,
            "first_client_message": first_message,
            "skills": [o.name for o in data.learning_objectives if o.name],
        }

    @staticmethod
    def _build_rubric_snapshot(data: ScenarioAuthoringData) -> dict:
        if not data.rubric:
            return MODULE1_RUBRIC
        snapshot = {}
        for item in data.rubric:
            key = _SLUG_RE.sub("_", item.category.strip().lower()).strip("_")
            if not key:
                continue
            snapshot[key] = {
                "label": item.category,
                "description": item.description or "",
                "max_score": item.max_score,
                "weight": item.weight,
                "observable_indicators": item.observable_indicators,
                "common_mistakes": item.common_mistakes,
                "feedback_guidance": item.feedback_guidance or "",
                "rating_anchors": item.rating_anchors,
                "optional_when_not_observable": item.optional_when_not_observable,
            }
        return snapshot or MODULE1_RUBRIC

    @staticmethod
    def _build_evaluator_preview_prompt(
        system_prompt: str,
        *,
        rubric_snapshot: dict,
        data: ScenarioAuthoringData,
        row: Scenario,
    ) -> str:
        preview_context = {
            "template_metadata": {
                "template_key": row.template_key,
                "template_version": row.template_version,
                "rubric_version": "draft",
                "output_schema_version": get_template(row.template_key).output_schema_version,
                "scenario_version_id": None,
            },
            "rubric": rubric_snapshot,
            "learning_objectives": [
                objective.model_dump() for objective in data.learning_objectives
            ],
            "competency_scale": [
                item.model_dump() for item in data.competency_scale
            ],
            "evaluation_focus_sections": [
                item.model_dump() for item in data.evaluation_focus_sections
            ],
            "reflection_questions": list(data.reflection_questions),
            "runtime_placeholders": {
                "client_state_history": "Inserted from the session state at evaluation time.",
                "transcript": "Inserted from the completed student/client conversation at evaluation time.",
            },
        }
        return (
            system_prompt.strip()
            + "\n\nDRAFT SCENARIO-SPECIFIC EVALUATION CONTEXT\n"
            + json.dumps(preview_context, indent=2)
            + "\n"
        )

    @staticmethod
    def _build_test_evaluation_trace(
        *,
        row: Scenario,
        data: ScenarioAuthoringData,
        conversation: list[ConversationMessage],
        state_history: list[dict],
    ) -> dict:
        template = get_template(row.template_key)
        rubric_snapshot = ScenarioAuthoringService._build_rubric_snapshot(data)
        evaluator_system_prompt = template.build_evaluator_prompt(
            [item.model_dump() for item in data.rubric],
            [objective.model_dump() for objective in data.learning_objectives],
        )
        template_metadata = {
            "template_key": row.template_key,
            "template_version": row.template_version,
            "rubric_version": "draft",
            "output_schema_version": template.output_schema_version,
            "scenario_version_id": None,
            "competency_scale": [item.model_dump() for item in data.competency_scale],
            "evaluation_focus_sections": [
                item.model_dump() for item in data.evaluation_focus_sections
            ],
            "reflection_questions": list(data.reflection_questions),
        }
        transcript = ScenarioAuthoringService._conversation_transcript(
            conversation,
            client_name=row.client_name or data.client_identity.name or "Client",
        )
        evaluator_user_prompt = EvaluationAgent._build_prompt(
            transcript=transcript,
            rubric=rubric_snapshot,
            template_metadata=template_metadata,
            learning_objectives=[
                objective.model_dump() for objective in data.learning_objectives
            ],
            state_history=compact_state_history(state_history),
        )
        return {
            "evaluation_transcript_text": transcript,
            "evaluator_system_prompt_text": evaluator_system_prompt,
            "evaluator_user_prompt_text": evaluator_user_prompt,
            "final_evaluation_prompt_text": (
                evaluator_system_prompt.strip()
                + "\n\nEVALUATOR USER PROMPT\n"
                + evaluator_user_prompt
            ),
        }

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

    async def _build_test_trace(
        self,
        *,
        row: Scenario,
        data: ScenarioAuthoringData,
        conversation: list[ConversationMessage],
        client_name: str,
    ) -> tuple[dict, PreparedClientTurn, SessionState]:
        template = get_template(row.template_key)
        initial = template.initial_state(data)
        state = SessionState(**initial)

        class _FlushOnlyDB:
            async def flush(self) -> None:
                return None

        persona_prompt = self._builder.build_runtime_persona_prompt(data)
        latest_runtime_context = build_runtime_client_context(state=state, allowed_disclosures=[])
        latest_stateful_prompt = f"{persona_prompt.rstrip()}\n\n{latest_runtime_context}"
        latest_conversation_prompt = ScenarioAgent._build_prompt(
            conversation,
            client_name=client_name,
        )
        turn_traces: list[dict] = []
        student_turn_count = 0
        latest_prepared: PreparedClientTurn | None = None
        latest_student_index = max(
            index
            for index, item in enumerate(conversation)
            if item.speaker == Speaker.STUDENT
        )
        for idx, turn in enumerate(conversation):
            if turn.speaker != Speaker.STUDENT:
                continue
            student_turn_count += 1
            prefix = conversation[: idx + 1]
            prepared = await self._turn_pipeline.prepare_turn(
                _FlushOnlyDB(),
                state=state,
                scenario=data,
                template_key=row.template_key,
                student_content=turn.content,
                conversation=prefix,
                student_turn_count=student_turn_count,
                client_name=client_name,
                semantic_analysis=idx == latest_student_index,
            )
            if idx + 1 < len(conversation) and conversation[idx + 1].speaker == Speaker.CLIENT:
                self._turn_pipeline.finalize_existing_response(
                    prepared=prepared,
                    scenario=data,
                    client_text=conversation[idx + 1].content,
                )
            latest_prepared = prepared
            event = state.state_history[-1]
            latest_runtime_context = prepared.runtime_context
            latest_stateful_prompt = prepared.system_prompt
            latest_conversation_prompt = prepared.conversation_prompt
            turn_traces.append(
                self._turn_trace(
                    prepared=prepared,
                    event=event,
                    student_message=turn.content,
                )
            )

        if latest_prepared is None:
            raise ValidationError("A counselor message is required to build a test turn.")
        latest_event = state.state_history[-1]
        trace = {
            "debug_state": self._debug_state(row=row, state=state, event=latest_event),
            "base_client_prompt_text": persona_prompt,
            "latest_runtime_context_text": latest_runtime_context,
            "latest_client_stateful_system_prompt_text": latest_stateful_prompt,
            "latest_client_conversation_prompt_text": latest_conversation_prompt,
            "state_history": state.state_history,
            "turn_traces": turn_traces,
        }
        return trace, latest_prepared, state

    @staticmethod
    def _turn_trace(
        *, prepared: PreparedClientTurn, event: dict, student_message: str
    ) -> dict:
        return {
            "student_turn_count": prepared.response_plan.turn,
            "student_message": student_message,
            "detected_behaviors": prepared.detection.labels,
            "counselor_analysis": prepared.detection.model_dump(),
            "cue_response_analysis": prepared.cue_response_analysis.model_dump(),
            "expected_client_reactions": event.get("expected_client_reactions", []),
            "engagement_delta": prepared.transition.engagement_delta,
            "trust_delta": prepared.transition.trust_delta,
            "engagement_level": prepared.transition.state.engagement_level,
            "trust_level": prepared.transition.state.trust_level,
            "disclosure_stage": prepared.transition.state.disclosure_stage,
            "session_stage": prepared.transition.state.session_stage,
            "stage_gate": event.get("stage_gate"),
            "allowed_disclosures": prepared.transition.allowed_disclosures,
            "response_plan": prepared.response_plan.model_dump(),
            "validation": event.get("validation"),
            "generation_attempts": event.get("generation_attempts", []),
            "revealed_information": event.get("revealed_information", []),
            "emotional_cues": event.get("emotional_cues", []),
            "runtime_context_text": prepared.runtime_context,
            "client_stateful_system_prompt_text": prepared.system_prompt,
            "client_conversation_prompt_text": prepared.conversation_prompt,
        }

    @staticmethod
    def _debug_state(*, row: Scenario, state: SessionState, event: dict) -> dict:
        return {
            "template_key": row.template_key,
            "template_version": row.template_version,
            "engagement_level": state.engagement_level,
            "trust_level": state.trust_level,
            "emotional_depth": state.emotional_depth or 1,
            "rupture_count": state.rupture_count or 0,
            "repair_count": state.repair_count or 0,
            "disclosure_stage": state.disclosure_stage,
            "session_stage": state.session_stage,
            "detected_behaviors": event.get("detected_behaviors", []),
            "allowed_disclosures": event.get("allowed_disclosures", []),
            "selected_disclosure_key": (event.get("response_plan") or {}).get(
                "selected_disclosure_key"
            ),
            "revealed_information": list(state.revealed_information),
            "emotional_cues": list(state.emotional_cues),
            "expected_client_reactions": event.get("expected_client_reactions", []),
        }

    @staticmethod
    def _authoring_from_row(row: Scenario) -> ScenarioAuthoringData:
        difficulty = (row.difficulty or "easy").lower()
        if difficulty not in ("easy", "medium", "hard"):
            difficulty = "easy"
        client_identity = row.client_identity or {"name": row.client_name or "Client"}
        presenting = row.presenting_concern or {"primary_concern": row.description or "their concern"}
        opening = row.opening_message
        if not opening and row.client_profile:
            opening = row.client_profile.get("first_client_message")
        return ScenarioAuthoringData(
            module_number=row.module_number,
            title=row.title,
            description=row.description or None,
            difficulty=difficulty,
            estimated_turns=row.estimated_turns,
            opening_message=opening,
            client_identity=client_identity,
            presenting_concern=presenting,
            cultural_considerations=row.cultural_considerations or {},
            resistance_configuration=row.resistance_configuration or {},
            engagement_levels=row.engagement_levels or [],
            engagement_increase_rules=row.engagement_increase_rules or [],
            engagement_decrease_rules=row.engagement_decrease_rules or [],
            disclosure_rules=row.disclosure_rules or {},
            progression_beats=row.progression_beats or [],
            emotional_cue_progression=row.emotional_cue_progression or [],
            silence_response_rules=row.silence_response_rules or [],
            counselor_skill_detection=row.counselor_skill_detection or [],
            session_success_indicators=row.session_success_indicators or [],
            emotional_tone=row.emotional_tone or {},
            hidden_information=row.hidden_information or [],
            learning_objectives=row.learning_objectives or [],
            rubric=row.rubric_items or [],
            competency_scale=row.competency_scale or [],
            evaluation_focus_sections=row.evaluation_focus_sections or [],
            reflection_questions=row.reflection_questions or [],
            safety_rules=row.safety_rules or {},
        )

    @staticmethod
    def _validate_for_publish(row: Scenario, data: ScenarioAuthoringData) -> None:
        errors: list[str] = []
        if not data.title.strip():
            errors.append("a title is required")
        if not data.client_identity.name.strip():
            errors.append("the client needs a name")
        if not data.presenting_concern.primary_concern.strip():
            errors.append("a primary presenting concern is required")
        if not data.learning_objectives:
            errors.append("at least one learning objective is required")
        if data.disclosure_rules.is_empty():
            errors.append("at least one disclosure rule is required")
        authored_behavior_keys = {
            str(rule.behavior_key)
            for rule in [
                *data.engagement_increase_rules,
                *data.engagement_decrease_rules,
                *data.counselor_skill_detection,
            ]
            if rule.behavior_key
        }
        unsupported_keys = sorted(
            authored_behavior_keys - SUPPORTED_RUNTIME_BEHAVIOR_KEYS
        )
        if unsupported_keys:
            errors.append(
                "unsupported behavior keys: " + ", ".join(unsupported_keys)
            )
        if data.safety_rules.crisis_content_allowed:
            errors.append("crisis content is not permitted in this version")
        if data.rubric:
            total = sum(item.weight for item in data.rubric)
            if total != 100:
                errors.append(f"rubric weights must total 100 (currently {total})")
        if not row.generated_prompt:
            errors.append("generate and preview the client behavior before publishing")

        if errors:
            raise ValidationError(
                "This scenario cannot be published yet: " + "; ".join(errors) + "."
            )

    async def _unique_slug(self, db: AsyncSession, title: str) -> str:
        base = _SLUG_RE.sub("_", title.strip().lower()).strip("_")[:48] or "scenario"
        if await scenario_crud.get_scenario_by_slug(db, base) is None:
            return base
        return f"{base}_{uuid.uuid4().hex[:6]}"


scenario_authoring_service = ScenarioAuthoringService()
