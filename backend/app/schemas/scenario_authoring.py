"""Structured faculty-authoring input models and the prompt builder's output.

These mirror the Scenario Builder fields in ``promptbuilding.md``. The aggregate
``ScenarioAuthoringData`` is the canonical, human-entered source of truth; the
generated prompt is derived from it and kept separately so prompts can be
regenerated without losing faculty input.

Most nested fields are optional so an in-progress draft can still be assembled
into a preview prompt. Hard publish-time validation lives in the authoring
service, not here.
"""

from __future__ import annotations

import uuid
import re
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, ValidationInfo, field_validator, model_validator

from app.schemas.common import ORMModel

Difficulty = Literal["easy", "medium", "hard"]


class ClientIdentity(BaseModel):
    name: str
    age: str | None = None
    pronouns: str | None = None
    occupation: str | None = None
    background: str | None = None
    identity_information: str | None = None


class PresentingConcern(BaseModel):
    primary_concern: str
    secondary_concern: str | None = None
    reason_for_attending: str | None = None
    client_explanation: str | None = None
    hoped_change: str | None = None


class CulturalConsiderations(BaseModel):
    cultural_factors: str | None = None
    language_preferences: str | None = None
    relevant_values: str | None = None
    concerns_about_counselor: str | None = None
    communication_preferences: str | None = None
    sensitive_topics: list[str] = Field(default_factory=list)


class ResistanceConfiguration(BaseModel):
    level: int = Field(default=2, ge=1, le=5)
    starting_engagement_level: int = Field(default=2, ge=1, le=5)
    minimum_engagement_level: int = Field(default=1, ge=1, le=5)
    maximum_engagement_level: int = Field(default=5, ge=1, le=5)
    trust_development_speed: Literal["slow", "moderate", "fast"] = "moderate"
    increases_when: str | None = None
    decreases_when: str | None = None
    trust_development: str | None = None
    behaviors_to_resist: list[str] = Field(default_factory=list)


class EngagementLevelDescription(BaseModel):
    level: int = Field(..., ge=1, le=5)
    label: str
    description: str
    typical_response: str | None = None


class ClientBehaviorRule(BaseModel):
    counselor_behavior: str
    behavior_key: str | None = None
    client_response: str
    engagement_change: int = Field(default=0, ge=-5, le=5)


class EmotionalCueRule(BaseModel):
    session_stage: Literal["early", "mid", "later"]
    emotional_cues: list[str] = Field(default_factory=list)
    example_statements: list[str] = Field(default_factory=list)


class SilenceResponseRule(BaseModel):
    counselor_use_of_silence: str
    client_response: str
    engagement_change: int = Field(default=0, ge=-5, le=5)


class CounselorSkillRule(BaseModel):
    skill: str
    behavior_key: str | None = None
    behavioral_indicator: str
    expected_client_reaction: str


class SessionSuccessIndicator(BaseModel):
    indicator: str
    evidence: str


class DisclosureItem(BaseModel):
    key: str | None = None
    label: str
    content_summary: str
    minimum_engagement_level: int = Field(default=1, ge=1, le=5)
    session_stage: Literal["early", "mid", "later"] = "early"
    requires_direct_question: bool = False
    faculty_only_notes: str | None = None


class DisclosureRules(BaseModel):
    immediate: list[DisclosureItem] = Field(default_factory=list)
    after_rapport: list[DisclosureItem] = Field(default_factory=list)
    on_direct_question: list[DisclosureItem] = Field(default_factory=list)
    never: list[str] = Field(default_factory=list)

    @field_validator("immediate", "after_rapport", "on_direct_question", mode="before")
    @classmethod
    def _coerce_disclosure_items(
        cls, value: list[object] | None, info: ValidationInfo
    ) -> list[object]:
        if value is None:
            return []
        defaults = {
            "immediate": {
                "minimum_engagement_level": 1,
                "session_stage": "early",
                "requires_direct_question": False,
            },
            "after_rapport": {
                "minimum_engagement_level": 3,
                "session_stage": "mid",
                "requires_direct_question": False,
            },
            "on_direct_question": {
                "minimum_engagement_level": 2,
                "session_stage": "early",
                "requires_direct_question": True,
            },
        }[info.field_name]
        coerced: list[object] = []
        for idx, item in enumerate(value):
            if isinstance(item, str):
                coerced.append(
                    {
                        "key": None,
                        "label": item,
                        "content_summary": item,
                        **defaults,
                        "faculty_only_notes": None,
                    }
                )
            elif isinstance(item, dict):
                content = item.get("content_summary") or item.get("label") or f"Disclosure {idx + 1}"
                coerced.append(
                    {
                        **defaults,
                        **item,
                        "label": item.get("label") or content,
                        "content_summary": content,
                    }
                )
            else:
                coerced.append(item)
        return coerced

    def is_empty(self) -> bool:
        return not (
            self.immediate or self.after_rapport or self.on_direct_question or self.never
        )


