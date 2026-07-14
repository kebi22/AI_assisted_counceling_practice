"""Deterministic builder that turns structured scenario data into a client prompt.

The builder assembles a Gemini system prompt from faculty-authored structured
fields in a fixed section order. It never calls Gemini, never writes to the
database, and never decides whether a scenario is publishable. It surfaces
non-fatal issues as ``warnings`` and always applies the Version 1 default
safety rules.
"""

from __future__ import annotations

import hashlib

from app.ai.prompts.scenario_template import (
    DEFAULT_OUTPUT_STYLE,
    DEFAULT_RESPONSE_LENGTH,
    DEFAULT_SAFETY_RULES,
    DEFAULT_TRUST_DEVELOPMENT,
    PROHIBITED_BEHAVIORS,
    RESISTANCE_LEVEL_LABELS,
    ROLE_AND_PURPOSE,
    SCENARIO_PROMPT_TEMPLATE_VERSION,
)
from app.schemas.scenario_authoring import (
    ClientBehaviorRule,
    DisclosureItem,
    GeneratedScenarioPrompt,
    ScenarioAuthoringData,
)


def _bullets(items: list[str], *, indent: str = "- ") -> list[str]:
    return [f"{indent}{item.strip()}" for item in items if item and item.strip()]


def _disclosure_bullets(items: list[DisclosureItem], *, indent: str = "  - ") -> list[str]:
    lines: list[str] = []
    for item in items:
        detail = item.content_summary.strip()
        if not detail:
            continue
        qualifiers = [
            f"minimum engagement {item.minimum_engagement_level}",
            f"{item.session_stage} stage",
        ]
        if item.requires_direct_question:
            qualifiers.append("requires direct question")
        lines.append(f"{indent}{item.label}: {detail} ({'; '.join(qualifiers)})")
    return lines


def _behavior_rule_bullets(items: list[ClientBehaviorRule], *, indent: str = "- ") -> list[str]:
    return [
        (
            f"{indent}{item.counselor_behavior}: respond by {item.client_response} "
            f"(engagement {item.engagement_change:+d})"
        )
        for item in items
    ]


