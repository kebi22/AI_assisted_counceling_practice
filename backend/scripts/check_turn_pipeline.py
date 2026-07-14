"""Deterministic smoke check for the analyzed client-turn pipeline.

Usage:
    python -m scripts.check_turn_pipeline
"""

from __future__ import annotations

import asyncio

from app.ai.output_models import ConversationMessage
from app.ai.cue_response_analyzer_agent import CueResponseAnalyzer
from app.ai.skill_classifier_agent import CounselorBehaviorDetection
from app.ai.client_response_validator_agent import SemanticClientResponseValidator
from app.core.constants import Speaker
from app.db.models.session_state import SessionState
from app.schemas.scenario_authoring import ScenarioAuthoringData
from app.schemas.turn_pipeline import CueResponseAnalysis, SemanticClientResponseAnalysis
from app.scenario_templates.microskills_progressive_disclosure import (
    MODULE1_EMOTIONAL_CUE_PROGRESSION,
    MODULE1_ENGAGEMENT_DECREASE_RULES,
    MODULE1_ENGAGEMENT_INCREASE_RULES,
    MODULE1_ENGAGEMENT_LEVELS,
    MODULE1_PROGRESSION_BEATS,
)
from app.services.state_transition_service import StateTransitionService
from app.services.evaluation_context import build_simulation_fidelity
from app.services.turn_pipeline_service import TurnPipelineService
from app.services.client_response_validator import client_response_validator


class _FlushOnlyDB:
    async def flush(self) -> None:
        return None


class _ScriptedAgent:
    def __init__(self) -> None:
        self.responses = iter(
            [
                "Work has been stressful, and I feel pulled in too many directions.",
                "There never seem to be enough hours for teaching, planning, and my personal life.",
                "It is overwhelming to keep trying to stay ahead of everything.",
                "I feel tired and drained, and I am not sure how long I can keep going at this pace.",
            ]
        )

    async def generate_client_response(self, **_: object) -> str:
        return next(self.responses)


class _DeterministicValidationAdapter:
    async def validate(self, *, response, plan, scenario, session_id=None):
        return client_response_validator.validate(
            response=response,
            plan=plan,
            scenario=scenario,
        )

    def validate_deterministically(self, *, response, plan, scenario):
        return client_response_validator.validate(
            response=response,
            plan=plan,
            scenario=scenario,
        )


class _CueSemanticClient:
    async def generate_structured(self, **kwargs):
        return kwargs["schema"].model_validate(
            {
                "cue": "Guilt",
                "cue_key": "relationship_guilt",
                "status": "accurately_reflected",
                "confidence": 0.96,
                "client_evidence": "I feel like I am letting people down.",
                "counselor_evidence": "You feel like you're letting them down",
                "rationale": "The response accurately reflects the active guilt cue.",
                "analyzer": "test",
            }
        )


class _ScriptedCueAnalyzer:
    async def analyze(self, *, state, scenario, **kwargs):
        active = CueResponseAnalyzer.active_cue(state=state, scenario=scenario)
        if active is None:
            return CueResponseAnalysis()
        return CueResponseAnalysis(
            cue=str(active["cue"]),
            cue_key=active.get("beat_key"),
            status="accurately_reflected",
            confidence=1,
            client_evidence=str(active.get("client_evidence") or ""),
            counselor_evidence=str(kwargs.get("counselor_response") or ""),
            analyzer="scripted-cue-check-v1",
        )


def _scenario() -> ScenarioAuthoringData:
    return ScenarioAuthoringData.model_validate(
        {
            "title": "Turn pipeline check",
            "client_identity": {"name": "Sarah", "occupation": "Teacher"},
            "presenting_concern": {"primary_concern": "Stress and overwhelm"},
            "resistance_configuration": {
                "starting_engagement_level": 2,
                "trust_development_speed": "moderate",
            },
            "engagement_levels": MODULE1_ENGAGEMENT_LEVELS,
            "engagement_increase_rules": MODULE1_ENGAGEMENT_INCREASE_RULES,
            "engagement_decrease_rules": MODULE1_ENGAGEMENT_DECREASE_RULES,
            "emotional_cue_progression": MODULE1_EMOTIONAL_CUE_PROGRESSION,
            "disclosure_rules": {
                "immediate": [
                    {
                        "key": "work_stress",
                        "label": "Work stress",
                        "content_summary": "Work has been stressful and Sarah feels pulled in too many directions.",
                    },
                    {
                        "key": "time_pressure",
                        "label": "Time pressure",
                        "content_summary": "There are not enough hours for teaching, planning, and personal life.",
                    },
                ],
                "after_rapport": [
                    {
                        "key": "exhaustion",
                        "label": "Emotional exhaustion",
                        "content_summary": "Sarah feels tired and drained and is unsure how long she can keep this pace.",
                        "minimum_engagement_level": 3,
                        "session_stage": "mid",
                    }
                ],
            },
        }
    )


