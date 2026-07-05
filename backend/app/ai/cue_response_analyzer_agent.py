"""Semantic analysis of how a counselor responds to one active emotional cue."""

from __future__ import annotations

import json
from typing import Any

from app.ai.client import GeminiClient, gemini_client
from app.ai.output_models import ConversationMessage
from app.core.config import settings
from app.core.exceptions import AIServiceError
from app.core.logging import get_logger
from app.db.models.session_state import SessionState
from app.schemas.scenario_authoring import ScenarioAuthoringData
from app.schemas.turn_pipeline import CueResponseAnalysis

logger = get_logger(__name__)

_MIN_CONFIDENCE = 0.72
_ACTIVE_STATUSES = {"presented", "unresolved", "missed"}

_SYSTEM_PROMPT = """You are an internal semantic evaluator for a counseling simulation.
Judge only whether the counselor's latest response meaningfully addresses the exact active
emotional cue shown in the input. Do not grant acknowledgment merely because the response
sounds empathic or mentions a different emotion. Ground every positive judgment in an exact
quote from the counselor response. Return only the requested JSON object.
"""


class CueResponseAnalyzer:
    """Produces cue-specific semantic evidence; it never changes state itself."""

    def __init__(self, client: GeminiClient | None = None) -> None:
        self._client = client or gemini_client

    async def analyze(
        self,
        *,
        counselor_response: str,
        conversation: list[ConversationMessage],
        state: SessionState,
        scenario: ScenarioAuthoringData,
        semantic: bool = True,
        session_id: str | None = None,
    ) -> CueResponseAnalysis:
        active = self.active_cue(state=state, scenario=scenario)
        if active is None:
            return CueResponseAnalysis(
                status="no_active_cue",
                rationale="No unresolved emotional cue was active before this counselor turn.",
            )
        if not semantic:
            return self._unresolved(active, "Semantic cue analysis was disabled for this replay.")

        try:
            analysis = await self._client.generate_structured(
                model=settings.gemini_client_model,
                system_instruction=_SYSTEM_PROMPT,
                prompt=self._build_prompt(
                    active=active,
                    counselor_response=counselor_response,
                    conversation=conversation,
                ),
                schema=CueResponseAnalysis,
                enforce_schema=True,
                session_id=session_id,
            )
        except AIServiceError:
            logger.warning(
                "Cue response analyzer using conservative unresolved fallback session_id=%s",
                session_id or "-",
            )
            return self._unresolved(active, "The semantic cue analyzer was unavailable.")

        if (
            analysis.cue is not None
            and analysis.cue.casefold() != str(active["cue"]).casefold()
        ):
            return self._unresolved(active, "The semantic result referenced a different cue.")
        if analysis.confidence < _MIN_CONFIDENCE:
            return self._unresolved(
                active,
                f"Semantic confidence {analysis.confidence:.2f} was below {_MIN_CONFIDENCE:.2f}.",
            )
        return analysis.model_copy(
            update={
                "cue": str(active["cue"]),
                "cue_key": active.get("beat_key"),
                "client_evidence": analysis.client_evidence
                or str(active.get("client_evidence") or ""),
                "analyzer": "gemini-cue-grounding-v1",
            }
        )

    @staticmethod
    def active_cue(
        *, state: SessionState, scenario: ScenarioAuthoringData
    ) -> dict[str, Any] | None:
        for raw in reversed(state.emotional_cues):
            if not isinstance(raw, dict) or raw.get("status") not in _ACTIVE_STATUSES:
                continue
            cue = raw.get("cue")
            if not cue:
                continue
            item = dict(raw)
            beat = next(
                (
                    candidate
                    for candidate in scenario.progression_beats
                    if (
                        candidate.key == item.get("beat_key")
                        or (
                            not item.get("beat_key")
                            and cue in candidate.emotional_cues
                            and candidate.key in set(state.revealed_information)
                        )
                    )
                ),
                None,
            )
            if beat:
                item["beat_key"] = beat.key
                item["private_meaning"] = beat.private_meaning
            return item
        return None

    @staticmethod
    def _unresolved(active: dict[str, Any], rationale: str) -> CueResponseAnalysis:
        return CueResponseAnalysis(
            cue=str(active["cue"]),
            cue_key=active.get("beat_key"),
            status="uncertain",
            confidence=0,
            client_evidence=str(active.get("client_evidence") or ""),
            rationale=rationale,
        )

    @staticmethod
    def _build_prompt(
        *,
        active: dict[str, Any],
        counselor_response: str,
        conversation: list[ConversationMessage],
    ) -> str:
        recent = [
            {
                "speaker": str(
                    turn.speaker.value if hasattr(turn.speaker, "value") else turn.speaker
                ),
                "content": turn.content,
            }
            for turn in conversation[-4:]
        ]
        payload = {
            "active_cue": {
                "cue": active.get("cue"),
                "cue_key": active.get("beat_key"),
                "private_meaning": active.get("private_meaning"),
                "client_evidence": active.get("client_evidence"),
                "prior_status": active.get("status"),
            },
            "counselor_response": counselor_response,
            "recent_conversation": recent,
        }
        return (
            "Classify the relationship between the counselor response and the exact active cue.\n\n"
            "Statuses:\n"
            "- ignored: does not address the cue.\n"
            "- topic_only: discusses the general topic but not the cue's emotion or meaning.\n"
            "- acknowledged: explicitly recognizes the cue without accurately reflecting its meaning.\n"
            "- accurately_reflected: accurately returns the cue's emotion or personal meaning.\n"
            "- deepened: accurately addresses the cue and invites or adds deeper exploration.\n"
            "- misattuned: assigns an unsupported emotion or meaning.\n"
            "- redirected: moves away from the cue toward another topic, facts, advice, or solutions.\n"
            "- uncertain: evidence is insufficient.\n\n"
            "Return cue, cue_key, status, confidence, client_evidence, counselor_evidence, "
            "rationale, and analyzer. counselor_evidence must be an exact quote.\n\n"
            f"Input:\n{json.dumps(payload, indent=2)}"
        )


cue_response_analyzer = CueResponseAnalyzer()
