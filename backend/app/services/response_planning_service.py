"""Build a constrained client-response plan from deterministic session state."""

from __future__ import annotations

from app.db.models.session_state import SessionState
from app.schemas.scenario_authoring import DisclosureItem, ScenarioAuthoringData
from app.schemas.turn_pipeline import ClientResponsePlan
from app.services.state_transition_service import StateTransitionResult
from app.utils.scenario_state import all_disclosure_items, disclosure_key


class ResponsePlanningService:
    """Selects one cue and at most one new disclosure for a client turn."""

    def build_plan(
        self,
        *,
        state: SessionState,
        scenario: ScenarioAuthoringData,
        transition: StateTransitionResult,
        student_turn_count: int,
    ) -> ClientResponsePlan:
        revealed = set(str(item) for item in state.revealed_information)
        unresolved_cues = self._active_unresolved_cues(state=state)
        eligible = (
            []
            if unresolved_cues
            else [
                item
                for item in transition.eligible_disclosures
                if disclosure_key(item) not in revealed
            ]
        )
        selected = eligible[0] if eligible else None
        selected_beat = next(
            (
                beat
                for beat in scenario.progression_beats
                if selected and beat.key == disclosure_key(selected)
            ),
            None,
        )
        recovery_beat = next(
            (
                beat
                for beat in reversed(scenario.progression_beats)
                if beat.key in revealed and beat.emotional_cues
            ),
            None,
        )
        all_items = all_disclosure_items(scenario)
        eligible_keys = [disclosure_key(item) for item in eligible]
        blocked_keys = [
            disclosure_key(item)
            for item in all_items
            if disclosure_key(item) not in revealed
            and disclosure_key(item) not in eligible_keys
        ]
        cues = (
            list(selected_beat.emotional_cues)
            if selected_beat and selected_beat.emotional_cues
            else unresolved_cues
            or (list(recovery_beat.emotional_cues) if recovery_beat else [])
        )
        permitted_cues = list(dict.fromkeys(cues))

        reactions = transition.event.get("expected_client_reactions") or []
        counselor_effect = (
            "; ".join(str(item) for item in reactions)
            if reactions
            else self._default_effect(transition)
        )
        if not selected and not unresolved_cues and recovery_beat:
            counselor_effect = (
                counselor_effect
                + " Re-express only the most recent revealed experience without introducing "
                "a new story fact or deeper private meaning."
            )
        return ClientResponsePlan(
            turn=student_turn_count,
            session_stage=state.session_stage,
            client_stance=self._stance(state, scenario),
            engagement_level=state.engagement_level,
            trust_level=state.trust_level,
            emotional_depth=state.emotional_depth or 1,
            rupture_count=state.rupture_count or 0,
            counselor_effect=counselor_effect,
            previous_cue_response=transition.event.get("previous_cue_response"),
            active_emotional_cues=cues,
            permitted_emotional_cues=permitted_cues,
            selected_disclosure_key=disclosure_key(selected) if selected else None,
            selected_progression_beat_key=selected_beat.key if selected_beat else None,
            selected_disclosure_label=selected.label if selected else None,
            selected_disclosure_content=selected.content_summary if selected else None,
            eligible_disclosure_keys=eligible_keys,
            blocked_disclosure_keys=blocked_keys,
            already_revealed_keys=sorted(revealed),
        )

    @staticmethod
    def _active_unresolved_cues(*, state: SessionState) -> list[str]:
        for item in reversed(state.emotional_cues):
            if (
                isinstance(item, dict)
                and item.get("status") in {"presented", "unresolved", "missed"}
                and item.get("cue")
            ):
                return [str(item["cue"])]
        return []

    @staticmethod
    def _stance(state: SessionState, scenario: ScenarioAuthoringData) -> str:
        for item in scenario.engagement_levels:
            if item.level == state.engagement_level:
                return f"{item.label}: {item.description}"
        return {
            1: "guarded and minimally expressive",
            2: "tentatively open but surface-level",
            3: "engaged while still somewhat cautious",
            4: "vulnerable and increasingly reflective",
            5: "deeply engaged in emotional exploration",
        }.get(state.engagement_level, "cautiously engaged")

    @staticmethod
    def _default_effect(transition: StateTransitionResult) -> str:
        if transition.engagement_delta < 0 or transition.trust_delta < 0:
            return "Become somewhat more guarded and keep the response closer to the surface."
        if transition.engagement_delta > 0 or transition.trust_delta > 0:
            return "Respond to the counselor's attunement with a modest increase in openness."
        return "Maintain the current level of openness without automatically deepening."


response_planning_service = ResponsePlanningService()
