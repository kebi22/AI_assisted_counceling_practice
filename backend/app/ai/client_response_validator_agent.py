"""Semantic disclosure and emotional-cue validation for generated client text."""

from __future__ import annotations

import json

from app.ai.client import GeminiClient, gemini_client
from app.core.config import settings
from app.core.exceptions import AIServiceError
from app.core.logging import get_logger
from app.schemas.scenario_authoring import ScenarioAuthoringData
from app.schemas.turn_pipeline import (
    ClientResponsePlan,
    ClientResponseValidation,
    SemanticClientResponseAnalysis,
)
from app.services.client_response_validator import (
    ClientResponseValidator,
    client_response_validator,
)
from app.utils.scenario_state import all_disclosure_items, disclosure_key


logger = get_logger(__name__)

_REVEALED_STATUSES = {"substantially_revealed", "explicitly_revealed"}
_DETECTED_CONFIDENCE = 0.80
_AMBIGUOUS_CONFIDENCE = 0.55
_CUE_CONFIDENCE = 0.65

_SYSTEM_PROMPT = """You are an internal semantic boundary checker for a counseling simulation.
You do not roleplay, counsel, score the student, or generate client dialogue.
Determine what the generated client response actually communicates by meaning.
Do not classify a disclosure as revealed merely because it shares a topic or vocabulary.
A disclosure is substantially revealed only when the response communicates its essential
private claim. Quote exact response evidence. Return only the requested JSON object.
"""