class ProgressionBeat(BaseModel):
    """One connected emotional cue and disclosure step in the client story."""

    key: str
    title: str
    session_stage: Literal["early", "mid", "later"] = "early"
    emotional_cues: list[str] = Field(default_factory=list)
    emotional_intensity: int = Field(default=1, ge=1, le=5)
    private_meaning: str | None = None
    disclosure_label: str | None = None
    disclosure_content: str | None = None
    semantic_claims: list[str] = Field(default_factory=list)
    example_expressions: list[str] = Field(default_factory=list)
    prerequisite_beat_keys: list[str] = Field(default_factory=list)
    minimum_trust_level: int = Field(default=1, ge=1, le=5)
    minimum_engagement_level: int = Field(default=1, ge=1, le=5)
    required_counselor_response: Literal[
        "any", "acknowledge_cue", "deepen_cue", "direct_question", "therapeutic_pause"
    ] = "any"
    trigger: Literal[
        "opening", "volunteer", "after_rapport", "direct_question", "after_reflection", "after_pause"
    ] = "volunteer"
    repeatable: bool = False
    required_for_completion: bool = False
    faculty_only_notes: str | None = None


class EmotionalTone(BaseModel):
    starting_tone: str | None = None
    possible_shifts: list[str] = Field(default_factory=list)
    typical_response_length: str | None = None
    communication_style: str | None = None
    intensity: str | None = None


class LearningObjective(BaseModel):
    name: str
    description: str | None = None


class RubricItem(BaseModel):
    category: str
    description: str | None = None
    max_score: int = Field(default=5, ge=1)
    weight: int = Field(default=0, ge=0, le=100)
    observable_indicators: list[str] = Field(default_factory=list)
    common_mistakes: list[str] = Field(default_factory=list)
    feedback_guidance: str | None = None
    rating_anchors: dict[str, str] = Field(default_factory=dict)
    optional_when_not_observable: bool = False


class CompetencyScaleBand(BaseModel):
    score_range: str
    competency_level: str


class EvaluationFocusSection(BaseModel):
    key: str
    title: str
    instructions: list[str] = Field(default_factory=list)


class SafetyRules(BaseModel):
    disallowed_topics: list[str] = Field(default_factory=list)
    max_emotional_intensity: str | None = None
    crisis_content_allowed: bool = False
    required_redirection: str | None = None
    ending_topics: list[str] = Field(default_factory=list)
    faculty_review_required: bool = False
    ambiguous_safety_phrases: list[str] = Field(default_factory=list)
    required_safety_clarification: str | None = None
    safety_review_triggers: list[str] = Field(default_factory=list)


