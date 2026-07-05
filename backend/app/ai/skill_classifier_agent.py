"""Hybrid semantic counselor-behavior classification boundary."""

from __future__ import annotations

import re
import json

from pydantic import BaseModel, Field

from app.ai.client import GeminiClient, gemini_client
from app.ai.output_models import ConversationMessage
from app.core.config import settings
from app.core.exceptions import AIServiceError
from app.core.logging import get_logger

logger = get_logger(__name__)

_QUESTION_RE = re.compile(r"\?")
_OPEN_QUESTION_RE = re.compile(
    r"\b(what|how|where|when|tell me|say more|can you share|could you share)\b",
    re.IGNORECASE,
)
_CLOSED_QUESTION_RE = re.compile(
    r"\b(do|did|does|is|are|was|were|can|could|would|have|has|will|should)\b",
    re.IGNORECASE,
)
_ADVICE_RE = re.compile(
    r"\b(you should|you need to|try to|have you tried|why don't you|the solution)\b",
    re.IGNORECASE,
)
_EMPATHY_RE = re.compile(
    r"\b(sounds like|seems like|that sounds|i hear|i can understand|must be|"
    r"overwhelming|hard|difficult|stressful|exhausting)\b",
    re.IGNORECASE,
)
_VALIDATION_RE = re.compile(
    r"\b(makes sense|understandable|valid|no wonder|given everything)\b",
    re.IGNORECASE,
)
_FEELING_RE = re.compile(
    r"\b(feel|feeling|felt|sad|angry|afraid|scared|worried|overwhelmed|"
    r"anxious|stressed|exhausted|drained|frustrated)\b",
    re.IGNORECASE,
)

ATOMIC_BEHAVIOR_KEYS = (
    "accurate_empathy",
    "reflection_of_feeling",
    "reflection_of_meaning",
    "open_ended_question",
    "validation",
    "emotional_exploration",
    "appropriate_processing_space",
    "premature_advice",
    "rapid_fire_questions",
    "excessive_questioning",
    "frequent_topic_shift",
    "early_problem_solving",
)
DERIVED_BEHAVIOR_KEYS = (
    "cue_acknowledgment",
    "cue_deepening",
    "therapeutic_presence",
    "rapport_building",
    "pacing",
    "ignored_emotional_cue",
)
SUPPORTED_RUNTIME_BEHAVIOR_KEYS = frozenset(
    (*ATOMIC_BEHAVIOR_KEYS, *DERIVED_BEHAVIOR_KEYS)
)


class CounselorBehaviorDetection(BaseModel):
    """Normalized behavior labels used by deterministic state transitions."""

    accurate_empathy: bool = False
    reflection_of_feeling: bool = False
    reflection_of_meaning: bool = False
    open_ended_question: bool = False
    validation: bool = False
    emotional_exploration: bool = False
    appropriate_processing_space: bool = False
    premature_advice: bool = False
    rapid_fire_questions: bool = False
    excessive_questioning: bool = False
    frequent_topic_shift: bool = False
    early_problem_solving: bool = False
    question_count: int = 0
    labels: list[str] = Field(default_factory=list)
    evidence: dict[str, str] = Field(default_factory=dict)
    analyzer: str = "deterministic-pattern-v1"


class SemanticCounselorAnalysis(BaseModel):
    """Sparse semantic findings; deterministic code still owns state changes."""

    accurate_empathy: bool = False
    reflection_of_feeling: bool = False
    reflection_of_meaning: bool = False
    open_ended_question: bool = False
    validation: bool = False
    emotional_exploration: bool = False
    appropriate_processing_space: bool = False
    premature_advice: bool = False
    rapid_fire_questions: bool = False
    excessive_questioning: bool = False
    frequent_topic_shift: bool = False
    early_problem_solving: bool = False
    evidence: dict[str, str] = Field(default_factory=dict)