class SemanticClientResponseValidator:
    """Uses semantic entailment while keeping deterministic permission authoritative."""

    def __init__(
        self,
        client: GeminiClient | None = None,
        fallback: ClientResponseValidator | None = None,
    ) -> None:
        self._client = client or gemini_client
        self._fallback = fallback or client_response_validator

    async def validate(
        self,
        *,
        response: str,
        plan: ClientResponsePlan,
        scenario: ScenarioAuthoringData,
        session_id: str | None = None,
    ) -> ClientResponseValidation:
        try:
            analysis = await self._client.generate_structured(
                model=settings.gemini_client_model,
                system_instruction=_SYSTEM_PROMPT,
                prompt=self._build_prompt(
                    response=response,
                    plan=plan,
                    scenario=scenario,
                ),
                schema=SemanticClientResponseAnalysis,
                enforce_schema=True,
                session_id=session_id,
            )
        except AIServiceError:
            logger.warning(
                "Semantic response validator using deterministic fallback session_id=%s",
                session_id or "-",
            )
            return self.validate_deterministically(
                response=response,
                plan=plan,
                scenario=scenario,
            )
        analysis = self._normalize_analysis(analysis=analysis, scenario=scenario)
        if not self._analysis_keys_valid(analysis=analysis, scenario=scenario):
            logger.warning(
                "Semantic response validator returned unknown keys; using deterministic fallback session_id=%s",
                session_id or "-",
            )
            return self.validate_deterministically(
                response=response,
                plan=plan,
                scenario=scenario,
            )
        return self._apply_permission_policy(
            analysis=analysis,
            plan=plan,
            scenario=scenario,
        )

    def validate_deterministically(
        self,
        *,
        response: str,
        plan: ClientResponsePlan,
        scenario: ScenarioAuthoringData,
    ) -> ClientResponseValidation:
        return self._fallback.validate(
            response=response,
            plan=plan,
            scenario=scenario,
        )

    @staticmethod
    def _normalize_analysis(
        *, analysis: SemanticClientResponseAnalysis, scenario: ScenarioAuthoringData
    ) -> SemanticClientResponseAnalysis:
        canonical_cues = {
            cue.casefold(): cue
            for item in scenario.emotional_cue_progression
            for cue in item.emotional_cues
        }
        normalized = analysis.model_copy(deep=True)
        for finding in normalized.cues:
            finding.cue = canonical_cues.get(finding.cue.casefold(), finding.cue)
        return normalized

    @staticmethod
    def _analysis_keys_valid(
        *, analysis: SemanticClientResponseAnalysis, scenario: ScenarioAuthoringData
    ) -> bool:
        expected_disclosures = {
            disclosure_key(item) for item in all_disclosure_items(scenario)
        }
        returned_disclosures = {
            item.disclosure_key for item in analysis.disclosures
        }
        expected_cues = {
            cue
            for item in scenario.emotional_cue_progression
            for cue in item.emotional_cues
        }
        returned_cues = {item.cue for item in analysis.cues}
        return (
            returned_disclosures <= expected_disclosures
            and returned_cues <= expected_cues
        )

    @staticmethod
    def _apply_permission_policy(
        *,
        analysis: SemanticClientResponseAnalysis,
        plan: ClientResponsePlan,
        scenario: ScenarioAuthoringData,
    ) -> ClientResponseValidation:
        detected = [
            item.disclosure_key
            for item in analysis.disclosures
            if item.status in _REVEALED_STATUSES
            and item.confidence >= _DETECTED_CONFIDENCE
        ]
        ambiguous = [
            item.disclosure_key
            for item in analysis.disclosures
            if item.status in _REVEALED_STATUSES
            and _AMBIGUOUS_CONFIDENCE <= item.confidence < _DETECTED_CONFIDENCE
        ]
        permitted = set(plan.already_revealed_keys)
        if plan.selected_disclosure_key:
            permitted.add(plan.selected_disclosure_key)
        unauthorized = [key for key in detected if key not in permitted]
        ambiguous_locked = [key for key in ambiguous if key not in permitted]
        cues = [
            item.cue
            for item in analysis.cues
            if item.status in {"expressed", "deepened"}
            and item.confidence >= _CUE_CONFIDENCE
        ]
        revealed_or_selected = set(plan.already_revealed_keys)
        if plan.selected_disclosure_key:
            revealed_or_selected.add(plan.selected_disclosure_key)
        flexible_cues = {
            cue
            for beat in scenario.progression_beats
            if beat.key in revealed_or_selected
            for cue in beat.emotional_cues
        }
        permitted_cues = set(plan.permitted_emotional_cues) | flexible_cues
        unauthorized_cues = [cue for cue in cues if cue not in permitted_cues]
        violations = [
            f"Semantic validation found locked disclosure '{key}'."
            for key in unauthorized
        ]
        violations.extend(
            f"Semantic validation was ambiguous about locked disclosure '{key}'."
            for key in ambiguous_locked
        )
        violations.extend(
            f"Semantic validation found locked emotional cue '{cue}'."
            for cue in unauthorized_cues
        )
        explicit_safety_violation = (
            analysis.safety.status == "explicit"
            and analysis.safety.confidence >= _DETECTED_CONFIDENCE
            and not scenario.safety_rules.crisis_content_allowed
        )
        if explicit_safety_violation:
            violations.append(
                "Generated response introduced explicit crisis or safety content that this scenario does not permit."
            )
        requires_clarification = (
            analysis.safety.status == "ambiguous"
            and analysis.safety.confidence >= _AMBIGUOUS_CONFIDENCE
        )
        return ClientResponseValidation(
            accepted=(
                not unauthorized
                and not ambiguous_locked
                and not unauthorized_cues
                and not explicit_safety_violation
            ),
            detected_disclosure_keys=detected,
            detected_emotional_cues=cues,
            unauthorized_emotional_cues=unauthorized_cues,
            unauthorized_disclosure_keys=unauthorized,
            ambiguous_disclosure_keys=ambiguous_locked,
            violations=violations,
            disclosure_findings=analysis.disclosures,
            cue_findings=analysis.cues,
            safety_finding=analysis.safety,
            requires_safety_clarification=requires_clarification,
            validator="gemini-semantic-entailment-v1",
        )

    @staticmethod
    def _build_prompt(
        *,
        response: str,
        plan: ClientResponsePlan,
        scenario: ScenarioAuthoringData,
    ) -> str:
        beat_by_key = {beat.key: beat for beat in scenario.progression_beats}
        disclosures = []
        for item in all_disclosure_items(scenario):
            key = disclosure_key(item)
            beat = beat_by_key.get(key)
            disclosures.append(
                {
                    "key": key,
                    "label": item.label,
                    "private_claim": item.content_summary,
                    "semantic_claims": beat.semantic_claims if beat else [item.content_summary],
                }
            )
        cue_definitions = [
            {
                "session_stage": item.session_stage,
                "cues": item.emotional_cues,
                "example_statements": item.example_statements,
            }
            for item in scenario.emotional_cue_progression
        ]
        payload = {
            "generated_client_response": response,
            "selected_disclosure_key": plan.selected_disclosure_key,
            "already_revealed_keys": plan.already_revealed_keys,
            "active_cue_candidates": plan.active_emotional_cues,
            "permitted_cues": plan.permitted_emotional_cues,
            "cue_definitions": cue_definitions,
            "disclosure_definitions": disclosures,
            "safety_policy": scenario.safety_rules.model_dump(),
        }
        return (
            "Analyze the generated response against every disclosure definition and active "
            "cue candidate. Distinguish topical similarity from semantic entailment.\n\n"
            "Disclosure statuses: not_present, related_only, partially_implied, "
            "substantially_revealed, explicitly_revealed.\n"
            "Cue statuses: not_present, expressed, deepened.\n\n"
            "Confidence may be returned as a decimal from 0.0 to 1.0.\n\n"
            "Return this exact JSON shape: disclosures (array of objects with "
            "disclosure_key, status, confidence, evidence, reason) and cues (array of "
            "objects with cue, status, confidence, evidence, reason), and safety (one "
            "object with status, category, confidence, evidence, reason). Safety status "
            "is ambiguous when wording reasonably requires direct clarification but does "
            "not itself state current danger, self-harm, harm to others, abuse, or crisis; "
            "explicit means the response clearly communicates one of those concerns. Return findings "
            "only for disclosures whose status is related_only or stronger and cues whose "
            "status is expressed or deepened. Omit not_present items. Evidence must be an "
            "exact quote from the generated response.\n\n"
            f"Validation input:\n{json.dumps(payload, indent=2)}"
        )


semantic_client_response_validator = SemanticClientResponseValidator()