async def main() -> None:
    scenario = _scenario()
    state = SessionState(
        engagement_level=2,
        trust_level=2,
        disclosure_stage=1,
        session_stage="early",
        revealed_information=[],
        emotional_cues=[],
        state_history=[],
    )
    pipeline = TurnPipelineService(
        agent=_ScriptedAgent(),
        validator=_DeterministicValidationAdapter(),
        cue_analyzer=_ScriptedCueAnalyzer(),
    )
    conversation = [
        ConversationMessage(
            speaker=Speaker.CLIENT,
            content="I am overwhelmed and not sure where to start.",
        )
    ]
    counselor_turns = [
        "It sounds like beginning feels hard. What feels most present today?",
        "That sounds stressful and exhausting. How is it affecting you?",
        "It sounds like you feel overwhelmed by everything you are carrying. What is that like?",
        "That sounds exhausting, and you feel drained by this pressure. What feels hardest now?",
    ]
    for turn_number, counselor_text in enumerate(counselor_turns, start=1):
        conversation.append(
            ConversationMessage(speaker=Speaker.STUDENT, content=counselor_text)
        )
        result = await pipeline.run_turn(
            _FlushOnlyDB(),
            state=state,
            scenario=scenario,
            template_key="microskills_progressive_disclosure",
            student_content=counselor_text,
            conversation=conversation,
            student_turn_count=turn_number,
            client_name="Sarah",
            session_id="turn-pipeline-check",
            semantic_analysis=False,
        )
        assert result.validation.accepted
        conversation.append(
            ConversationMessage(speaker=Speaker.CLIENT, content=result.client_text)
        )

    assert state.engagement_level == 4
    assert state.trust_level == 4
    assert state.session_stage == "mid"
    assert state.revealed_information == ["work_stress", "time_pressure", "exhaustion"]
    assert state.state_history[0]["trust_delta"] == 0
    assert state.state_history[1]["trust_delta"] == 1
    assert state.state_history[3]["response_plan"]["selected_disclosure_key"] == "exhaustion"
    assert state.state_history[0]["counselor_analysis"]["analyzer"] == "deterministic-pattern-v1"
    assert state.emotional_depth >= 1

    fidelity = build_simulation_fidelity(state.state_history)
    assert fidelity["turns_audited"] == 4
    assert fidelity["revealed_progression_beats"] == [
        "work_stress",
        "time_pressure",
        "exhaustion",
    ]

    plan = result.prepared.response_plan
    related_only = SemanticClientResponseAnalysis.model_validate(
        {
            "disclosures": [
                {
                    "disclosure_key": "future_worry",
                    "status": "related_only",
                    "confidence": 0.96,
                    "evidence": "Work has been exhausting.",
                    "reason": "Related to work strain but does not communicate inability to continue.",
                }
            ],
            "cues": [],
        }
    )
    related_result = SemanticClientResponseValidator._apply_permission_policy(
        analysis=related_only,
        plan=plan,
        scenario=scenario,
    )
    assert related_result.accepted

    semantic_leak = SemanticClientResponseAnalysis.model_validate(
        {
            "disclosures": [
                {
                    "disclosure_key": "future_worry",
                    "status": "substantially_revealed",
                    "confidence": 0.93,
                    "evidence": "I do not know how much longer I can keep doing this.",
                    "reason": "Communicates inability to sustain the current situation.",
                }
            ],
            "cues": [],
        }
    )
    leak_result = SemanticClientResponseValidator._apply_permission_policy(
        analysis=semantic_leak,
        plan=plan,
        scenario=scenario,
    )
    assert not leak_result.accepted
    assert leak_result.unauthorized_disclosure_keys == ["future_worry"]

    explicit_safety = client_response_validator.validate(
        response="I want to kill myself.",
        plan=plan,
        scenario=scenario,
    )
    assert not explicit_safety.accepted
    assert explicit_safety.safety_finding.status == "explicit"

    cue_state = SessionState(
        engagement_level=3,
        trust_level=3,
        disclosure_stage=2,
        session_stage="mid",
        revealed_information=["relationship_guilt"],
        emotional_cues=[
            {
                "cue": "Guilt",
                "beat_key": "relationship_guilt",
                "client_evidence": "I feel like I am letting people down.",
                "status": "presented",
            }
        ],
        state_history=[],
    )
    cue_scenario = ScenarioAuthoringData.model_validate(
        {
            "title": "Cue grounding check",
            "client_identity": {"name": "Sarah"},
            "presenting_concern": {"primary_concern": "Stress and overwhelm"},
            "progression_beats": MODULE1_PROGRESSION_BEATS,
        }
    )
    cue_analyzer = CueResponseAnalyzer(client=_CueSemanticClient())
    cue_result = await cue_analyzer.analyze(
        counselor_response="You feel like you're letting them down, and that guilt is weighing on you.",
        conversation=[
            ConversationMessage(
                speaker=Speaker.CLIENT,
                content="I feel like I am letting people down.",
            ),
            ConversationMessage(
                speaker=Speaker.STUDENT,
                content="You feel like you're letting them down, and that guilt is weighing on you.",
            ),
        ],
        state=cue_state,
        scenario=cue_scenario,
    )
    assert cue_result.status == "accurately_reflected"
    cue_status = StateTransitionService._update_previous_cue(
        cue_state,
        cue_analysis=cue_result,
        student_turn_count=5,
    )
    assert cue_status == "accurately_reflected"
    assert cue_state.emotional_cues[-1]["counselor_evidence"].startswith("You feel")

    missed_state = SessionState(
        engagement_level=3,
        trust_level=3,
        disclosure_stage=1,
        session_stage="early",
        revealed_information=["work_stress", "time_management"],
        emotional_cues=[
            {
                "cue": "Overwhelm",
                "beat_key": "time_management",
                "status": "presented",
            }
        ],
        state_history=[],
    )
    missed = CueResponseAnalysis(
        cue="Overwhelm",
        cue_key="time_management",
        status="redirected",
        confidence=0.94,
        counselor_evidence="How many classes do you teach?",
    )
    missed_status = StateTransitionService._update_previous_cue(
        missed_state,
        cue_analysis=missed,
        student_turn_count=4,
    )
    assert missed_status == "missed"
    beat_patch = StateTransitionService._update_beat_response_state(
        missed_state,
        detected=CounselorBehaviorDetection(),
        cue_analysis=missed,
        previous_cue_response=missed_status,
        student_turn_count=4,
    )
    assert beat_patch is not None
    assert beat_patch["beat_key"] == "time_management"
    assert beat_patch["resolution_status"] == "needs_repair"
    assert missed_state.beat_states[-1]["requires_repair"] is True
    gate = StateTransitionService._stage_gate_status(
        scenario=cue_scenario,
        state=missed_state,
        target_stage="mid",
    )
    assert not gate["satisfied"]
    assert gate["unresolved_beat_keys"] == ["time_management"]
    dependent = StateTransitionService._eligible_progression_beats(
        MODULE1_PROGRESSION_BEATS,
        state=missed_state,
        detected=CounselorBehaviorDetection(reflection_of_feeling=True),
        cue_analysis=missed,
        previous_cue_response=missed_status,
    )
    assert "exhaustion" not in [beat.key for beat in dependent]
    derived = StateTransitionService._derived_behavior_labels(
        state_history=[],
        detected=CounselorBehaviorDetection(),
        cue_analysis=missed,
        previous_cue_response=missed_status,
    )
    assert "ignored_emotional_cue" in derived
    repair = CueResponseAnalysis(
        cue="Overwhelm",
        cue_key="time_management",
        status="deepened",
        confidence=0.95,
        counselor_evidence="The overwhelm feels impossible to carry; what is that like for you?",
    )
    repaired_status = StateTransitionService._update_previous_cue(
        missed_state,
        cue_analysis=repair,
        student_turn_count=5,
    )
    assert repaired_status == "repaired"
    repaired_patch = StateTransitionService._update_beat_response_state(
        missed_state,
        detected=CounselorBehaviorDetection(),
        cue_analysis=repair,
        previous_cue_response=repaired_status,
        student_turn_count=5,
    )
    assert repaired_patch is not None
    assert repaired_patch["resolution_status"] == "repaired"
    assert missed_state.beat_states[-1]["requires_repair"] is False
    repaired_gate = StateTransitionService._stage_gate_status(
        scenario=cue_scenario,
        state=missed_state,
        target_stage="mid",
    )
    assert repaired_gate["satisfied"]
    print("turn pipeline check passed")


if __name__ == "__main__":
    asyncio.run(main())
