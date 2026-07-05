"""Unit tests for deterministic client-state transitions."""

from app.ai.skill_classifier_agent import CounselorBehaviorDetection
from app.db.models.session_state import SessionState
from app.schemas.scenario_authoring import (
    ClientIdentity,
    DisclosureItem,
    DisclosureRules,
    PresentingConcern,
    ScenarioAuthoringData,
)
from app.schemas.turn_pipeline import CueResponseAnalysis
from app.services.state_transition_service import StateTransitionService


class _FakeDB:
    async def flush(self) -> None:
        return None


def _scenario() -> ScenarioAuthoringData:
    return ScenarioAuthoringData(
        title="Practice Scenario",
        client_identity=ClientIdentity(name="Jordan"),
        presenting_concern=PresentingConcern(primary_concern="Work stress."),
        disclosure_rules=DisclosureRules(
            immediate=["I feel worn down at work."],
            after_rapport=["I worry I am failing my students."],
        ),
    )


def _state(**overrides) -> SessionState:
    fields = {
        "engagement_level": 2,
        "trust_level": 2,
        "disclosure_stage": 1,
        "session_stage": "early",
        "revealed_information": [],
        "emotional_cues": [],
        "state_history": [],
    }
    fields.update(overrides)
    return SessionState(**fields)


async def test_empathy_can_increase_engagement_and_unlock_mid_disclosure():
    service = StateTransitionService()
    detection = CounselorBehaviorDetection(
        accurate_empathy=True,
        open_ended_question=True,
        labels=["accurate_empathy", "open_ended_question"],
    )

    result = await service.apply_student_turn(
        _FakeDB(),
        state=_state(state_history=[{"trust_building_streak": 1}]),
        scenario=_scenario(),
        template_key="microskills_progressive_disclosure",
        detected=detection,
        cue_analysis=CueResponseAnalysis(),
        student_turn_count=4,
    )

    assert result.engagement_delta == 1
    assert result.trust_delta == 1
    assert result.state.engagement_level == 3
    assert result.state.session_stage == "mid"
    assert "I worry I am failing my students." in result.allowed_disclosures
    assert result.state.state_history[-1]["detected_behaviors"] == [
        "accurate_empathy",
        "open_ended_question",
    ]


async def test_premature_advice_decreases_engagement():
    service = StateTransitionService()
    detection = CounselorBehaviorDetection(
        premature_advice=True,
        labels=["premature_advice"],
    )

    result = await service.apply_student_turn(
        _FakeDB(),
        state=_state(engagement_level=3, trust_level=3),
        scenario=_scenario(),
        template_key="microskills_progressive_disclosure",
        detected=detection,
        cue_analysis=CueResponseAnalysis(),
        student_turn_count=2,
    )

    assert result.engagement_delta == -1
    assert result.state.engagement_level == 2
    assert result.state.trust_level == 2
    assert result.trust_delta == -1


async def test_elapsed_turns_alone_do_not_unlock_deep_disclosure():
    service = StateTransitionService()
    detection = CounselorBehaviorDetection()

    result = await service.apply_student_turn(
        _FakeDB(),
        state=_state(engagement_level=2, trust_level=2),
        scenario=_scenario(),
        template_key="microskills_progressive_disclosure",
        detected=detection,
        cue_analysis=CueResponseAnalysis(),
        student_turn_count=8,
    )

    assert result.state.session_stage == "early"
    assert result.state.disclosure_stage == 1
    assert result.allowed_disclosures == ["I feel worn down at work."]


async def test_direct_question_disclosure_requires_a_question_on_that_turn():
    scenario = _scenario()
    scenario.disclosure_rules.on_direct_question = [
        DisclosureItem(
            key="future_worry",
            label="Future worry",
            content_summary="I worry this pace is not sustainable.",
            minimum_engagement_level=2,
            session_stage="early",
            requires_direct_question=True,
        )
    ]
    service = StateTransitionService()

    result = await service.apply_student_turn(
        _FakeDB(),
        state=_state(),
        scenario=scenario,
        template_key="microskills_progressive_disclosure",
        detected=CounselorBehaviorDetection(),
        cue_analysis=CueResponseAnalysis(),
        student_turn_count=1,
    )

    assert "I worry this pace is not sustainable." not in result.allowed_disclosures