class ScenarioPromptBuilder:
    """Assembles a simulated-client system prompt from structured scenario data."""

    def build_client_prompt(
        self, scenario: ScenarioAuthoringData
    ) -> GeneratedScenarioPrompt:
        warnings: list[str] = []
        sections: list[str] = []

        sections.append(self._role_section())
        sections.append(self._identity_section(scenario))
        sections.append(self._presenting_concern_section(scenario))

        cultural = self._cultural_section(scenario)
        if cultural:
            sections.append(cultural)

        sections.append(self._tone_section(scenario))
        sections.append(self._resistance_section(scenario))
        sections.append(self._engagement_model_section(scenario))
        progression = self._progression_section(scenario)
        if progression:
            sections.append(progression)
        sections.append(self._disclosure_section(scenario, warnings))
        emotional = self._emotional_cue_section(scenario)
        if emotional:
            sections.append(emotional)
        silence = self._silence_section(scenario)
        if silence:
            sections.append(silence)
        skills = self._skill_detection_section(scenario)
        if skills:
            sections.append(skills)
        success = self._success_indicator_section(scenario)
        if success:
            sections.append(success)

        hidden = self._hidden_information_section(scenario)
        if hidden:
            sections.append(hidden)

        sections.append(self._response_behavior_section(scenario))
        sections.append(self._trust_development_section(scenario))
        sections.append(self._safety_section(scenario, warnings))
        sections.append(self._prohibited_section())
        sections.append(self._output_style_section())

        self._collect_content_warnings(scenario, warnings)

        prompt_text = "\n\n".join(section.strip() for section in sections if section.strip())
        prompt_text = prompt_text.strip() + "\n"

        return GeneratedScenarioPrompt(
            prompt_text=prompt_text,
            prompt_version=self._make_version(prompt_text),
            warnings=warnings,
        )

    def build_runtime_persona_prompt(self, scenario: ScenarioAuthoringData) -> str:
        """Build the stable roleplay prompt without future cues or disclosures.

        Locked scenario facts stay server-side. The turn pipeline appends only the
        cue and optional disclosure selected for the current response.
        """
        warnings: list[str] = []
        sections = [
            self._role_section(),
            self._identity_section(scenario),
            self._public_presenting_concern_section(scenario),
        ]
        cultural = self._cultural_section(scenario)
        if cultural:
            sections.append(cultural)
        sections.extend(
            [
                self._runtime_tone_section(scenario),
                self._resistance_section(scenario),
                self._response_behavior_section(scenario),
                self._trust_development_section(scenario),
                self._runtime_plan_rules_section(),
                self._safety_section(scenario, warnings),
                self._prohibited_section(),
                self._output_style_section(),
            ]
        )
        return "\n\n".join(section.strip() for section in sections if section.strip()).strip() + "\n"

    # -- Section renderers --------------------------------------------------

    @staticmethod
    def _role_section() -> str:
        return f"ROLE AND PURPOSE\n{ROLE_AND_PURPOSE}"

    @staticmethod
    def _identity_section(scenario: ScenarioAuthoringData) -> str:
        identity = scenario.client_identity
        lines = ["CLIENT IDENTITY", f"- Name: {identity.name}"]
        if identity.age:
            lines.append(f"- Age: {identity.age}")
        if identity.pronouns:
            lines.append(f"- Pronouns: {identity.pronouns}")
        if identity.occupation:
            lines.append(f"- Occupation or role: {identity.occupation}")
        if identity.background:
            lines.append(f"- Background: {identity.background}")
        if identity.identity_information:
            lines.append(f"- Relevant identity context: {identity.identity_information}")
        return "\n".join(lines)

    @staticmethod
    def _presenting_concern_section(scenario: ScenarioAuthoringData) -> str:
        concern = scenario.presenting_concern
        lines = ["PRESENTING CONCERN", f"- Primary concern: {concern.primary_concern}"]
        if concern.secondary_concern:
            lines.append(f"- Secondary concern: {concern.secondary_concern}")
        if concern.reason_for_attending:
            lines.append(f"- Reason for attending: {concern.reason_for_attending}")
        if concern.client_explanation:
            lines.append(f"- Your own explanation: {concern.client_explanation}")
        if concern.hoped_change:
            lines.append(f"- What you hope changes: {concern.hoped_change}")
        return "\n".join(lines)

    @staticmethod
    def _public_presenting_concern_section(scenario: ScenarioAuthoringData) -> str:
        concern = scenario.presenting_concern
        lines = ["PRESENTING CONCERN", f"- Primary concern: {concern.primary_concern}"]
        if concern.reason_for_attending:
            lines.append(f"- Reason for attending: {concern.reason_for_attending}")
        lines.append(
            "- Do not invent or reveal additional private history unless the current "
            "turn response plan explicitly permits it."
        )
        return "\n".join(lines)

    @staticmethod
    def _cultural_section(scenario: ScenarioAuthoringData) -> str | None:
        c = scenario.cultural_considerations
        lines: list[str] = []
        if c.cultural_factors:
            lines.append(f"- Cultural or contextual factors: {c.cultural_factors}")
        if c.language_preferences:
            lines.append(f"- Language preferences: {c.language_preferences}")
        if c.relevant_values:
            lines.append(f"- Relevant values: {c.relevant_values}")
        if c.concerns_about_counselor:
            lines.append(f"- Possible concerns about the counselor: {c.concerns_about_counselor}")
        if c.communication_preferences:
            lines.append(f"- Communication preferences: {c.communication_preferences}")
        if c.sensitive_topics:
            lines.append("- Approach these topics with sensitivity:")
            lines.extend(_bullets(c.sensitive_topics, indent="  - "))
        if not lines:
            return None
        return "CULTURAL AND CONTEXTUAL CONSIDERATIONS\n" + "\n".join(lines)

    @staticmethod
    def _tone_section(scenario: ScenarioAuthoringData) -> str:
        tone = scenario.emotional_tone
        lines = ["STARTING DEMEANOR AND EMOTIONAL TONE"]
        if tone.starting_tone:
            lines.append(f"- Starting tone: {tone.starting_tone}")
        else:
            lines.append("- Starting tone: cooperative but hesitant")
        if tone.possible_shifts:
            lines.append("- Possible emotional shifts as the session progresses:")
            lines.extend(_bullets(tone.possible_shifts, indent="  - "))
        if tone.communication_style:
            lines.append(f"- Communication style: {tone.communication_style}")
        if tone.intensity:
            lines.append(f"- Level of emotional intensity: {tone.intensity}")
        lines.append(
            "- These describe simulated behavior only; you do not have real emotions."
        )
        return "\n".join(lines)

    @staticmethod
    def _runtime_tone_section(scenario: ScenarioAuthoringData) -> str:
        """Render only stable tone attributes; future shifts stay server-side."""
        tone = scenario.emotional_tone
        lines = [
            "STARTING DEMEANOR AND COMMUNICATION STYLE",
            f"- Starting tone: {tone.starting_tone or 'cooperative but hesitant'}",
        ]
        if tone.communication_style:
            lines.append(f"- Communication style: {tone.communication_style}")
        if tone.intensity:
            lines.append(f"- Maximum baseline intensity: {tone.intensity}")
        lines.append(
            "- Follow the current turn plan for any emotional shift; future shifts are "
            "intentionally omitted."
        )
        return "\n".join(lines)

    @staticmethod
    def _resistance_section(scenario: ScenarioAuthoringData) -> str:
        r = scenario.resistance_configuration
        label = RESISTANCE_LEVEL_LABELS.get(r.level, "guarded")
        lines = [
            "RESISTANCE BEHAVIOR",
            f"- Overall stance: {label} (level {r.level} of 5).",
        ]
        if r.increases_when:
            lines.append(f"- Become more guarded when: {r.increases_when}")
        if r.decreases_when:
            lines.append(f"- Become more open when: {r.decreases_when}")
        if r.behaviors_to_resist:
            lines.append("- Resist these specific behaviors:")
            lines.extend(_bullets(r.behaviors_to_resist, indent="  - "))
        return "\n".join(lines)

    @staticmethod
    def _engagement_model_section(scenario: ScenarioAuthoringData) -> str:
        lines = [
            "ENGAGEMENT MODEL",
            (
                f"- Start at engagement {scenario.resistance_configuration.starting_engagement_level}; "
                f"stay between {scenario.resistance_configuration.minimum_engagement_level} "
                f"and {scenario.resistance_configuration.maximum_engagement_level}."
            ),
        ]
        if scenario.engagement_levels:
            lines.append("- Engagement levels:")
            for item in scenario.engagement_levels:
                response = f" Typical response: {item.typical_response}" if item.typical_response else ""
                lines.append(
                    f"  - Level {item.level} ({item.label}): {item.description}{response}"
                )
        if scenario.engagement_increase_rules:
            lines.append("- Become more open when the counselor demonstrates:")
            lines.extend(_behavior_rule_bullets(scenario.engagement_increase_rules, indent="  - "))
        if scenario.engagement_decrease_rules:
            lines.append("- Become more guarded when the counselor demonstrates:")
            lines.extend(_behavior_rule_bullets(scenario.engagement_decrease_rules, indent="  - "))
        return "\n".join(lines)

    @staticmethod
    def _disclosure_section(
        scenario: ScenarioAuthoringData, warnings: list[str]
    ) -> str:
        d = scenario.disclosure_rules
        lines = ["DISCLOSURE RULES", "Reveal information only according to these rules:"]
        if d.immediate:
            lines.append("- You may share immediately:")
            lines.extend(_disclosure_bullets(d.immediate, indent="  - "))
        if d.after_rapport:
            lines.append("- Share only after rapport develops:")
            lines.extend(_disclosure_bullets(d.after_rapport, indent="  - "))
        if d.on_direct_question:
            lines.append("- Share only if the counselor asks directly:")
            lines.extend(_disclosure_bullets(d.on_direct_question, indent="  - "))
        if d.never:
            lines.append("- Never disclose in this scenario:")
            lines.extend(_bullets(d.never, indent="  - "))
        if d.is_empty():
            lines.append(
                "- Disclose your concern gradually; do not reveal everything at once."
            )
        return "\n".join(lines)

    @staticmethod
    def _progression_section(scenario: ScenarioAuthoringData) -> str | None:
        if not scenario.progression_beats:
            return None
        lines = [
            "CONNECTED STORY PROGRESSION",
            "Treat each beat as a boundary: prerequisites and counselor conditions must be satisfied before its disclosure is used.",
        ]
        for index, beat in enumerate(scenario.progression_beats, start=1):
            prerequisites = ", ".join(beat.prerequisite_beat_keys) or "none"
            cues = ", ".join(beat.emotional_cues) or "none"
            lines.extend(
                [
                    f"- Beat {index} [{beat.key}] {beat.title} ({beat.session_stage} stage)",
                    f"  Emotional cues: {cues}; intensity {beat.emotional_intensity}/5",
                    f"  Private meaning: {beat.private_meaning or 'not specified'}",
                    f"  Permitted disclosure: {beat.disclosure_content or 'none'}",
                    f"  Prerequisites: {prerequisites}; trust {beat.minimum_trust_level}+; engagement {beat.minimum_engagement_level}+",
                    f"  Entry trigger: {beat.trigger}; post-presentation response milestone before dependent beats: {beat.required_counselor_response}",
                ]
            )
        return "\n".join(lines)

    @staticmethod
    def _emotional_cue_section(scenario: ScenarioAuthoringData) -> str | None:
        if not scenario.emotional_cue_progression:
            return None
        lines = [
            "EMOTIONAL CUE PROGRESSION",
            "Use these cues as the session deepens. Do not jump to later cues too early.",
        ]
        for item in scenario.emotional_cue_progression:
            cues = ", ".join(item.emotional_cues) or "unspecified cues"
            examples = "; ".join(item.example_statements)
            lines.append(f"- {item.session_stage.title()} session: {cues}")
            if examples:
                lines.append(f"  Example statements: {examples}")
        return "\n".join(lines)

    @staticmethod
    def _silence_section(scenario: ScenarioAuthoringData) -> str | None:
        if not scenario.silence_response_rules:
            return None
        lines = ["SILENCE RESPONSE RULES"]
        for item in scenario.silence_response_rules:
            lines.append(
                f"- {item.counselor_use_of_silence}: {item.client_response} "
                f"(engagement {item.engagement_change:+d})"
            )
        return "\n".join(lines)

    @staticmethod
    def _skill_detection_section(scenario: ScenarioAuthoringData) -> str | None:
        if not scenario.counselor_skill_detection:
            return None
        lines = ["COUNSELOR SKILL REACTIONS"]
        for item in scenario.counselor_skill_detection:
            lines.append(
                f"- {item.skill}: when you observe {item.behavioral_indicator}, "
                f"respond with {item.expected_client_reaction}."
            )
        return "\n".join(lines)

    @staticmethod
    def _success_indicator_section(scenario: ScenarioAuthoringData) -> str | None:
        if not scenario.session_success_indicators:
            return None
        lines = [
            "SESSION SUCCESS INDICATORS",
            "The interaction is going well when these patterns emerge:",
        ]
        for item in scenario.session_success_indicators:
            lines.append(f"- {item.indicator}: {item.evidence}")
        return "\n".join(lines)

    @staticmethod
    def _hidden_information_section(scenario: ScenarioAuthoringData) -> str | None:
        if not scenario.hidden_information:
            return None
        lines = [
            "HIDDEN INFORMATION",
            "The following is known to you but must never be volunteered or shown "
            "to the counselor. Reveal it only when the disclosure rules above allow:",
        ]
        lines.extend(_bullets(scenario.hidden_information))
        return "\n".join(lines)

    @staticmethod
    def _response_behavior_section(scenario: ScenarioAuthoringData) -> str:
        length = (
            scenario.emotional_tone.typical_response_length or DEFAULT_RESPONSE_LENGTH
        )
        lines = ["RESPONSE BEHAVIOR", f"- {length}"]
        return "\n".join(lines)

    @staticmethod
    def _runtime_plan_rules_section() -> str:
        return (
            "TURN RESPONSE PLAN RULES\n"
            "- The runtime turn plan is authoritative for the next response.\n"
            "- Express only the active emotional cue supplied for this turn.\n"
            "- Reveal at most the one permitted new disclosure, and only when it feels natural.\n"
            "- Never infer the content of locked private information.\n"
            "- Do not automatically become more vulnerable merely because the counselor asks a question."
        )

    @staticmethod
    def _trust_development_section(scenario: ScenarioAuthoringData) -> str:
        trust = (
            scenario.resistance_configuration.trust_development
            or DEFAULT_TRUST_DEVELOPMENT
        )
        return f"TRUST-DEVELOPMENT RULES\n- {trust}"

    @staticmethod
    def _safety_section(scenario: ScenarioAuthoringData, warnings: list[str]) -> str:
        safety = scenario.safety_rules
        lines = ["SAFETY RESTRICTIONS"]
        # Default safety rules always apply (Version 1 policy).
        lines.extend(_bullets(list(DEFAULT_SAFETY_RULES)))
        if safety.disallowed_topics:
            lines.append("- Additional disallowed topics:")
            lines.extend(_bullets(safety.disallowed_topics, indent="  - "))
        if safety.required_redirection:
            lines.append(f"- If pushed toward unsafe content: {safety.required_redirection}")
        if safety.max_emotional_intensity:
            lines.append(
                f"- Do not exceed this emotional intensity: {safety.max_emotional_intensity}"
            )
        return "\n".join(lines)

    @staticmethod
    def _prohibited_section() -> str:
        return "PROHIBITED BEHAVIORS\n" + "\n".join(_bullets(list(PROHIBITED_BEHAVIORS)))

    @staticmethod
    def _output_style_section() -> str:
        return "OUTPUT STYLE\n" + "\n".join(_bullets(list(DEFAULT_OUTPUT_STYLE)))

    # -- Warnings & versioning ---------------------------------------------

    @staticmethod
    def _collect_content_warnings(
        scenario: ScenarioAuthoringData, warnings: list[str]
    ) -> None:
        if not scenario.learning_objectives:
            warnings.append("No learning objectives defined.")

        if scenario.disclosure_rules.is_empty() and not scenario.progression_beats:
            warnings.append("No disclosure rules defined; using a generic default.")

        if scenario.rubric:
            total_weight = sum(item.weight for item in scenario.rubric)
            if total_weight != 100:
                warnings.append(
                    f"Rubric weights total {total_weight} instead of 100."
                )

        if scenario.safety_rules.crisis_content_allowed:
            warnings.append(
                "Crisis content is not permitted in Version 1; the request to allow "
                "it was ignored and default safety rules were kept."
            )

    @staticmethod
    def _make_version(prompt_text: str) -> str:
        """Stable version: template version + short content fingerprint.

        The same structured input always yields the same prompt and version;
        any wording change produces a new fingerprint for auditability.
        """
        digest = hashlib.sha256(prompt_text.encode("utf-8")).hexdigest()[:8]
        return f"{SCENARIO_PROMPT_TEMPLATE_VERSION}+{digest}"


scenario_prompt_builder = ScenarioPromptBuilder()
