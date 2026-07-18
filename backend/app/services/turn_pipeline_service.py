"""Orchestrate one analyzed, planned, generated, and validated client turn."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.client_response_validator_agent import (
    SemanticClientResponseValidator,
    semantic_client_response_validator,
)
from app.ai.cue_response_analyzer_agent import (
    CueResponseAnalyzer,
    cue_response_analyzer,
)
from app.ai.output_models import ConversationMessage
from app.ai.prompt_builder import ScenarioPromptBuilder, scenario_prompt_builder
from app.ai.runtime_context_builder import build_runtime_client_context
from app.ai.scenario_agent import ScenarioAgent, scenario_agent
from app.ai.skill_classifier_agent import (
    CounselorBehaviorDetection,
    SkillClassifierAgent,
    skill_classifier_agent,
)
from app.db.models.session_state import SessionState
from app.schemas.scenario_authoring import ScenarioAuthoringData
from app.schemas.turn_pipeline import (
    ClientResponsePlan,
    ClientResponseValidation,
    CueResponseAnalysis,
)
from app.services.response_planning_service import (
    ResponsePlanningService,
    response_planning_service,
)
from app.services.state_transition_service import (
    StateTransitionResult,
    StateTransitionService,
    state_transition_service,
)
from app.utils.scenario_state import STAGE_ORDER, all_disclosure_items, disclosure_key


_CUE_FALLBACKS = {
    "stress": "I think the stress is the clearest part right now. There is a lot competing for my attention, and I am still trying to sort out where to begin.",
    "frustration": "I think the frustrating part is how little room there seems to be for everything. I am not ready to go much deeper than that yet.",
    "overwhelm": "Mostly it feels like too much at once. I can name the overwhelm, but I am still figuring out how to explain the rest of it.",
    "fatigue": "I have been feeling tired more often, and it is becoming harder to recover from the pressure.",
    "guilt": "There is some guilt there, although it is difficult for me to say much more about it yet.",
    "self-doubt": "I have started questioning myself more, but I am still hesitant to unpack that fully.",
}

_BEAT_FALLBACKS = {
    "emotional_exhaustion": (
        "I feel drained in a way that is more than just being busy. Even when I "
        "get through the day, I do not really feel restored."
    ),
}

_LOCKED_DISCLOSURE_GUARDRAILS = {
    "sustainability_doubts": (
        "Do not mention how long the client can keep going, whether this can "
        "continue, burnout, being unable to keep doing this, or long-term "
        "sustainability. Stay with tiredness, depletion, and difficulty feeling "
        "restored."
    ),
}


@dataclass(frozen=True)
class PreparedClientTurn:
    detection: CounselorBehaviorDetection
    cue_response_analysis: CueResponseAnalysis
    transition: StateTransitionResult
    response_plan: ClientResponsePlan
    persona_prompt: str
    runtime_context: str
    system_prompt: str
    conversation_prompt: str


@dataclass(frozen=True)
class TurnPipelineResult:
    client_text: str
    validation: ClientResponseValidation
    prepared: PreparedClientTurn
    generation_attempts: list[dict]


class TurnPipelineService:
    """Keeps AI interpretation and wording inside deterministic state boundaries."""

    def __init__(
        self,
        *,
        classifier: SkillClassifierAgent | None = None,
        transition_service: StateTransitionService | None = None,
        planner: ResponsePlanningService | None = None,
        prompt_builder: ScenarioPromptBuilder | None = None,
        agent: ScenarioAgent | None = None,
        validator: SemanticClientResponseValidator | None = None,
        cue_analyzer: CueResponseAnalyzer | None = None,
    ) -> None:
        self._classifier = classifier or skill_classifier_agent
        self._transition_service = transition_service or state_transition_service
        self._planner = planner or response_planning_service
        self._prompt_builder = prompt_builder or scenario_prompt_builder
        self._agent = agent or scenario_agent
        self._validator = validator or semantic_client_response_validator
        self._cue_analyzer = cue_analyzer or cue_response_analyzer

    def initialize_opening_state(
        self,
        *,
        state: SessionState,
        scenario: ScenarioAuthoringData,
        opening_message: str,
    ) -> ClientResponseValidation:
        """Record cues and disclosures already present in the authored opening line."""
        early_cues = [
            cue
            for item in scenario.emotional_cue_progression
            if STAGE_ORDER.get(item.session_stage, 1) <= STAGE_ORDER["early"]
            for cue in item.emotional_cues
        ]
        all_keys = [disclosure_key(item) for item in all_disclosure_items(scenario)]
        plan = ClientResponsePlan(
            turn=0,
            session_stage="early",
            client_stance="opening statement",
            engagement_level=state.engagement_level,
            trust_level=state.trust_level,
            emotional_depth=state.emotional_depth or 1,
            rupture_count=state.rupture_count or 0,
            counselor_effect="No counselor response has occurred yet.",
            active_emotional_cues=early_cues,
            permitted_emotional_cues=early_cues,
            eligible_disclosure_keys=all_keys,
            blocked_disclosure_keys=[],
            already_revealed_keys=all_keys,
            maximum_new_disclosures=0,
        )
        validation = self._validator.validate_deterministically(
            response=opening_message,
            plan=plan,
            scenario=scenario,
        )
        authored_opening_keys = [
            beat.key
            for beat in scenario.progression_beats
            if beat.trigger == "opening" and beat.disclosure_content
        ]
        state.revealed_information = list(
            dict.fromkeys([*validation.detected_disclosure_keys, *authored_opening_keys])
        )
        state.beat_states = []
        for key in state.revealed_information:
            beat = next(
                (item for item in scenario.progression_beats if item.key == key),
                None,
            )
            state.beat_states = StateTransitionService._upsert_beat_state(
                state.beat_states or [],
                {
                    "beat_key": str(key),
                    "disclosure_status": "revealed",
                    "post_disclosure_status": (
                        "pending_response"
                        if beat and beat.required_counselor_response != "any"
                        else "not_required"
                    ),
                    "resolution_status": (
                        "pending_response"
                        if beat and beat.required_counselor_response != "any"
                        else "resolved"
                    ),
                    "requires_repair": False,
                    "revealed_on_turn": 0,
                },
            )
        state.emotional_cues = []
        for cue in validation.detected_emotional_cues:
            beat = next(
                (
                    item
                    for item in scenario.progression_beats
                    if item.trigger == "opening" and cue in item.emotional_cues
                ),
                None,
            )
            state.emotional_cues.append(
                {
                    "cue": cue,
                    "beat_key": beat.key if beat else None,
                    "private_meaning": beat.private_meaning if beat else None,
                    "client_evidence": opening_message,
                    "status": "presented",
                    "presented_on_turn": 0,
                }
            )
        state.state_history = [
            {
                "turn": 0,
                "event_type": "opening_observation",
                "client_response": opening_message,
                "validation": validation.model_dump(),
                "revealed_information": list(state.revealed_information),
                "emotional_cues": list(state.emotional_cues),
                "beat_states": list(state.beat_states),
                "engagement_level": state.engagement_level,
                "trust_level": state.trust_level,
                "emotional_depth": state.emotional_depth or 1,
                "session_stage": state.session_stage,
            }
        ]
        return validation

    async def prepare_turn(
        self,
        db: AsyncSession,
        *,
        state: SessionState,
        scenario: ScenarioAuthoringData,
        template_key: str,
        student_content: str,
        conversation: list[ConversationMessage],
        student_turn_count: int,
        client_name: str,
        semantic_analysis: bool = True,
        session_id: str | None = None,
    ) -> PreparedClientTurn:
        detection = await self._classifier.classify(
            content=student_content,
            conversation=conversation,
            semantic=semantic_analysis,
        )
        cue_analysis = await self._cue_analyzer.analyze(
            counselor_response=student_content,
            conversation=conversation,
            state=state,
            scenario=scenario,
            semantic=semantic_analysis,
            session_id=session_id,
        )
        transition = await self._transition_service.apply_student_turn(
            db,
            state=state,
            scenario=scenario,
            template_key=template_key,
            detected=detection,
            cue_analysis=cue_analysis,
            student_turn_count=student_turn_count,
        )
        plan = self._planner.build_plan(
            state=transition.state,
            scenario=scenario,
            transition=transition,
            student_turn_count=student_turn_count,
        )
        persona_prompt = self._prompt_builder.build_runtime_persona_prompt(scenario)
        runtime_context = build_runtime_client_context(
            state=transition.state,
            response_plan=plan,
        )
        system_prompt = f"{persona_prompt.rstrip()}\n\n{runtime_context}"
        conversation_prompt = ScenarioAgent._build_prompt(
            conversation,
            client_name=client_name,
        )
        return PreparedClientTurn(
            detection=detection,
            cue_response_analysis=cue_analysis,
            transition=transition,
            response_plan=plan,
            persona_prompt=persona_prompt,
            runtime_context=runtime_context,
            system_prompt=system_prompt,
            conversation_prompt=conversation_prompt,
        )

    async def run_turn(
        self,
        db: AsyncSession,
        *,
        state: SessionState,
        scenario: ScenarioAuthoringData,
        template_key: str,
        student_content: str,
        conversation: list[ConversationMessage],
        student_turn_count: int,
        client_name: str,
        session_id: str | None = None,
        semantic_analysis: bool = True,
    ) -> TurnPipelineResult:
        prepared = await self.prepare_turn(
            db,
            state=state,
            scenario=scenario,
            template_key=template_key,
            student_content=student_content,
            conversation=conversation,
            student_turn_count=student_turn_count,
            client_name=client_name,
            semantic_analysis=semantic_analysis,
            session_id=session_id,
        )
        result = await self.generate_prepared_turn(
            prepared=prepared,
            scenario=scenario,
            conversation=conversation,
            client_name=client_name,
            session_id=session_id,
        )
        await db.flush()
        return result

    async def generate_prepared_turn(
        self,
        *,
        prepared: PreparedClientTurn,
        scenario: ScenarioAuthoringData,
        conversation: list[ConversationMessage],
        client_name: str,
        session_id: str | None = None,
    ) -> TurnPipelineResult:
        """Generate and finalize a turn that has already passed deterministic planning."""
        generation_attempts: list[dict] = []
        client_text = await self._agent.generate_client_response(
            scenario_prompt=prepared.system_prompt,
            conversation=conversation,
            client_name=client_name,
            session_id=session_id,
        )
        validation = await self._validator.validate(
            response=client_text,
            plan=prepared.response_plan,
            scenario=scenario,
            session_id=session_id,
        )
        generation_attempts.append(
            {"attempt": 1, "response": client_text, "validation": validation.model_dump()}
        )
        if not validation.accepted:
            correction = self._retry_prompt(
                prepared=prepared,
                validation=validation,
                rejected_response=client_text,
            )
            client_text = await self._agent.generate_client_response(
                scenario_prompt=correction,
                conversation=conversation,
                client_name=client_name,
                session_id=session_id,
            )
            validation = await self._validator.validate(
                response=client_text,
                plan=prepared.response_plan,
                scenario=scenario,
                session_id=session_id,
            )
            generation_attempts.append(
                {"attempt": 2, "response": client_text, "validation": validation.model_dump()}
            )
        if not validation.accepted:
            client_text = self._controlled_fallback(prepared.response_plan)
            validation = self._validator.validate_deterministically(
                response=client_text,
                plan=prepared.response_plan,
                scenario=scenario,
            )
            generation_attempts.append(
                {
                    "attempt": 3,
                    "response": client_text,
                    "validation": validation.model_dump(),
                    "source": "controlled_fallback",
                }
            )

        self.finalize_turn(
            state=prepared.transition.state,
            prepared=prepared,
            client_text=client_text,
            validation=validation,
            generation_attempts=generation_attempts,
        )
        return TurnPipelineResult(
            client_text=client_text,
            validation=validation,
            prepared=prepared,
            generation_attempts=generation_attempts,
        )

    def finalize_existing_response(
        self,
        *,
        prepared: PreparedClientTurn,
        scenario: ScenarioAuthoringData,
        client_text: str,
    ) -> ClientResponseValidation:
        """Reconcile a stored client response while replaying a faculty test trace."""
        validation = self._validator.validate_deterministically(
            response=client_text,
            plan=prepared.response_plan,
            scenario=scenario,
        )
        self.finalize_turn(
            state=prepared.transition.state,
            prepared=prepared,
            client_text=client_text,
            validation=validation,
            generation_attempts=[
                {
                    "attempt": 1,
                    "response": client_text,
                    "validation": validation.model_dump(),
                    "source": "replayed_existing_response",
                }
            ],
        )
        return validation

    @staticmethod
    def finalize_turn(
        *,
        state: SessionState,
        prepared: PreparedClientTurn,
        client_text: str,
        validation: ClientResponseValidation,
        generation_attempts: list[dict] | None = None,
    ) -> None:
        revealed = list(state.revealed_information)
        permitted = set(prepared.response_plan.already_revealed_keys)
        if prepared.response_plan.selected_disclosure_key:
            permitted.add(prepared.response_plan.selected_disclosure_key)
        fallback_revealed_key = TurnPipelineService._fallback_revealed_key(
            prepared=prepared,
            validation=validation,
            generation_attempts=generation_attempts or [],
        )
        if fallback_revealed_key:
            permitted.add(fallback_revealed_key)
        for key in validation.detected_disclosure_keys:
            if key in permitted and key not in revealed:
                revealed.append(key)
                state.beat_states = StateTransitionService._upsert_beat_state(
                    state.beat_states or [],
                    {
                        "beat_key": key,
                        "disclosure_status": "revealed",
                        "post_disclosure_status": "pending_response",
                        "resolution_status": "pending_response",
                        "requires_repair": False,
                        "revealed_on_turn": prepared.response_plan.turn,
                    },
                )
        if fallback_revealed_key and fallback_revealed_key not in revealed:
            revealed.append(fallback_revealed_key)
            state.beat_states = StateTransitionService._upsert_beat_state(
                state.beat_states or [],
                {
                    "beat_key": fallback_revealed_key,
                    "disclosure_status": "revealed",
                    "post_disclosure_status": "pending_response",
                    "resolution_status": "pending_response",
                    "requires_repair": False,
                    "revealed_on_turn": prepared.response_plan.turn,
                    "source": "controlled_fallback",
                },
            )
        state.revealed_information = revealed

        cue_ledger = list(state.emotional_cues)
        for cue in validation.detected_emotional_cues:
            finding = next(
                (item for item in validation.cue_findings if item.cue == cue),
                None,
            )
            existing_index = next(
                (
                    index
                    for index in range(len(cue_ledger) - 1, -1, -1)
                    if isinstance(cue_ledger[index], dict)
                    and str(cue_ledger[index].get("cue", "")).casefold()
                    == cue.casefold()
                    and cue_ledger[index].get("status")
                    in {"presented", "unresolved", "missed"}
                ),
                None,
            )
            if existing_index is not None:
                cue_ledger[existing_index] = {
                    **cue_ledger[existing_index],
                    "beat_key": cue_ledger[existing_index].get("beat_key")
                    or prepared.response_plan.selected_progression_beat_key,
                    "client_evidence": finding.evidence if finding else client_text,
                    "reexpressed_on_turn": prepared.response_plan.turn,
                }
                continue
            cue_ledger.append(
                {
                    "cue": cue,
                    "beat_key": prepared.response_plan.selected_progression_beat_key,
                    "client_evidence": finding.evidence if finding else client_text,
                    "status": "presented",
                    "presented_on_turn": prepared.response_plan.turn,
                }
            )
        state.emotional_cues = cue_ledger

        event = {
            **prepared.transition.event,
            "response_plan": prepared.response_plan.model_dump(),
            "validation": validation.model_dump(),
            "generation_attempts": generation_attempts or [],
            "client_response": client_text,
            "revealed_information": list(state.revealed_information),
            "emotional_cues": list(state.emotional_cues),
            "beat_states": list(state.beat_states or []),
            "client_persona_prompt_text": prepared.persona_prompt,
            "runtime_context_text": prepared.runtime_context,
            "client_stateful_system_prompt_text": prepared.system_prompt,
            "client_conversation_prompt_text": prepared.conversation_prompt,
        }
        event["state_after"] = {
            "engagement_level": state.engagement_level,
            "trust_level": state.trust_level,
            "disclosure_stage": state.disclosure_stage,
            "session_stage": state.session_stage,
            "revealed_information": list(state.revealed_information),
            "emotional_cues": list(state.emotional_cues),
            "beat_states": list(state.beat_states or []),
            "emotional_depth": state.emotional_depth or 1,
            "rupture_count": state.rupture_count or 0,
            "repair_count": state.repair_count or 0,
        }
        history = list(state.state_history)
        if history and history[-1].get("turn") == prepared.response_plan.turn:
            history[-1] = event
        else:
            history.append(event)
        state.state_history = history

    @staticmethod
    def _controlled_fallback(plan: ClientResponsePlan) -> str:
        if plan.selected_disclosure_key in _BEAT_FALLBACKS:
            return _BEAT_FALLBACKS[plan.selected_disclosure_key]
        cue = plan.active_emotional_cues[0].lower() if plan.active_emotional_cues else ""
        return _CUE_FALLBACKS.get(
            cue,
            "I'm still trying to put that into words. I think I need a little more time before I can say much more about it.",
        )

    @staticmethod
    def _retry_prompt(
        *,
        prepared: PreparedClientTurn,
        validation: ClientResponseValidation,
        rejected_response: str,
    ) -> str:
        locked_keys = validation.unauthorized_disclosure_keys
        guardrails = [
            _LOCKED_DISCLOSURE_GUARDRAILS[key]
            for key in locked_keys
            if key in _LOCKED_DISCLOSURE_GUARDRAILS
        ]
        selected_content = prepared.response_plan.selected_disclosure_content or (
            "No new story fact is permitted; stay with the active emotional cue."
        )
        permitted_cues = ", ".join(prepared.response_plan.permitted_emotional_cues) or "none"
        blocked_keys = ", ".join(prepared.response_plan.blocked_disclosure_keys) or "none"
        guardrail_text = (
            "\nSpecific locked-boundary guidance:\n- " + "\n- ".join(guardrails)
            if guardrails
            else ""
        )
        return (
            prepared.system_prompt
            + "\n\nGENERATION CORRECTION\n"
            + "The prior draft crossed a disclosure boundary and was rejected.\n"
            + f"Rejected draft:\n{rejected_response}\n\n"
            + "Write a different, natural client response that follows the response plan exactly.\n"
            + f"Allowed new disclosure: {selected_content}\n"
            + f"Permitted emotional cues: {permitted_cues}\n"
            + f"Locked disclosure keys to avoid: {blocked_keys}\n"
            + guardrail_text
            + "\nKeep the response emotionally realistic, but do not add future story facts, "
            + "long-term conclusions, crisis implications, or private meanings that are not "
            + "explicitly allowed above."
        )

    @staticmethod
    def _fallback_revealed_key(
        *,
        prepared: PreparedClientTurn,
        validation: ClientResponseValidation,
        generation_attempts: list[dict],
    ) -> str | None:
        if not validation.accepted or not generation_attempts:
            return None
        latest = generation_attempts[-1]
        if latest.get("source") != "controlled_fallback":
            return None
        key = prepared.response_plan.selected_disclosure_key
        if key and key in _BEAT_FALLBACKS:
            return key
        return None


turn_pipeline_service = TurnPipelineService()