class ScenarioAuthoringData(BaseModel):
    """Everything a faculty member enters to define one client scenario."""

    module_number: int = 1
    title: str
    description: str | None = None
    difficulty: Difficulty = "easy"
    estimated_turns: int | None = None
    # Optional first line the client says to open the session. If omitted, one is
    # derived from the presenting concern at publish time.
    opening_message: str | None = None

    client_identity: ClientIdentity
    presenting_concern: PresentingConcern
    cultural_considerations: CulturalConsiderations = Field(
        default_factory=CulturalConsiderations
    )
    resistance_configuration: ResistanceConfiguration = Field(
        default_factory=ResistanceConfiguration
    )
    engagement_levels: list[EngagementLevelDescription] = Field(default_factory=list)
    engagement_increase_rules: list[ClientBehaviorRule] = Field(default_factory=list)
    engagement_decrease_rules: list[ClientBehaviorRule] = Field(default_factory=list)
    disclosure_rules: DisclosureRules = Field(default_factory=DisclosureRules)
    progression_beats: list[ProgressionBeat] = Field(default_factory=list)
    emotional_cue_progression: list[EmotionalCueRule] = Field(default_factory=list)
    silence_response_rules: list[SilenceResponseRule] = Field(default_factory=list)
    counselor_skill_detection: list[CounselorSkillRule] = Field(default_factory=list)
    session_success_indicators: list[SessionSuccessIndicator] = Field(default_factory=list)
    emotional_tone: EmotionalTone = Field(default_factory=EmotionalTone)
    hidden_information: list[str] = Field(default_factory=list)
    learning_objectives: list[LearningObjective] = Field(default_factory=list)
    rubric: list[RubricItem] = Field(default_factory=list)
    competency_scale: list[CompetencyScaleBand] = Field(default_factory=list)
    evaluation_focus_sections: list[EvaluationFocusSection] = Field(default_factory=list)
    reflection_questions: list[str] = Field(default_factory=list)
    safety_rules: SafetyRules = Field(default_factory=SafetyRules)

    @model_validator(mode="before")
    @classmethod
    def _synchronize_progression_formats(cls, value: Any) -> Any:
        if not isinstance(value, dict):
            return value
        data = dict(value)
        beats = data.get("progression_beats") or []
        if beats:
            data["disclosure_rules"] = cls._legacy_disclosures_from_beats(
                beats,
                existing=data.get("disclosure_rules"),
            )
            data["emotional_cue_progression"] = cls._legacy_cues_from_beats(beats)
        else:
            data["progression_beats"] = cls._beats_from_legacy(
                data.get("disclosure_rules") or {},
                data.get("emotional_cue_progression") or [],
            )
        return data

    @staticmethod
    def _beats_from_legacy(disclosures: dict, cue_rules: list[dict]) -> list[dict]:
        cues_by_stage = {
            str(item.get("session_stage", "early")): list(item.get("emotional_cues") or [])
            for item in cue_rules
            if isinstance(item, dict)
        }
        beats: list[dict] = []
        groups = (
            ("immediate", "volunteer", "any"),
            ("after_rapport", "after_rapport", "any"),
            ("on_direct_question", "direct_question", "direct_question"),
        )
        for group, trigger, required_response in groups:
            for index, raw in enumerate(disclosures.get(group) or []):
                item = raw if isinstance(raw, dict) else {"label": str(raw), "content_summary": str(raw)}
                label = item.get("label") or item.get("content_summary") or "Disclosure"
                key = item.get("key") or re.sub(r"[^a-z0-9]+", "_", label.lower()).strip("_")
                stage = item.get("session_stage") or ("mid" if group == "after_rapport" else "early")
                beats.append(
                    {
                        "key": key or f"beat_{len(beats) + 1}",
                        "title": label,
                        "session_stage": stage,
                        "emotional_cues": cues_by_stage.get(stage, [])[:1],
                        "emotional_intensity": {"early": 2, "mid": 3, "later": 4}.get(stage, 2),
                        "private_meaning": item.get("faculty_only_notes"),
                        "disclosure_label": label,
                        "disclosure_content": item.get("content_summary") or label,
                        "semantic_claims": [item.get("content_summary") or label],
                        "example_expressions": [],
                        "prerequisite_beat_keys": [],
                        "minimum_trust_level": 1,
                        "minimum_engagement_level": item.get("minimum_engagement_level", 1),
                        "required_counselor_response": required_response,
                        "trigger": trigger,
                        "repeatable": False,
                        "required_for_completion": False,
                        "faculty_only_notes": item.get("faculty_only_notes"),
                    }
                )
        return beats

    @staticmethod
    def _legacy_disclosures_from_beats(beats: list[dict], existing: Any) -> dict:
        never = existing.get("never", []) if isinstance(existing, dict) else []
        result: dict[str, Any] = {
            "immediate": [],
            "after_rapport": [],
            "on_direct_question": [],
            "never": never,
        }
        for beat in beats:
            content = beat.get("disclosure_content")
            if not content:
                continue
            trigger = beat.get("trigger", "volunteer")
            group = (
                "on_direct_question"
                if trigger == "direct_question"
                else "after_rapport"
                if trigger in {"after_rapport", "after_reflection", "after_pause"}
                else "immediate"
            )
            result[group].append(
                {
                    "key": beat.get("key"),
                    "label": beat.get("disclosure_label") or beat.get("title") or beat.get("key"),
                    "content_summary": content,
                    "minimum_engagement_level": beat.get("minimum_engagement_level", 1),
                    "session_stage": beat.get("session_stage", "early"),
                    "requires_direct_question": trigger == "direct_question",
                    "faculty_only_notes": beat.get("faculty_only_notes") or beat.get("private_meaning"),
                }
            )
        return result

    @staticmethod
    def _legacy_cues_from_beats(beats: list[dict]) -> list[dict]:
        grouped: dict[str, dict[str, list[str]]] = {}
        for beat in beats:
            stage = beat.get("session_stage", "early")
            entry = grouped.setdefault(stage, {"cues": [], "examples": []})
            for cue in beat.get("emotional_cues") or []:
                if cue not in entry["cues"]:
                    entry["cues"].append(cue)
            for example in beat.get("example_expressions") or []:
                if example not in entry["examples"]:
                    entry["examples"].append(example)
        return [
            {
                "session_stage": stage,
                "emotional_cues": values["cues"],
                "example_statements": values["examples"],
            }
            for stage, values in grouped.items()
        ]


