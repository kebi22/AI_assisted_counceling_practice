"""Build per-turn runtime context for the simulated client prompt."""

from __future__ import annotations

from app.db.models.session_state import SessionState
from app.schemas.turn_pipeline import ClientResponsePlan


def build_runtime_client_context(
    *,
    state: SessionState,
    allowed_disclosures: list[str] | None = None,
    response_plan: ClientResponsePlan | None = None,
) -> str:
    """Return prompt text appended to the static client prompt for one turn."""
    if response_plan is not None:
        disclosure_text = (
            f"- {response_plan.selected_disclosure_label}: "
            f"{response_plan.selected_disclosure_content}"
            if response_plan.selected_disclosure_content
            else "- No new private information may be disclosed in this response."
        )
        cue_text = (
            ", ".join(response_plan.active_emotional_cues)
            if response_plan.active_emotional_cues
            else "Maintain the current emotional tone without introducing a deeper cue."
        )
        blocked_count = len(response_plan.blocked_disclosure_keys)
        revealed_text = (
            "\n".join(f"- {item}" for item in response_plan.already_revealed_keys)
            or "- None yet."
        )
        plan_text = f"""

DETERMINISTIC RESPONSE PLAN
- Client stance: {response_plan.client_stance}
- Counselor effect: {response_plan.counselor_effect}
- Response to previous emotional cue: {response_plan.previous_cue_response or "not applicable"}
- Active emotional cue for this response: {cue_text}
- Maximum new disclosures: {response_plan.maximum_new_disclosures}

THE ONLY PERMITTED NEW DISCLOSURE
{disclosure_text}

LOCKED PRIVATE INFORMATION
- {blocked_count} future disclosure item(s) remain locked and have intentionally
  been omitted from this prompt. Do not invent or infer their content.
""".rstrip()
    else:
        disclosures = allowed_disclosures or ["No new hidden information may be disclosed."]
        disclosure_text = "\n".join(f"- {item}" for item in disclosures)
        revealed = state.revealed_information or ["None yet."]
        revealed_text = "\n".join(f"- {item}" for item in revealed)
        plan_text = f"""

ALLOWED DISCLOSURES FOR THIS NEXT RESPONSE
{disclosure_text}
""".rstrip()

    return f"""

RUNTIME CLIENT STATE
- Current engagement level: {state.engagement_level} of 5.
- Current trust level: {state.trust_level} of 5.
- Current emotional depth: {state.emotional_depth or 1} of 5.
- Recorded alliance ruptures: {state.rupture_count or 0}.
- Current disclosure stage: {state.disclosure_stage}.
- Current session stage: {state.session_stage}.

{plan_text}

ALREADY REVEALED INFORMATION
{revealed_text}

Follow the deterministic response plan strictly. Do not reveal deeper hidden
information unless it is the one permitted disclosure for this turn.
""".strip()
