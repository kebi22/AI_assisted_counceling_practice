"""Module 1 microskills template definition.

This file is intentionally thin at first: it centralizes the template identity,
default state, rubric, and prompt entry points so later state-transition and
evaluation work can depend on a stable architecture.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from app.ai.prompt_builder import scenario_prompt_builder
from app.ai.skill_classifier_agent import SUPPORTED_RUNTIME_BEHAVIOR_KEYS
from app.ai.prompts.module1_evaluator import (
    MODULE1_EVALUATOR_SYSTEM_PROMPT,
    MODULE1_RUBRIC,
    MODULE1_RUBRIC_ITEMS,
)
from app.ai.prompts.scenario_template import (
    DEFAULT_OUTPUT_STYLE,
    DEFAULT_RESPONSE_LENGTH,
    DEFAULT_SAFETY_RULES,
    DEFAULT_TRUST_DEVELOPMENT,
    PROHIBITED_BEHAVIORS,
    RESISTANCE_LEVEL_LABELS,
    ROLE_AND_PURPOSE,
)
from app.schemas.scenario_authoring import DisclosureItem, ScenarioAuthoringData
from app.utils.scenario_state import STAGE_ORDER, disclosure_key


MODULE1_CLIENT_OVERVIEW: dict[str, Any] = {
    "name": "Sarah",
    "age": "28",
    "occupation": "Teacher",
    "presenting_concern": "Stress, overwhelm, difficulty balancing responsibilities",
    "risk_level": "No safety concerns",
    "counseling_history": "First counseling experience",
    "initial_engagement_level": "1-2 (Guarded to Tentatively Open)",
    "primary_training_focus": [
        "Therapeutic presence",
        "Empathy",
        "Reflections",
        "Rapport",
        "Emotional exploration",
        "Pacing",
        "Silence",
    ],
}

MODULE1_ENGAGEMENT_LEVELS: list[dict[str, Any]] = [
    {
        "level": 1,
        "label": "Guarded",
        "description": "Shares minimal information and remains cautious.",
        "typical_response": "I don't really know where to start.",
    },
    {
        "level": 2,
        "label": "Tentatively Open",
        "description": "Provides more details but remains surface-level.",
        "typical_response": "Work has been stressful lately.",
    },
    {
        "level": 3,
        "label": "Engaged",
        "description": "Discusses feelings and frustrations.",
        "typical_response": "I feel like I'm constantly behind.",
    },
    {
        "level": 4,
        "label": "Vulnerable",
        "description": "Shares deeper emotions and personal concerns.",
        "typical_response": "I feel guilty because I'm not showing up for people the way I want to.",
    },
    {
        "level": 5,
        "label": "Deep Exploration",
        "description": "Reflects on identity, values, and emotional impact.",
        "typical_response": "I feel like I've lost parts of myself.",
    },
]

MODULE1_ENGAGEMENT_INCREASE_RULES: list[dict[str, Any]] = [
    {
        "counselor_behavior": "Accurate empathy",
        "behavior_key": "accurate_empathy",
        "client_response": "Shares additional emotional content",
        "engagement_change": 1,
    },
    {
        "counselor_behavior": "Reflection of feelings",
        "behavior_key": "reflection_of_feeling",
        "client_response": "Expands emotional exploration",
        "engagement_change": 1,
    },
    {
        "counselor_behavior": "Reflection of meaning",
        "behavior_key": "reflection_of_meaning",
        "client_response": "Discusses deeper concerns",
        "engagement_change": 1,
    },
    {
        "counselor_behavior": "Appropriate silence",
        "behavior_key": "appropriate_processing_space",
        "client_response": "Continues talking and self-reflecting",
        "engagement_change": 1,
    },
    {
        "counselor_behavior": "Strong therapeutic presence",
        "behavior_key": "therapeutic_presence",
        "client_response": "Increased trust and openness",
        "engagement_change": 1,
    },
    {
        "counselor_behavior": "Emotional exploration",
        "behavior_key": "emotional_exploration",
        "client_response": "Moves toward vulnerability",
        "engagement_change": 1,
    },
]

MODULE1_ENGAGEMENT_DECREASE_RULES: list[dict[str, Any]] = [
    {
        "counselor_behavior": "Excessive questioning",
        "behavior_key": "excessive_questioning",
        "client_response": "Shorter responses",
        "engagement_change": -1,
    },
    {
        "counselor_behavior": "Rapid-fire questions",
        "behavior_key": "rapid_fire_questions",
        "client_response": "Becomes task-focused",
        "engagement_change": -1,
    },
    {
        "counselor_behavior": "Premature advice",
        "behavior_key": "premature_advice",
        "client_response": "Becomes less emotionally expressive",
        "engagement_change": -1,
    },
    {
        "counselor_behavior": "Ignoring emotional cues",
        "behavior_key": "ignored_emotional_cue",
        "client_response": "Returns to surface-level content",
        "engagement_change": -1,
    },
    {
        "counselor_behavior": "Frequent topic shifts",
        "behavior_key": "frequent_topic_shift",
        "client_response": "Becomes guarded",
        "engagement_change": -1,
    },
    {
        "counselor_behavior": "Problem-solving too early",
        "behavior_key": "early_problem_solving",
        "client_response": "Withdraws emotionally",
        "engagement_change": -1,
    },
]

MODULE1_EMOTIONAL_CUE_PROGRESSION: list[dict[str, Any]] = [
    {
        "session_stage": "early",
        "emotional_cues": ["Stress", "Frustration", "Overwhelm"],
        "example_statements": ["There just aren't enough hours in the day."],
    },
    {
        "session_stage": "mid",
        "emotional_cues": ["Fatigue", "Guilt", "Self-doubt"],
        "example_statements": ["I feel like I'm letting people down."],
    },
    {
        "session_stage": "later",
        "emotional_cues": ["Identity concerns", "Emotional exhaustion"],
        "example_statements": ["I don't really feel like myself anymore."],
    },
]

MODULE1_DISCLOSURE_SEQUENCE: list[dict[str, str]] = [
    {"information_area": "Work stress", "when_revealed": "Early session"},
    {"information_area": "Time management concerns", "when_revealed": "Early session"},
    {"information_area": "Emotional exhaustion", "when_revealed": "Mid session"},
    {"information_area": "Guilt about relationships", "when_revealed": "Mid session"},
    {"information_area": "Doubts about sustainability", "when_revealed": "Later session"},
    {"information_area": "Loss of fulfillment", "when_revealed": "Later session"},
    {"information_area": "Identity concerns", "when_revealed": "Later session"},
]

MODULE1_PROGRESSION_BEATS: list[dict[str, Any]] = [
    {
        "key": "work_stress",
        "title": "Work pressure",
        "session_stage": "early",
        "emotional_cues": ["Stress"],
        "emotional_intensity": 2,
        "private_meaning": "Sarah feels continuously pulled between competing teaching demands.",
        "disclosure_label": "Work stress",
        "disclosure_content": "Work has become stressful and competing teaching responsibilities feel difficult to balance.",
        "semantic_claims": ["Work is stressful", "Teaching responsibilities compete for limited time"],
        "example_expressions": ["Work has been pretty stressful lately."],
        "prerequisite_beat_keys": [],
        "minimum_trust_level": 1,
        "minimum_engagement_level": 1,
        "required_counselor_response": "any",
        "trigger": "opening",
        "required_for_completion": True,
    },
    {
        "key": "time_management",
        "title": "Not enough time",
        "session_stage": "early",
        "emotional_cues": ["Frustration", "Overwhelm"],
        "emotional_intensity": 2,
        "private_meaning": "The practical time problem is beginning to feel emotionally unmanageable.",
        "disclosure_label": "Time management concerns",
        "disclosure_content": "There never seem to be enough hours for teaching, planning, and a personal life.",
        "semantic_claims": ["There is not enough time", "Work and personal responsibilities feel impossible to balance"],
        "example_expressions": ["There are never enough hours in the day."],
        "prerequisite_beat_keys": ["work_stress"],
        "minimum_trust_level": 1,
        "minimum_engagement_level": 2,
        "required_counselor_response": "any",
        "trigger": "volunteer",
        "required_for_completion": True,
    },
    {
        "key": "emotional_exhaustion",
        "title": "Running on empty",
        "session_stage": "mid",
        "emotional_cues": ["Fatigue"],
        "emotional_intensity": 3,
        "private_meaning": "Sarah is no longer merely busy; she is emotionally depleted.",
        "disclosure_label": "Emotional exhaustion",
        "disclosure_content": "Sarah feels tired, drained, and as though she is running on empty.",
        "semantic_claims": ["She is emotionally depleted", "Rest is not restoring her energy"],
        "example_expressions": ["I feel like I'm running on empty most of the time."],
        "prerequisite_beat_keys": ["time_management"],
        "minimum_trust_level": 3,
        "minimum_engagement_level": 3,
        "required_counselor_response": "acknowledge_cue",
        "trigger": "after_rapport",
        "required_for_completion": True,
    },
    {
        "key": "relationship_guilt",
        "title": "Letting people down",
        "session_stage": "mid",
        "emotional_cues": ["Guilt", "Self-doubt"],
        "emotional_intensity": 4,
        "private_meaning": "Her depletion conflicts with the kind of friend and family member she wants to be.",
        "disclosure_label": "Guilt about relationships",
        "disclosure_content": "Sarah feels guilty that she has little left to give friends and family.",
        "semantic_claims": ["She believes she is disappointing people", "She has little emotional energy left for relationships"],
        "example_expressions": ["I know I'm not showing up for people the way I want to."],
        "prerequisite_beat_keys": ["emotional_exhaustion"],
        "minimum_trust_level": 3,
        "minimum_engagement_level": 3,
        "required_counselor_response": "acknowledge_cue",
        "trigger": "after_reflection",
        "required_for_completion": True,
    },
    {
        "key": "identity_concerns",
        "title": "Losing parts of herself",
        "session_stage": "later",
        "emotional_cues": ["Identity concerns"],
        "emotional_intensity": 5,
        "private_meaning": "The strain now threatens Sarah's sense of identity and connection.",
        "disclosure_label": "Identity concerns",
        "disclosure_content": "Sarah feels disconnected from important parts of herself and no longer feels like herself.",
        "semantic_claims": ["She no longer feels like herself", "Important parts of her identity feel lost"],
        "example_expressions": ["I don't really feel like myself anymore."],
        "prerequisite_beat_keys": ["relationship_guilt"],
        "minimum_trust_level": 4,
        "minimum_engagement_level": 4,
        "required_counselor_response": "deepen_cue",
        "trigger": "after_reflection",
        "required_for_completion": True,
    },
    {
        "key": "loss_of_fulfillment",
        "title": "Joy has faded",
        "session_stage": "later",
        "emotional_cues": ["Emotional exhaustion"],
        "emotional_intensity": 5,
        "private_meaning": "Teaching once expressed Sarah's values; its loss of meaning is especially painful.",
        "disclosure_label": "Loss of fulfillment",
        "disclosure_content": "Teaching no longer feels fulfilling, and Sarah feels she is only going through the motions.",
        "semantic_claims": ["Teaching has lost its joy", "She is going through the motions"],
        "example_expressions": ["Teaching used to be so fulfilling, but now it just feels like another task."],
        "prerequisite_beat_keys": ["identity_concerns"],
        "minimum_trust_level": 4,
        "minimum_engagement_level": 4,
        "required_counselor_response": "deepen_cue",
        "trigger": "after_reflection",
        "required_for_completion": True,
    },
    {
        "key": "sustainability_doubts",
        "title": "Can this continue?",
        "session_stage": "later",
        "emotional_cues": ["Self-doubt"],
        "emotional_intensity": 4,
        "private_meaning": "Sarah is questioning whether her current way of living and working is sustainable.",
        "disclosure_label": "Doubts about sustainability",
        "disclosure_content": "Sarah doubts that she can continue carrying her responsibilities this way.",
        "semantic_claims": ["Her current pace feels unsustainable", "She doubts she can keep doing this"],
        "example_expressions": ["I don't know how long I can keep doing this."],
        "prerequisite_beat_keys": ["loss_of_fulfillment"],
        "minimum_trust_level": 4,
        "minimum_engagement_level": 4,
        "required_counselor_response": "direct_question",
        "trigger": "direct_question",
        "required_for_completion": False,
    },
]

MODULE1_SILENCE_RESPONSE_RULES: list[dict[str, Any]] = [
    {
        "counselor_use_of_silence": "Appropriate therapeutic pause",
        "client_response": "Elaborates further",
        "engagement_change": 1,
    },
    {
        "counselor_use_of_silence": "Silence after emotional disclosure",
        "client_response": "Shares deeper thoughts",
        "engagement_change": 1,
    },
    {
        "counselor_use_of_silence": "Consistent patience",
        "client_response": "Increased reflection",
        "engagement_change": 1,
    },
    {
        "counselor_use_of_silence": "Excessively long silence",
        "client_response": "I'm not really sure what else to say.",
        "engagement_change": -1,
    },
    {
        "counselor_use_of_silence": "Awkward silence",
        "client_response": "Returns to surface-level discussion",
        "engagement_change": -1,
    },
]

MODULE1_COUNSELOR_SKILL_DETECTION: list[dict[str, Any]] = [
    {
        "skill": "Empathy",
        "behavior_key": "accurate_empathy",
        "behavioral_indicator": "Validation and emotional understanding",
        "expected_client_reaction": "Increased trust",
    },
    {
        "skill": "Reflection Skills",
        "behavior_key": "reflection_of_feeling",
        "behavioral_indicator": "Reflection of content, feeling, or meaning",
        "expected_client_reaction": "Greater emotional depth",
    },
    {
        "skill": "Rapport Building",
        "behavior_key": "rapport_building",
        "behavioral_indicator": "Warmth and genuineness",
        "expected_client_reaction": "Increased engagement",
    },
    {
        "skill": "Therapeutic Presence",
        "behavior_key": "therapeutic_presence",
        "behavioral_indicator": "Full attention and responsiveness",
        "expected_client_reaction": "Increased openness",
    },
    {
        "skill": "Emotional Exploration",
        "behavior_key": "emotional_exploration",
        "behavioral_indicator": "Focus on feelings and meaning",
        "expected_client_reaction": "Vulnerability increases",
    },
    {
        "skill": "Appropriate Pacing",
        "behavior_key": "pacing",
        "behavioral_indicator": "Balanced flow of conversation",
        "expected_client_reaction": "Sustained engagement",
    },
    {
        "skill": "Silence Tolerance",
        "behavior_key": "appropriate_processing_space",
        "behavioral_indicator": "Allows reflection without rushing",
        "expected_client_reaction": "Deeper disclosures",
    },
]

MODULE1_SUCCESS_INDICATORS: list[dict[str, str]] = [
    {"indicator": "Strong Alliance", "evidence": "Sarah reaches Level 4 or 5 engagement"},
    {"indicator": "Emotional Exploration", "evidence": "Multiple emotional disclosures occur"},
    {"indicator": "Effective Reflections", "evidence": "Sarah expands rather than repeats information"},
    {"indicator": "Therapeutic Presence", "evidence": "Sarah comments on feeling understood"},
    {"indicator": "Meaningful Self-Reflection", "evidence": "Sarah explores deeper personal concerns"},
]

MODULE1_COMPETENCY_SCALE: list[dict[str, str]] = [
    {"score_range": "4.5-5.0", "competency_level": "Advanced Skill Demonstration"},
    {"score_range": "3.5-4.49", "competency_level": "Proficient Skill Demonstration"},
    {"score_range": "2.5-3.49", "competency_level": "Developing Skill Demonstration"},
    {"score_range": "1.5-2.49", "competency_level": "Emerging Skill Demonstration"},
    {"score_range": "1.0-1.49", "competency_level": "Beginning Skill Demonstration"},
]

MODULE1_EVALUATION_FOCUS_SECTIONS: list[dict[str, Any]] = [
    {
        "key": "strengths_observed",
        "title": "Strengths Observed",
        "instructions": [
            "Identify 2-4 specific strengths from the interaction.",
            "Reference specific counselor statements or behaviors whenever possible.",
        ],
    },
    {
        "key": "areas_for_growth",
        "title": "Areas for Growth",
        "instructions": [
            "Identify 2-4 opportunities for improvement.",
            "Include specific examples and practical suggestions.",
        ],
    },
    {
        "key": "emotional_exploration_analysis",
        "title": "Emotional Exploration Analysis",
        "instructions": [
            "Identify at least two moments when Sarah expressed meaningful emotion.",
            "Classify whether the counselor deepened exploration, stayed surface-level, redirected, or missed the cue.",
            "Provide an alternative response that may have encouraged deeper exploration.",
        ],
    },
]

MODULE1_REFLECTION_QUESTIONS: list[str] = [
    "What counseling strengths emerged during this interaction? Provide specific examples.",
    "Which counseling skills appeared strongest, and how did they contribute to the therapeutic relationship?",
    "Where could the counselor deepen the interaction or facilitate greater emotional exploration?",
    "How effectively did the counselor respond to emotional content?",
    "How did the counselor's pacing influence rapport and client engagement?",
    "How effectively were questions balanced with reflections and empathic responses?",
    "How was silence used throughout the interaction? What effect did it appear to have on the client?",
    "What opportunities existed to respond more fully to emotional content?",
    "If this session continued, what counseling skill should be the counselor's primary area of focus for future growth?",
    "What is one specific counseling intervention or response that could strengthen future sessions?",
]


class Module1MicroskillsTemplate:
    key = "microskills_progressive_disclosure"
    version = "2.0.0"
    display_name = "Advanced Microskills and Emotional Exploration"
    supported_modalities = ["text"]
    output_schema_version = "2.0.0"
    authoring_schema = ScenarioAuthoringData

    def default_rubric(self) -> list[dict[str, Any]]:
        return [dict(item) for item in MODULE1_RUBRIC_ITEMS]

    def default_safety_policy(self) -> dict[str, Any]:
        return {
            "crisis_content_allowed": False,
            "abuse_disclosure_allowed": False,
            "rules": list(DEFAULT_SAFETY_RULES),
        }

    def template_content(self) -> dict[str, Any]:
        return {
            "client_prompt_scaffold": {
                "role_and_purpose": ROLE_AND_PURPOSE,
                "default_response_length": DEFAULT_RESPONSE_LENGTH,
                "default_trust_development": DEFAULT_TRUST_DEVELOPMENT,
                "default_output_style": list(DEFAULT_OUTPUT_STYLE),
                "default_safety_rules": list(DEFAULT_SAFETY_RULES),
                "prohibited_behaviors": list(PROHIBITED_BEHAVIORS),
                "resistance_level_labels": RESISTANCE_LEVEL_LABELS,
            },
            "state_policy": {
                "engagement_range": [1, 5],
                "engagement_levels": MODULE1_ENGAGEMENT_LEVELS,
                "session_stages": ["early", "mid", "later"],
                "stage_rules": {
                    "early": "Default stage, including turns 1-3 or engagement below 3.",
                    "mid": "Turn 4+ and engagement 3+.",
                    "later": "Turn 8+ and engagement 4+.",
                },
                "engagement_increase_rules": MODULE1_ENGAGEMENT_INCREASE_RULES,
                "engagement_decrease_rules": MODULE1_ENGAGEMENT_DECREASE_RULES,
                "emotional_cue_progression": MODULE1_EMOTIONAL_CUE_PROGRESSION,
                "progression_beats": MODULE1_PROGRESSION_BEATS,
                "maximum_engagement_movement_per_turn": 1,
                "supported_behavior_keys": sorted(SUPPORTED_RUNTIME_BEHAVIOR_KEYS),
            },
            "module1_client_blueprint": {
                "client_overview": MODULE1_CLIENT_OVERVIEW,
                "disclosure_sequence": MODULE1_DISCLOSURE_SEQUENCE,
                "progression_beats": MODULE1_PROGRESSION_BEATS,
                "silence_response_rules": MODULE1_SILENCE_RESPONSE_RULES,
                "counselor_skill_detection": MODULE1_COUNSELOR_SKILL_DETECTION,
                "session_success_indicators": MODULE1_SUCCESS_INDICATORS,
            },
            "disclosure_policy": {
                "rule": (
                    "A disclosure is allowed only when current engagement is at or above "
                    "the disclosure minimum and current session stage is at or after the "
                    "disclosure stage."
                ),
                "item_fields": [
                    "label",
                    "content_summary",
                    "minimum_engagement_level",
                    "session_stage",
                    "requires_direct_question",
                    "faculty_only_notes",
                ],
            },
            "competency_scale": MODULE1_COMPETENCY_SCALE,
            "evaluation_focus_sections": MODULE1_EVALUATION_FOCUS_SECTIONS,
            "reflection_questions": MODULE1_REFLECTION_QUESTIONS,
            "evaluator_prompt": MODULE1_EVALUATOR_SYSTEM_PROMPT,
        }

    def initial_state(self, profile: BaseModel) -> dict[str, Any]:
        data = self._coerce_profile(profile)
        config = data.resistance_configuration
        starting_level = max(
            config.minimum_engagement_level,
            min(config.maximum_engagement_level, config.starting_engagement_level),
        )
        return {
            "engagement_level": starting_level,
            "trust_level": starting_level,
            "disclosure_stage": 1,
            "emotional_depth": 1,
            "rupture_count": 0,
            "repair_count": 0,
            "revealed_information": [],
            "emotional_cues": [],
            "session_stage": "early",
            "state_history": [],
        }

    def allowed_disclosures(
        self,
        profile: BaseModel,
        current_state: dict[str, Any],
        *,
        has_direct_question: bool = False,
    ) -> list[str]:
        return [
            item.content_summary
            for item in self.eligible_disclosures(
                profile,
                current_state,
                has_direct_question=has_direct_question,
            )
        ]

    def eligible_disclosures(
        self,
        profile: BaseModel,
        current_state: dict[str, Any],
        *,
        has_direct_question: bool = False,
    ) -> list[DisclosureItem]:
        data = self._coerce_profile(profile)
        engagement = int(current_state.get("engagement_level", 1))
        stage = str(current_state.get("session_stage", "early"))
        stage_rank = STAGE_ORDER.get(stage, 1)
        revealed = {
            str(item) for item in current_state.get("revealed_information", [])
        }
        disclosure_groups = (
            data.disclosure_rules.immediate,
            data.disclosure_rules.after_rapport,
            data.disclosure_rules.on_direct_question,
        )
        allowed = [
            item
            for group in disclosure_groups
            for item in group
            if self._item_allowed(
                item.minimum_engagement_level,
                item.session_stage,
                engagement,
                stage_rank,
            )
            and disclosure_key(item) not in revealed
            and (not item.requires_direct_question or has_direct_question)
        ]
        return allowed

    def build_client_prompt(self, profile: BaseModel) -> str:
        return scenario_prompt_builder.build_client_prompt(
            self._coerce_profile(profile)
        ).prompt_text

    def build_evaluator_prompt(
        self, rubric: list[dict[str, Any]], learning_objectives: list[dict[str, Any]]
    ) -> str:
        return MODULE1_EVALUATOR_SYSTEM_PROMPT

    @staticmethod
    def _coerce_profile(profile: BaseModel) -> ScenarioAuthoringData:
        if isinstance(profile, ScenarioAuthoringData):
            return profile
        return ScenarioAuthoringData.model_validate(profile)

    @staticmethod
    def _item_allowed(
        minimum_engagement_level: int,
        session_stage: str,
        engagement: int,
        current_stage_rank: int,
    ) -> bool:
        required_stage_rank = STAGE_ORDER.get(session_stage, 1)
        return engagement >= minimum_engagement_level and current_stage_rank >= required_stage_rank
