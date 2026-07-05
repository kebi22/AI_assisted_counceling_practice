"""Evaluation agent: scores a transcript against the Module 1 rubric via Gemini."""

from __future__ import annotations

import json
from typing import Any

from pydantic import ValidationError

from app.ai.client import GeminiClient, gemini_client
from app.ai.prompts.module1_evaluator import MODULE1_EVALUATOR_SYSTEM_PROMPT
from app.core.config import settings
from app.core.exceptions import AIServiceError, EvaluationValidationError
from app.core.logging import get_logger
from app.schemas.evaluation import EvaluationResult, RubricCriterionScore, TranscriptEvidence

logger = get_logger(__name__)


class EvaluationAgent:
    """Requests structured rubric feedback for a completed transcript."""

    def __init__(self, client: GeminiClient | None = None) -> None:
        self._client = client or gemini_client

    async def evaluate(
        self,
        *,
        transcript: str,
        rubric: dict[str, Any],
        system_prompt: str | None = None,
        template_metadata: dict[str, Any] | None = None,
        learning_objectives: list[Any] | None = None,
        state_history: list[Any] | None = None,
        simulation_fidelity: dict[str, Any] | None = None,
        session_id: str | None = None,
    ) -> EvaluationResult:
        """Return a validated ``EvaluationResult`` for the transcript."""
        prompt = self._build_prompt(
            transcript=transcript,
            rubric=rubric,
            template_metadata=template_metadata or {},
            learning_objectives=learning_objectives or [],
            state_history=state_history or [],
            simulation_fidelity=simulation_fidelity or {},
        )
        try:
            result = await self._client.generate_structured(
                model=settings.gemini_evaluator_model,
                system_instruction=system_prompt or MODULE1_EVALUATOR_SYSTEM_PROMPT,
                prompt=prompt,
                schema=EvaluationResult,
                session_id=session_id,
            )
        except AIServiceError:
            logger.warning(
                "Evaluation agent using fallback report for session_id=%s",
                session_id or "-",
            )
            return self._apply_observability(
                result=self._fallback_evaluation(
                    transcript=transcript,
                    rubric=rubric,
                ),
                rubric=rubric,
            )
        except ValidationError as exc:
            raise EvaluationValidationError(
                "The AI evaluation did not match the required structure."
            ) from exc

        return self._apply_observability(result=result, rubric=rubric)

    @staticmethod
    def _fallback_evaluation(*, transcript: str, rubric: dict[str, Any]) -> EvaluationResult:
        rubric_scores: dict[str, RubricCriterionScore] = {}
        for key, item in rubric.items():
            if isinstance(item, dict):
                label = item.get("label") or key.replace("_", " ").title()
                description = item.get("description") or ""
                max_score = int(item.get("max_score") or 5)
            else:
                label = key.replace("_", " ").title()
                description = str(item)
                max_score = 5
            rubric_scores[key] = RubricCriterionScore(
                score=min(4, max_score),
                max_score=max_score,
                label=label,
                description=description,
                feedback=(
                    "Preliminary fallback score because the AI evaluator timed out. "
                    "A faculty review is recommended for the final interpretation."
                ),
            )

        student_lines = [
            line.split(":", 1)[1].strip()
            for line in transcript.splitlines()
            if line.startswith("Counselor (student):") and ":" in line
        ]
        quote = student_lines[0] if student_lines else "Student responses were present."
        return EvaluationResult(
            overall_score=3.5,
            rubric_scores=rubric_scores,
            strengths=[
                "You stayed engaged with the client and continued the conversation long enough to support practice feedback.",
                "Your responses appeared to invite further sharing rather than ending the conversation prematurely.",
            ],
            areas_for_growth=[
                "Because the AI evaluator timed out, ask faculty to review the transcript for precise skill-level feedback.",
                "Continue focusing on empathy, reflection of feeling and meaning, pacing, and emotional exploration.",
            ],
            evidence_from_transcript=[
                TranscriptEvidence(
                    quote=quote,
                    feedback=(
                        "This quote is included as a starting point for review. "
                        "The automated evaluator could not complete a full evidence analysis."
                    ),
                )
            ],
            suggested_improved_response=(
                "It sounds like this has been weighing on you deeply. Could we slow down "
                "and stay with what feels most painful or important right now?"
            ),
            faculty_review_recommended=True,
            specialized_analyses={
                "fallback_notice": (
                    "The AI evaluator timed out, so this report was generated by a conservative "
                    "server-side fallback and should be reviewed by faculty."
                )
            },
            missed_opportunities=[],
        )

    @staticmethod
    def _build_prompt(
        *,
        transcript: str,
        rubric: dict[str, Any],
        template_metadata: dict[str, Any],
        learning_objectives: list[Any],
        state_history: list[Any],
        simulation_fidelity: dict[str, Any] | None = None,
    ) -> str:
        return (
            "Evaluate the following counseling practice transcript using the provided "
            "scenario rubric, learning objectives, and client-state history. Score each "
            "observable rubric dimension from 1 to 5 and provide specific, supportive feedback "
            "grounded in the student's actual words.\n\n"
            "Return one JSON object only, with no Markdown fences or prose outside JSON. "
            "Use this exact top-level shape: overall_score (number 1-5), rubric_scores "
            "(object keyed by rubric criterion key; each value has score, max_score, "
            "label, description, feedback; score is null when not observable), strengths (array of strings), "
            "areas_for_growth (array of strings), evidence_from_transcript (array of "
            "objects with quote and feedback), suggested_improved_response (string), "
            "faculty_review_recommended (boolean), specialized_analyses (object), and "
            "missed_opportunities (array of objects).\n\n"
            f"Template metadata:\n{json.dumps(template_metadata, indent=2)}\n\n"
            f"Rubric:\n{json.dumps(rubric, indent=2)}\n\n"
            f"Learning objectives:\n{json.dumps(learning_objectives, indent=2)}\n\n"
            f"Client state history:\n{json.dumps(state_history, indent=2)}\n\n"
            "The following simulation-fidelity audit describes the simulated client's "
            "adherence to its state machine. Do not use it to reward or penalize the student's "
            "competency score; report it separately under specialized_analyses if useful.\n"
            f"Simulation fidelity:\n{json.dumps(simulation_fidelity or {}, indent=2)}\n\n"
            f"Transcript:\n{transcript}\n"
        )

    @staticmethod
    def _apply_observability(
        *, result: EvaluationResult, rubric: dict[str, Any]
    ) -> EvaluationResult:
        for key, criterion in rubric.items():
            if not isinstance(criterion, dict) or not criterion.get(
                "optional_when_not_observable"
            ):
                continue
            score = result.rubric_scores.get(key)
            if score is None:
                continue
            score.score = None
            score.feedback = (
                "Not observable in this text-only simulation. This criterion was excluded "
                "from the overall score."
            )
        weighted: list[tuple[float, float]] = []
        for key, score in result.rubric_scores.items():
            if score.score is None:
                continue
            criterion = rubric.get(key) if isinstance(rubric, dict) else None
            weight = float(criterion.get("weight") or 1) if isinstance(criterion, dict) else 1.0
            weighted.append(((score.score / score.max_score) * 5, weight))
        if weighted:
            result.overall_score = round(
                sum(value * weight for value, weight in weighted)
                / sum(weight for _, weight in weighted),
                2,
            )
        return result


evaluation_agent = EvaluationAgent()
