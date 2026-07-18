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
        beat_response_state = self._update_beat_response_state(
            state,
            detected=detected,
            cue_analysis=cue_analysis,
            previous_cue_response=previous_cue_response,
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
        stage_engagement_cap = {"early": 3, "mid": 4, "later": 5}.get(
            state.session_stage,
            max_level,
        )
        state.engagement_level = self._clamp(
            state.engagement_level + engagement_delta,
            min_level=min_level,
            max_level=min(max_level, stage_engagement_cap),
        )
        state.session_stage, stage_gate = self._session_stage(
            current_stage=state.session_stage,
            trust_level=state.trust_level,
            engagement_level=state.engagement_level,
            scenario=scenario,
            state=state,
            student_turn_count=student_turn_count,
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
            "beat_response_state": beat_response_state,
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
        trust_level: int,
        engagement_level: int,
        scenario: ScenarioAuthoringData,
        state: SessionState,
        student_turn_count: int,
    ) -> tuple[str, dict[str, Any]]:
        target = (
            "mid" if current_stage == "early" else "later" if current_stage == "mid" else "later"
        )
        gate = StateTransitionService._stage_gate_status(
            scenario=scenario,
            state=state,
            target_stage=target,
            student_turn_count=student_turn_count,
        )
        required_level = 3 if current_stage == "early" else 4
        milestone_ready = (
            trust_level >= required_level and engagement_level >= required_level
        )
        gate["time_and_trust_ready"] = milestone_ready
        gate["milestone_ready"] = milestone_ready
        gate["required_trust_level"] = required_level
        gate["required_engagement_level"] = required_level
        gate["progression_basis"] = "clinical_milestones"
        if milestone_ready and gate["satisfied"]:
            return target, gate
        return current_stage, gate

    @staticmethod
    def _stage_gate_status(
        *,
        scenario: ScenarioAuthoringData,
        state: SessionState,
        target_stage: str,
        student_turn_count: int | None = None,
    ) -> dict[str, Any]:
        target_rank = STAGE_ORDER.get(target_stage, 1)
        required_beats = [
            beat
            for beat in scenario.progression_beats
            if beat.required_for_completion
            and STAGE_ORDER.get(beat.session_stage, 1) < target_rank
        ]
        required = [beat.key for beat in required_beats]
        minimum_turns = 3 if target_stage == "mid" else 6 if target_stage == "later" else 0
        turn_ready = student_turn_count is None or student_turn_count >= minimum_turns
        if not required:
            return {
                "target_stage": target_stage,
                "satisfied": turn_ready,
                "required_beat_keys": [],
                "missing_beat_keys": [],
                "required_cues": [],
                "missing_required_cues": [],
                "unaddressed_required_cues": [],
                "blocking_cues": [],
                "minimum_turns": minimum_turns,
                "turn_ready": turn_ready,
                "legacy_compatible": True,
            }
        revealed = {str(item) for item in state.revealed_information}
        missing = [key for key in required if key not in revealed]
        beat_state_map = StateTransitionService._beat_state_map(state)
        unresolved_beats = [
            key
            for key in required
            if key in revealed
            and StateTransitionService._beat_needs_repair(
                beat_state_map.get(key)
            )
        ]
        required_cues = [
            {"beat_key": beat.key, "cue": cue}
            for beat in required_beats
            for cue in beat.emotional_cues
        ]
        sufficient_statuses = {
            "acknowledged",
            "accurately_reflected",
            "deepened",
            "repaired",
        }
        cue_records = [
            item
            for item in state.emotional_cues
            if isinstance(item, dict) and item.get("beat_key") in required
        ]
        missing_required_cues = [
            item
            for item in required_cues
            if not any(
                str(record.get("cue", "")).casefold() == item["cue"].casefold()
                and record.get("beat_key") == item["beat_key"]
                for record in cue_records
            )
        ]
        unaddressed_required_cues = [
            item
            for item in required_cues
            if item not in missing_required_cues
            and not any(
                str(record.get("cue", "")).casefold() == item["cue"].casefold()
                and record.get("beat_key") == item["beat_key"]
                and record.get("status") in sufficient_statuses
                for record in cue_records
            )
        ]
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
        result = {
            "target_stage": target_stage,
            "satisfied": (
                turn_ready
                and not missing
                and not missing_required_cues
                and not unaddressed_required_cues
                and not blocking
                and not unresolved_beats
            ),
            "required_beat_keys": required,
            "missing_beat_keys": missing,
            "unresolved_beat_keys": unresolved_beats,
            "required_cues": required_cues,
            "missing_required_cues": missing_required_cues,
            "unaddressed_required_cues": unaddressed_required_cues,
            "blocking_cues": blocking,
            "minimum_turns": minimum_turns,
            "turn_ready": turn_ready,
            "legacy_compatible": False,
        }
        return result

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
            "beat_states": state.beat_states or [],
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
            "beat_states": list(state.beat_states or []),
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
    def _update_beat_response_state(
        state: SessionState,
        *,
        detected: CounselorBehaviorDetection,
        cue_analysis: CueResponseAnalysis,
        previous_cue_response: str | None,
        student_turn_count: int,
    ) -> dict[str, Any] | None:
        if previous_cue_response is None:
            return None
        cue_record = next(
            (
                item
                for item in reversed(state.emotional_cues)
                if isinstance(item, dict)
                and item.get("responded_on_turn") == student_turn_count
                and item.get("beat_key")
            ),
            None,
        )
        beat_key = str(cue_record.get("beat_key")) if cue_record else cue_analysis.cue_key
        if not beat_key:
            return None
        harmful = any(
            (
                detected.premature_advice,
                detected.rapid_fire_questions,
                detected.excessive_questioning,
                detected.frequent_topic_shift,
                detected.early_problem_solving,
            )
        )
        missed = previous_cue_response in {"missed", "unresolved"} or cue_analysis.status in {
            "ignored",
            "topic_only",
            "misattuned",
            "redirected",
        }
        positive = previous_cue_response in {
            "acknowledged",
            "accurately_reflected",
            "deepened",
            "repaired",
        }
        if harmful or missed:
            patch = {
                "beat_key": beat_key,
                "disclosure_status": "revealed",
                "post_disclosure_status": "ruptured" if harmful else "missed",
                "resolution_status": "needs_repair",
                "requires_repair": True,
                "last_cue_response": previous_cue_response,
                "last_semantic_status": cue_analysis.status,
                "last_counselor_evidence": cue_analysis.counselor_evidence,
                "responded_on_turn": student_turn_count,
            }
        elif positive:
            patch = {
                "beat_key": beat_key,
                "disclosure_status": "revealed",
                "post_disclosure_status": (
                    "repaired" if previous_cue_response == "repaired" else "held"
                ),
                "resolution_status": (
                    "repaired" if previous_cue_response == "repaired" else "resolved"
                ),
                "requires_repair": False,
                "last_cue_response": previous_cue_response,
                "last_semantic_status": cue_analysis.status,
                "last_counselor_evidence": cue_analysis.counselor_evidence,
                "responded_on_turn": student_turn_count,
            }
        else:
            return None
        state.beat_states = StateTransitionService._upsert_beat_state(
            state.beat_states or [],
            patch,
        )
        return patch

    @staticmethod
    def _upsert_beat_state(
        beat_states: list[Any], patch: dict[str, Any]
    ) -> list[dict[str, Any]]:
        ledger = [dict(item) for item in beat_states if isinstance(item, dict)]
        index = next(
            (
                idx
                for idx, item in enumerate(ledger)
                if item.get("beat_key") == patch.get("beat_key")
            ),
            None,
        )
        if index is None:
            ledger.append(patch)
        else:
            ledger[index] = {**ledger[index], **patch}
        return ledger

    @staticmethod
    def _beat_state_map(state: SessionState) -> dict[str, dict[str, Any]]:
        return {
            str(item.get("beat_key")): item
            for item in state.beat_states or []
            if isinstance(item, dict) and item.get("beat_key")
        }

    @staticmethod
    def _beat_needs_repair(beat_state: dict[str, Any] | None) -> bool:
        if not beat_state:
            return False
        return bool(beat_state.get("requires_repair")) or beat_state.get(
            "resolution_status"
        ) in {"needs_repair", "unresolved"}

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
        beat_state_map = StateTransitionService._beat_state_map(state)
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
            if any(
                StateTransitionService._beat_needs_repair(beat_state_map.get(key))
                for key in beat.prerequisite_beat_keys
            ):
                continue
            prerequisite_beats = [
                candidate
                for candidate in beats
                if candidate.key in beat.prerequisite_beat_keys
            ]
            if any(
                not StateTransitionService._beat_expectation_satisfied(
                    prerequisite, state=state
                )
                for prerequisite in prerequisite_beats
            ):
                continue
            if beat.trigger == "direct_question" and detected.question_count == 0:
                continue
            if beat.trigger == "after_reflection" and not (
                detected.reflection_of_feeling or detected.reflection_of_meaning
            ):
                continue
            if beat.trigger == "after_pause" and not detected.appropriate_processing_space:
                continue
            eligible.append(beat)
        return eligible

    @staticmethod
    def _beat_expectation_satisfied(
        beat: ProgressionBeat, *, state: SessionState
    ) -> bool:
        """Evaluate a revealed beat's post-presentation counselor milestone."""
        requirement = beat.required_counselor_response
        beat_state = StateTransitionService._beat_state_map(state).get(beat.key)
        if StateTransitionService._beat_needs_repair(beat_state):
            return False
        if requirement == "any":
            return True
        records = [
            item
            for item in state.emotional_cues
            if isinstance(item, dict) and item.get("beat_key") == beat.key
        ]
        statuses = {str(item.get("status")) for item in records}
        if requirement == "acknowledge_cue":
            return bool(
                statuses
                & {"acknowledged", "accurately_reflected", "deepened", "repaired"}
            )
        if requirement == "deepen_cue":
            return bool(statuses & {"deepened", "repaired"})
        if requirement == "direct_question":
            return any(item.get("question_count", 0) > 0 for item in records)
        if requirement == "therapeutic_pause":
            return any(item.get("appropriate_processing_space") for item in records)
        return False

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
