"""Validate generated client text against its deterministic response plan."""

from __future__ import annotations

import re

from app.schemas.scenario_authoring import DisclosureItem, ScenarioAuthoringData
from app.schemas.turn_pipeline import ClientResponsePlan, ClientResponseValidation
from app.schemas.turn_pipeline import SemanticSafetyFinding
from app.utils.scenario_state import all_disclosure_items, disclosure_key


_STOP_WORDS = {
    "about", "after", "again", "because", "being", "feels", "from", "have",
    "into", "just", "like", "more", "really", "sarah", "that", "their", "there",
    "they", "this", "with", "work", "would",
}

_CUE_ALIASES = {
    "stress": ("stress",),
    "frustration": ("frustrat",),
    "overwhelm": ("overwhelm", "too much"),
    "fatigue": ("tired", "drained", "exhaust", "running on empty"),
    "guilt": ("guilt", "letting people down", "disappoint"),
    "self-doubt": ("doubt", "question myself", "not good enough"),
    "identity concerns": ("myself", "who i am", "parts of myself"),
    "emotional exhaustion": ("nothing left", "running on empty", "drained", "exhaust"),
}

_EXPLICIT_SAFETY_RE = re.compile(
    r"\b(kill myself|hurt myself|harm myself|end my life|suicide|kill someone|hurt someone)\b",
    re.IGNORECASE,
)


class ClientResponseValidator:
    """Deterministic first-line guard; replaceable by a semantic validator later."""

    def validate(
        self,
        *,
        response: str,
        plan: ClientResponsePlan,
        scenario: ScenarioAuthoringData,
    ) -> ClientResponseValidation:
        detected = [
            disclosure_key(item)
            for item in all_disclosure_items(scenario)
            if self._matches_disclosure(response, item)
        ]
        permitted = set(plan.already_revealed_keys)
        if plan.selected_disclosure_key:
            permitted.add(plan.selected_disclosure_key)
        unauthorized = [key for key in detected if key not in permitted]
        cues = [
            cue
            for cue in plan.active_emotional_cues
            if self._matches_cue(response, cue)
        ]
        violations = [
            f"Generated response included locked disclosure '{key}'."
            for key in unauthorized
        ]
        explicit_safety = bool(_EXPLICIT_SAFETY_RE.search(response))
        ambiguous_phrase = next(
            (
                phrase
                for phrase in scenario.safety_rules.ambiguous_safety_phrases
                if phrase.casefold() in response.casefold()
            ),
            None,
        )
        if explicit_safety and not scenario.safety_rules.crisis_content_allowed:
            violations.append(
                "Generated response introduced explicit crisis or safety content that this scenario does not permit."
            )
        safety = SemanticSafetyFinding(
            status="explicit" if explicit_safety else "ambiguous" if ambiguous_phrase else "none",
            category="crisis_content" if explicit_safety else "faculty_configured_phrase" if ambiguous_phrase else None,
            confidence=1 if explicit_safety or ambiguous_phrase else 0,
            evidence=(
                _EXPLICIT_SAFETY_RE.search(response).group(0)
                if explicit_safety
                else ambiguous_phrase or ""
            ),
            reason=(
                "Matched explicit safety language."
                if explicit_safety
                else "Matched a faculty-configured ambiguous phrase."
                if ambiguous_phrase
                else ""
            ),
        )
        return ClientResponseValidation(
            accepted=not unauthorized and not (
                explicit_safety and not scenario.safety_rules.crisis_content_allowed
            ),
            detected_disclosure_keys=detected,
            detected_emotional_cues=cues,
            unauthorized_disclosure_keys=unauthorized,
            violations=violations,
            safety_finding=safety,
            requires_safety_clarification=bool(ambiguous_phrase),
        )

    @staticmethod
    def _meaningful_tokens(value: str) -> set[str]:
        return {
            token
            for token in re.findall(r"[a-z0-9']+", value.lower())
            if len(token) >= 4 and token not in _STOP_WORDS
        }

    def _matches_disclosure(self, response: str, item: DisclosureItem) -> bool:
        response_tokens = self._meaningful_tokens(response)
        disclosure_tokens = self._meaningful_tokens(
            f"{item.label} {item.content_summary}"
        )
        if not disclosure_tokens:
            return False
        overlap = response_tokens & disclosure_tokens
        threshold = 1 if len(disclosure_tokens) <= 3 else 2
        return len(overlap) >= threshold and len(overlap) / len(disclosure_tokens) >= 0.35

    @staticmethod
    def _matches_cue(response: str, cue: str) -> bool:
        lowered = response.lower()
        aliases = _CUE_ALIASES.get(cue.lower(), (cue.lower(),))
        return any(alias in lowered for alias in aliases)


client_response_validator = ClientResponseValidator()
