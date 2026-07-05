"""Deterministic client-state transitions for student turns."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.skill_classifier_agent import CounselorBehaviorDetection
from app.db.models.session_state import SessionState
from app.schemas.scenario_authoring import DisclosureItem, ProgressionBeat, ScenarioAuthoringData
from app.schemas.turn_pipeline import CueResponseAnalysis
from app.scenario_templates import get_template
from app.utils.scenario_state import STAGE_ORDER, disclosure_key

_ENGAGEMENT_INCREASE_BEHAVIORS = (
    "accurate_empathy",
    "reflection_of_feeling",
    "reflection_of_meaning",
    "validation",
    "emotional_exploration",
    "appropriate_processing_space",
    "cue_acknowledgment",
    "cue_deepening",
    "therapeutic_presence",
    "rapport_building",
    "pacing",
)
_TRUST_INCREASE_BEHAVIORS = (
    "accurate_empathy",
    "reflection_of_feeling",
    "reflection_of_meaning",
    "validation",
    "emotional_exploration",
    "cue_acknowledgment",
    "cue_deepening",
    "therapeutic_presence",
    "rapport_building",
)
_DECREASE_BEHAVIORS = (
    "premature_advice",
    "rapid_fire_questions",
    "excessive_questioning",
    "frequent_topic_shift",
    "early_problem_solving",
    "ignored_emotional_cue",
)


@dataclass(frozen=True)
class StateTransitionResult:
    state: SessionState
    engagement_delta: int
    trust_delta: int
    allowed_disclosures: list[str]
    eligible_disclosures: list[DisclosureItem]
    event: dict[str, Any]


class StateTransitionService:
    """Applies template-aware deterministic state changes."""

    async def apply_student_turn(
        self,
        db: AsyncSession,
        *,
        state: SessionState,
        scenario: ScenarioAuthoringData,
        template_key: str,
        detected: CounselorBehaviorDetection,
        cue_analysis: CueResponseAnalysis,
        student_turn_count: int,
    ) -> StateTransitionResult:
        state_before = self._state_snapshot(state)
        previous_cue_response = self._update_previous_cue(
            state,
            cue_analysis=cue_analysis,
            student_turn_count=student_turn_count,
        )
        derived_labels = self._derived_behavior_labels(
            state_history=state.state_history,
            detected=detected,
            cue_analysis=cue_analysis,
            previous_cue_response=previous_cue_response,
        )
        detected.labels = list(dict.fromkeys([*detected.labels, *derived_labels]))
        detected_set = set(detected.labels)
        positive = [name for name in _ENGAGEMENT_INCREASE_BEHAVIORS if name in detected_set]
        trust_positive = [name for name in _TRUST_INCREASE_BEHAVIORS if name in detected_set]
        negative = [name for name in _DECREASE_BEHAVIORS if name in detected_set]
        positive_rules = self._matching_rules(
            detected.labels, scenario.engagement_increase_rules
        )
        negative_rules = self._matching_rules(
            detected.labels, scenario.engagement_decrease_rules
        )
        engagement_delta = self._engagement_delta(
            positive,
            negative,
            positive_rule_changes=[item.engagement_change for item in positive_rules],
            negative_rule_changes=[item.engagement_change for item in negative_rules],
        )
        trust_streak = self._trust_building_streak(
            state.state_history,
            has_positive=bool(trust_positive),
            has_negative=bool(negative),
        )
        trust_delta = self._trust_delta(
            trust_positive,
            negative,
            streak=trust_streak,
            speed=scenario.resistance_configuration.trust_development_speed,
        )

        min_level = scenario.resistance_configuration.minimum_engagement_level
        max_level = scenario.resistance_configuration.maximum_engagement_level
        state.trust_level = self._clamp(
            state.trust_level + trust_delta,
            min_level=min_level,
            max_level=max_level,
        )
        state.session_stage, stage_gate = self._session_stage(
            current_stage=state.session_stage,
            student_turn_count=student_turn_count,
            trust_level=state.trust_level,
            scenario=scenario,
            state=state,
        )
        stage_engagement_cap = {"early": 3, "mid": 4, "later": 5}.get(
            state.session_stage,
            max_level,
        )
        state.engagement_level = self._clamp(
            state.engagement_level + engagement_delta,
            min_level=min_level,
            max_level=min(max_level, stage_engagement_cap),
        )
        state.disclosure_stage = self._disclosure_stage(state.session_stage)
        self._update_depth_and_rupture(
            state,
            detected=detected,
            cue_analysis=cue_analysis,
            previous_cue_response=previous_cue_response,
        )

        template = get_template(template_key)
        eligible_beats = self._eligible_progression_beats(
            scenario.progression_beats,
            state=state,
            detected=detected,
            cue_analysis=cue_analysis,
            previous_cue_response=previous_cue_response,
        )
        eligible_disclosures = (
            [self._beat_disclosure(beat) for beat in eligible_beats if beat.disclosure_content]
            if scenario.progression_beats
            else template.eligible_disclosures(
                scenario,
                self._state_dict(state),
                has_direct_question=detected.question_count > 0,
            )
        )
        allowed_disclosures = [item.content_summary for item in eligible_disclosures]

        event = {
            "turn": student_turn_count,
            "detected_behaviors": detected.labels,
            "counselor_analysis": detected.model_dump(),
            "cue_response_analysis": cue_analysis.model_dump(),
            "derived_behavior_labels": derived_labels,
            "expected_client_reactions": [
                item.client_response for item in [*positive_rules, *negative_rules]
            ],
            "engagement_delta": engagement_delta,
            "trust_delta": trust_delta,
            "trust_building_streak": trust_streak,
            "engagement_level": state.engagement_level,
            "trust_level": state.trust_level,
            "disclosure_stage": state.disclosure_stage,
            "session_stage": state.session_stage,
            "stage_gate": stage_gate,
            "allowed_disclosures": allowed_disclosures,
            "eligible_disclosure_keys": [
                disclosure_key(item) for item in eligible_disclosures
            ],
            "eligible_progression_beat_keys": [beat.key for beat in eligible_beats],
            "previous_cue_response": previous_cue_response,
            "state_before": state_before,
            "state_after": self._state_snapshot(state),
        }
        state.state_history = [*state.state_history, event]
        await db.flush()
        return StateTransitionResult(
            state=state,
            engagement_delta=engagement_delta,
            trust_delta=trust_delta,
            allowed_disclosures=allowed_disclosures,
            eligible_disclosures=eligible_disclosures,
            event=event,
        )

    @staticmethod
    def _engagement_delta(
        positive: list[str],
        negative: list[str],
        *,
        positive_rule_changes: list[int] | None = None,
        negative_rule_changes: list[int] | None = None,
    ) -> int:
        if "ignored_emotional_cue" in negative:
            return min(negative_rule_changes or [-1])
        if negative and not positive:
            return min(negative_rule_changes or [-1])
        if positive and not negative:
            return max(positive_rule_changes or [1])
        return 0

    @staticmethod
    def _matching_rules(detected_labels: list[str], rules: list[Any]) -> list[Any]:
        detected = set(detected_labels)
        return [
            rule
            for rule in rules
            if rule.behavior_key and rule.behavior_key in detected
        ]

    @staticmethod
    def _trust_delta(
        positive: list[str],
        negative: list[str],
        *,
        streak: int,
        speed: str,
    ) -> int:
        if "ignored_emotional_cue" in negative:
            return -1
        if negative and not positive:
            return -1
        if not positive or negative:
            return 0
        turns_per_level = {"fast": 1, "moderate": 2, "slow": 3}.get(speed, 2)
        return 1 if streak > 0 and streak % turns_per_level == 0 else 0

    @staticmethod
    def _trust_building_streak(
        state_history: list[dict[str, Any]], *, has_positive: bool, has_negative: bool
    ) -> int:
        if not has_positive or has_negative:
            return 0
        previous = state_history[-1].get("trust_building_streak", 0) if state_history else 0
        return int(previous) + 1

    @staticmethod
    def _session_stage(
        *,
        current_stage: str,
        student_turn_count: int,
        trust_level: int,
        scenario: ScenarioAuthoringData,
        state: SessionState,
    ) -> tuple[str, dict[str, Any]]:
        target = (
            "mid" if current_stage == "early" else "later" if current_stage == "mid" else "later"
        )
        gate = StateTransitionService._stage_gate_status(
            scenario=scenario,
            state=state,
            target_stage=target,
        )
        time_and_trust_ready = (
            current_stage == "early" and student_turn_count >= 4 and trust_level >= 3
        ) or (
            current_stage == "mid" and student_turn_count >= 8 and trust_level >= 4
        )
        gate["time_and_trust_ready"] = time_and_trust_ready
        if time_and_trust_ready and gate["satisfied"]:
            return target, gate
        return current_stage, gate

    @staticmethod
    def _stage_gate_status(
        *,
        scenario: ScenarioAuthoringData,
        state: SessionState,
        target_stage: str,
    ) -> dict[str, Any]:
        target_rank = STAGE_ORDER.get(target_stage, 1)
        required = [
            beat.key
            for beat in scenario.progression_beats
            if beat.required_for_completion
            and STAGE_ORDER.get(beat.session_stage, 1) < target_rank
        ]
        if not required:
            return {
                "target_stage": target_stage,
                "satisfied": True,
                "required_beat_keys": [],
                "missing_beat_keys": [],
                "blocking_cues": [],
                "legacy_compatible": True,
            }
        revealed = {str(item) for item in state.revealed_information}
        missing = [key for key in required if key not in revealed]
        blocking = [
            {
                "beat_key": item.get("beat_key"),
                "cue": item.get("cue"),
                "status": item.get("status"),
            }
            for item in state.emotional_cues
            if isinstance(item, dict)
            and item.get("beat_key") in required
            and item.get("status") in {"presented", "unresolved", "missed"}
        ]
        return {
            "target_stage": target_stage,
            "satisfied": not missing and not blocking,
            "required_beat_keys": required,
            "missing_beat_keys": missing,
            "blocking_cues": blocking,
            "legacy_compatible": False,
        }

    @staticmethod
    def _disclosure_stage(session_stage: str) -> int:
        return {"early": 1, "mid": 2, "later": 3}.get(session_stage, 1)

    @staticmethod
    def _clamp(value: int, *, min_level: int = 1, max_level: int = 5) -> int:
        return max(min_level, min(max_level, value))

    @staticmethod
    def _state_dict(state: SessionState) -> dict[str, Any]:
        return {
            "engagement_level": state.engagement_level,
            "trust_level": state.trust_level,
            "disclosure_stage": state.disclosure_stage,
            "session_stage": state.session_stage,
            "revealed_information": state.revealed_information,
            "emotional_cues": state.emotional_cues,
            "state_history": state.state_history,
            "emotional_depth": state.emotional_depth or 1,
            "rupture_count": state.rupture_count or 0,
            "repair_count": state.repair_count or 0,
        }

    @staticmethod
    def _state_snapshot(state: SessionState) -> dict[str, Any]:
        return {
            "engagement_level": state.engagement_level,
            "trust_level": state.trust_level,
            "disclosure_stage": state.disclosure_stage,
            "session_stage": state.session_stage,
            "revealed_information": list(state.revealed_information),
            "emotional_cues": list(state.emotional_cues),
            "emotional_depth": state.emotional_depth or 1,
            "rupture_count": state.rupture_count or 0,
            "repair_count": state.repair_count or 0,
        }

    @staticmethod
    def _derived_behavior_labels(
        *,
        state_history: list[dict[str, Any]],
        detected: CounselorBehaviorDetection,
        cue_analysis: CueResponseAnalysis,
        previous_cue_response: str | None,
    ) -> list[str]:
        labels: list[str] = []
        positive_cue = cue_analysis.status in {
            "acknowledged",
            "accurately_reflected",
            "deepened",
        }
        missed_cue = cue_analysis.status in {
            "ignored",
            "topic_only",
            "misattuned",
            "redirected",
        }
        harmful = any(
            getattr(detected, name)
            for name in (
                "premature_advice",
                "rapid_fire_questions",
                "excessive_questioning",
                "frequent_topic_shift",
                "early_problem_solving",
            )
        )
        if positive_cue or previous_cue_response == "repaired":
            labels.extend(["cue_acknowledgment", "therapeutic_presence"])
        if cue_analysis.status == "deepened":
            labels.append("cue_deepening")
        if missed_cue:
            labels.append("ignored_emotional_cue")
        if not harmful and detected.question_count <= 1 and (
            positive_cue or detected.appropriate_processing_space
        ):
            labels.append("pacing")
        prior_presence = any(
            "therapeutic_presence" in set(event.get("detected_behaviors") or [])
            for event in state_history[-2:]
        )
        if "therapeutic_presence" in labels and prior_presence:
            labels.append("rapport_building")
        return labels

    @staticmethod
    def _update_previous_cue(
        state: SessionState,
        *,
        cue_analysis: CueResponseAnalysis,
        student_turn_count: int,
    ) -> str | None:
        ledger = [dict(item) if isinstance(item, dict) else item for item in state.emotional_cues]
        active_index = next(
            (
                index
                for index in range(len(ledger) - 1, -1, -1)
                if isinstance(ledger[index], dict)
                and ledger[index].get("status") in {"presented", "unresolved", "missed"}
            ),
            None,
        )
        if active_index is None:
            return None
        active_cue = str(ledger[active_index].get("cue") or "")
        analysis_matches = bool(
            cue_analysis.cue
            and cue_analysis.cue.casefold() == active_cue.casefold()
        )
        prior_status = ledger[active_index].get("status")
        if analysis_matches and cue_analysis.status in {
            "acknowledged",
            "accurately_reflected",
            "deepened",
        }:
            status = "repaired" if prior_status == "missed" else cue_analysis.status
        elif analysis_matches and cue_analysis.status in {
            "ignored",
            "topic_only",
            "misattuned",
            "redirected",
        }:
            status = "missed"
        else:
            status = "unresolved"
        ledger[active_index] = {
            **ledger[active_index],
            "status": status,
            "semantic_status": cue_analysis.status,
            "semantic_confidence": cue_analysis.confidence,
            "counselor_evidence": cue_analysis.counselor_evidence,
            "semantic_rationale": cue_analysis.rationale,
            "analyzer": cue_analysis.analyzer,
            "responded_on_turn": student_turn_count,
        }
        state.emotional_cues = ledger
        return status

    @staticmethod
    def _eligible_progression_beats(
        beats: list[ProgressionBeat],
        *,
        state: SessionState,
        detected: CounselorBehaviorDetection,
        cue_analysis: CueResponseAnalysis,
        previous_cue_response: str | None,
    ) -> list[ProgressionBeat]:
        revealed = {str(item) for item in state.revealed_information}
        current_stage = STAGE_ORDER.get(state.session_stage, 1)
        eligible: list[ProgressionBeat] = []
        for beat in beats:
            if beat.key in revealed and not beat.repeatable:
                continue
            if STAGE_ORDER.get(beat.session_stage, 1) > current_stage:
                continue
            if state.engagement_level < beat.minimum_engagement_level:
                continue
            if state.trust_level < beat.minimum_trust_level:
                continue
            if any(key not in revealed for key in beat.prerequisite_beat_keys):
                continue
            if beat.trigger == "direct_question" and detected.question_count == 0:
                continue
            if beat.trigger == "after_reflection" and not (
                detected.reflection_of_feeling or detected.reflection_of_meaning
            ):
                continue
            if beat.trigger == "after_pause" and not detected.appropriate_processing_space:
                continue
            requirement = beat.required_counselor_response
            if requirement == "acknowledge_cue" and previous_cue_response not in {
                "acknowledged",
                "accurately_reflected",
                "deepened",
                "repaired",
            }:
                continue
            if requirement == "deepen_cue" and cue_analysis.status != "deepened":
                continue
            if requirement == "direct_question" and detected.question_count == 0:
                continue
            if requirement == "therapeutic_pause" and not detected.appropriate_processing_space:
                continue
            eligible.append(beat)
        return eligible

    @staticmethod
    def _beat_disclosure(beat: ProgressionBeat) -> DisclosureItem:
        return DisclosureItem(
            key=beat.key,
            label=beat.disclosure_label or beat.title,
            content_summary=beat.disclosure_content or "",
            minimum_engagement_level=beat.minimum_engagement_level,
            session_stage=beat.session_stage,
            requires_direct_question=beat.trigger == "direct_question",
            faculty_only_notes=beat.faculty_only_notes or beat.private_meaning,
        )

    @staticmethod
    def _update_depth_and_rupture(
        state: SessionState,
        *,
        detected: CounselorBehaviorDetection,
        cue_analysis: CueResponseAnalysis,
        previous_cue_response: str | None,
    ) -> None:
        harmful = any(
            (
                detected.premature_advice,
                detected.rapid_fire_questions,
                detected.excessive_questioning,
                detected.frequent_topic_shift,
                detected.early_problem_solving,
            )
        )
        cue_miss = cue_analysis.status in {
            "ignored",
            "topic_only",
            "misattuned",
            "redirected",
        }
        if harmful or cue_miss:
            state.rupture_count = (state.rupture_count or 0) + 1
        if previous_cue_response == "repaired":
            state.repair_count = (state.repair_count or 0) + 1
        depth = state.emotional_depth or 1
        if cue_analysis.status == "deepened":
            depth += 1
        stage_cap = {"early": 2, "mid": 4, "later": 5}.get(state.session_stage, 2)
        state.emotional_depth = max(1, min(stage_cap, depth))


state_transition_service = StateTransitionService()