class SkillClassifierAgent:
    """Classifies one student turn into counseling behavior labels."""

    def __init__(self, client: GeminiClient | None = None) -> None:
        self._client = client or gemini_client

    async def classify(
        self,
        *,
        content: str,
        conversation: list[ConversationMessage],
        semantic: bool = True,
    ) -> CounselorBehaviorDetection:
        deterministic = self.classify_deterministically(content=content)
        if not semantic:
            return deterministic
        try:
            analysis = await self._client.generate_structured(
                model=settings.gemini_client_model,
                system_instruction=(
                    "You classify a counselor-in-training's single response by therapeutic "
                    "function and meaning. Use the immediately preceding client statement as "
                    "context. Do not reward the mere presence of feeling words: a reflection "
                    "must accurately return the client's experience. Return JSON only."
                ),
                prompt=self._semantic_prompt(content=content, conversation=conversation),
                schema=SemanticCounselorAnalysis,
                enforce_schema=True,
            )
        except AIServiceError:
            logger.warning("Semantic counselor classifier using deterministic fallback")
            return deterministic

        detection = CounselorBehaviorDetection(
            **analysis.model_dump(exclude={"evidence"}),
            question_count=deterministic.question_count,
            evidence=analysis.evidence,
            analyzer="gemini-semantic-counselor-v1",
        )
        detection.labels = SkillClassifierAgent._labels(detection)
        return detection

    @staticmethod
    def classify_deterministically(*, content: str) -> CounselorBehaviorDetection:
        text = content.strip()
        question_count = len(_QUESTION_RE.findall(text))
        has_open_question = bool(_OPEN_QUESTION_RE.search(text))
        has_closed_question = bool(_CLOSED_QUESTION_RE.search(text)) and question_count > 0
        has_empathy = bool(_EMPATHY_RE.search(text))
        has_validation = bool(_VALIDATION_RE.search(text))
        has_feeling = bool(_FEELING_RE.search(text))
        has_advice = bool(_ADVICE_RE.search(text))

        detection = CounselorBehaviorDetection(
            accurate_empathy=has_empathy,
            reflection_of_feeling=has_empathy and has_feeling,
            reflection_of_meaning=has_empathy and not question_count,
            open_ended_question=has_open_question and question_count > 0,
            validation=has_validation,
            emotional_exploration=has_feeling and has_open_question,
            appropriate_processing_space=question_count == 0 and len(text.split()) <= 24,
            premature_advice=has_advice,
            rapid_fire_questions=question_count >= 3,
            excessive_questioning=question_count >= 2 and not (has_empathy or has_validation),
            frequent_topic_shift="anyway" in text.lower(),
            early_problem_solving=has_advice or (has_closed_question and "fix" in text.lower()),
            question_count=question_count,
        )
        detection.labels = SkillClassifierAgent._labels(detection)
        return detection

    @staticmethod
    def _semantic_prompt(
        *, content: str, conversation: list[ConversationMessage]
    ) -> str:
        prior_client = next(
            (
                turn.content
                for turn in reversed(conversation[:-1])
                if str(turn.speaker.value if hasattr(turn.speaker, "value") else turn.speaker)
                == "client"
            ),
            "",
        )
        payload = {
            "immediately_preceding_client_statement": prior_client,
            "counselor_response": content,
        }
        return (
            "Classify only behaviors clearly demonstrated in the counselor response. "
            "For every true behavior, include a short exact quote in evidence keyed by "
            "the behavior name. Distinguish open exploration from questioning, validation "
            "from generic reassurance, and reflection of meaning from paraphrase. Mark "
            "premature advice or problem solving when the response moves to solutions before "
            "sufficient emotional exploration. Mark processing space only when the response "
            "is a deliberate brief invitation or therapeutic pause, not merely any short text.\n\n"
            f"Input:\n{json.dumps(payload, indent=2)}"
        )

    @staticmethod
    def _labels(detection: CounselorBehaviorDetection) -> list[str]:
        return [
            field
            for field in ATOMIC_BEHAVIOR_KEYS
            if getattr(detection, field)
        ]


skill_classifier_agent = SkillClassifierAgent()
