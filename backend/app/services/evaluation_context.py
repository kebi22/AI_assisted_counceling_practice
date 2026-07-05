"""Prepare compact deterministic turn evidence for the evaluator model."""

from __future__ import annotations

from typing import Any


_TRACE_ONLY_FIELDS = {
    "client_persona_prompt_text",
    "runtime_context_text",
    "client_stateful_system_prompt_text",
    "client_conversation_prompt_text",
}


def compact_state_history(state_history: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Exclude large prompt copies while retaining plans, outcomes, and validation."""
    return [
        {key: value for key, value in event.items() if key not in _TRACE_ONLY_FIELDS}
        for event in state_history
    ]


def build_simulation_fidelity(
    state_history: list[dict[str, Any]],
    *,
    progression_beats: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Audit client-simulation behavior separately from student competency."""
    events = [event for event in state_history if event.get("turn") != 0]
    validations = [event.get("validation") or {} for event in events]
    attempts = [attempt for event in events for attempt in event.get("generation_attempts") or []]
    final_state = (state_history[-1].get("state_after") or state_history[-1]) if state_history else {}
    revealed = list(final_state.get("revealed_information") or [])
    required = [
        beat.get("key")
        for beat in progression_beats or []
        if beat.get("required_for_completion")
    ]
    cue_ledger = list(final_state.get("emotional_cues") or [])
    statuses = {
        status: sum(
            1
            for cue in cue_ledger
            if isinstance(cue, dict) and cue.get("status") == status
        )
        for status in (
            "presented",
            "acknowledged",
            "accurately_reflected",
            "deepened",
            "unresolved",
            "missed",
            "repaired",
        )
    }
    return {
        "purpose": "Simulation fidelity audit; this does not score counselor competency.",
        "turns_audited": len(events),
        "semantic_validator_turns": sum(
            1 for item in validations if str(item.get("validator", "")).startswith("gemini")
        ),
        "semantic_cue_analysis_turns": sum(
            1
            for event in events
            if str((event.get("cue_response_analysis") or {}).get("analyzer", "")).startswith(
                "gemini"
            )
        ),
        "story_gate_blocked_turns": [
            event.get("turn")
            for event in events
            if (event.get("stage_gate") or {}).get("time_and_trust_ready")
            and not (event.get("stage_gate") or {}).get("satisfied")
        ],
        "rejected_generation_attempts": sum(
            1 for item in attempts if not (item.get("validation") or {}).get("accepted", True)
        ),
        "controlled_fallbacks": sum(
            1 for item in attempts if item.get("source") == "controlled_fallback"
        ),
        "revealed_progression_beats": revealed,
        "required_progression_beats": required,
        "required_beats_reached": [key for key in required if key in revealed],
        "required_beats_not_reached": [key for key in required if key not in revealed],
        "cue_ledger_status_counts": statuses,
        "rupture_count": int(final_state.get("rupture_count") or 0),
        "repair_count": int(final_state.get("repair_count") or 0),
        "final_emotional_depth": int(final_state.get("emotional_depth") or 1),
        "safety_clarification_turns": [
            event.get("turn")
            for event, validation in zip(events, validations)
            if validation.get("requires_safety_clarification")
        ],
    }