class GeneratedScenarioPrompt(BaseModel):
    """Deterministic output of the prompt builder."""

    prompt_text: str
    prompt_version: str
    warnings: list[str] = Field(default_factory=list)


# --- API: faculty authoring requests --------------------------------------


class ScenarioAuthoringInput(ScenarioAuthoringData):
    """Body for creating or replacing a scenario draft.

    Identical to ``ScenarioAuthoringData`` today; kept as a distinct name so the
    request contract can diverge from the internal builder input later.
    """


class TestTurn(BaseModel):
    speaker: Literal["client", "student"]
    content: str


class ScenarioTestMessageRequest(BaseModel):
    content: str
    history: list[TestTurn] = Field(default_factory=list)


# --- API: faculty authoring responses -------------------------------------


class FacultyScenarioSummary(ORMModel):
    id: uuid.UUID
    module_number: int
    template_key: str
    template_version: str
    current_version_id: uuid.UUID | None = None
    title: str
    slug: str
    difficulty: str
    status: str
    client_name: str
    prompt_version: str | None = None
    created_by: str | None = None
    updated_at: datetime


class FacultyScenarioDetail(ORMModel):
    id: uuid.UUID
    module_number: int
    template_key: str
    template_version: str
    current_version_id: uuid.UUID | None = None
    title: str
    slug: str
    description: str
    difficulty: str
    estimated_turns: int | None = None
    opening_message: str | None = None
    status: str

    client_identity: ClientIdentity | None = None
    presenting_concern: PresentingConcern | None = None
    cultural_considerations: CulturalConsiderations | None = None
    resistance_configuration: ResistanceConfiguration | None = None
    engagement_levels: list[EngagementLevelDescription] | None = None
    engagement_increase_rules: list[ClientBehaviorRule] | None = None
    engagement_decrease_rules: list[ClientBehaviorRule] | None = None
    disclosure_rules: DisclosureRules | None = None
    progression_beats: list[ProgressionBeat] | None = None
    emotional_cue_progression: list[EmotionalCueRule] | None = None
    silence_response_rules: list[SilenceResponseRule] | None = None
    counselor_skill_detection: list[CounselorSkillRule] | None = None
    session_success_indicators: list[SessionSuccessIndicator] | None = None
    emotional_tone: EmotionalTone | None = None
    hidden_information: list[str] | None = None
    learning_objectives: list[LearningObjective] | None = None
    rubric_items: list[RubricItem] | None = None
    competency_scale: list[CompetencyScaleBand] | None = None
    evaluation_focus_sections: list[EvaluationFocusSection] | None = None
    reflection_questions: list[str] | None = None
    safety_rules: SafetyRules | None = None

    generated_prompt: str | None = None
    prompt_version: str | None = None
    prompt_generated_at: datetime | None = None
    created_by: str | None = None
    published_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class ScenarioPreviewResponse(BaseModel):
    status: str
    prompt_text: str
    evaluator_prompt_text: str
    prompt_version: str
    warnings: list[str] = Field(default_factory=list)


class ScenarioPublishResponse(BaseModel):
    id: uuid.UUID
    status: str
    slug: str
    prompt_version: str | None = None
    scenario_version_id: uuid.UUID | None = None
    template_key: str
    template_version: str


class ScenarioTemplateResponse(BaseModel):
    key: str
    version: str
    display_name: str
    supported_modalities: list[str]
    output_schema_version: str
    default_rubric: list[dict]
    default_safety_policy: dict
    content: dict


class ScenarioTestMessageResponse(BaseModel):
    reply: str
    debug_state: dict | None = None
    trace: dict | None = None
