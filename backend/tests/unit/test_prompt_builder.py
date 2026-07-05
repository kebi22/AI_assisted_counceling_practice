"""Unit tests for the deterministic scenario prompt builder."""

from app.ai.prompt_builder import ScenarioPromptBuilder
from app.ai.prompts.scenario_template import SCENARIO_PROMPT_TEMPLATE_VERSION
from app.schemas.scenario_authoring import (
    ClientIdentity,
    DisclosureRules,
    EmotionalTone,
    LearningObjective,
    PresentingConcern,
    ResistanceConfiguration,
    RubricItem,
    SafetyRules,
    ScenarioAuthoringData,
)


def _jordan_scenario(**overrides) -> ScenarioAuthoringData:
    data = ScenarioAuthoringData(
        title="Burned-Out Teacher",
        difficulty="easy",
        client_identity=ClientIdentity(
            name="Jordan",
            age="29",
            occupation="Middle school teacher",
        ),
        presenting_concern=PresentingConcern(
            primary_concern="Feeling overwhelmed and emotionally exhausted at work.",
            reason_for_attending="Encouraged by a supervisor to seek support.",
        ),
        resistance_configuration=ResistanceConfiguration(
            level=2,
            increases_when="The student gives advice too early.",
            decreases_when="The student reflects feelings and asks open questions.",
        ),
        disclosure_rules=DisclosureRules(
            immediate=["You feel exhausted from work."],
            after_rapport=["You have considered leaving teaching."],
            never=["Any crisis or self-harm content."],
        ),
        emotional_tone=EmotionalTone(starting_tone="hesitant"),
        hidden_information=["You privately fear you are no longer good at your job."],
        learning_objectives=[LearningObjective(name="Demonstrate empathy")],
        rubric=[
            RubricItem(category="Empathy", weight=50),
            RubricItem(category="Reflection", weight=50),
        ],
        safety_rules=SafetyRules(),
    )
    return data.model_copy(update=overrides)


def test_builds_sections_in_order():
    result = ScenarioPromptBuilder().build_client_prompt(_jordan_scenario())
    text = result.prompt_text

    for header in [
        "ROLE AND PURPOSE",
        "CLIENT IDENTITY",
        "PRESENTING CONCERN",
        "STARTING DEMEANOR AND EMOTIONAL TONE",
        "RESISTANCE BEHAVIOR",
        "DISCLOSURE RULES",
        "HIDDEN INFORMATION",
        "RESPONSE BEHAVIOR",
        "TRUST-DEVELOPMENT RULES",
        "SAFETY RESTRICTIONS",
        "PROHIBITED BEHAVIORS",
        "OUTPUT STYLE",
    ]:
        assert header in text, f"missing section: {header}"

    positions = [text.index(h) for h in ["CLIENT IDENTITY", "DISCLOSURE RULES", "OUTPUT STYLE"]]
    assert positions == sorted(positions)


def test_default_safety_rules_always_present():
    scenario = _jordan_scenario(safety_rules=SafetyRules())
    result = ScenarioPromptBuilder().build_client_prompt(scenario)
    assert "Do not break character" in result.prompt_text
    assert "crisis" in result.prompt_text.lower()


def test_hidden_information_not_volunteered_instruction():
    result = ScenarioPromptBuilder().build_client_prompt(_jordan_scenario())
    assert "never be volunteered" in result.prompt_text
    assert "fear you are no longer good" in result.prompt_text


def test_version_is_stable_and_template_tagged():
    builder = ScenarioPromptBuilder()
    first = builder.build_client_prompt(_jordan_scenario())
    second = builder.build_client_prompt(_jordan_scenario())
    assert first.prompt_version == second.prompt_version
    assert first.prompt_version.startswith(f"{SCENARIO_PROMPT_TEMPLATE_VERSION}+")


def test_version_changes_when_content_changes():
    builder = ScenarioPromptBuilder()
    base = builder.build_client_prompt(_jordan_scenario())
    changed = builder.build_client_prompt(
        _jordan_scenario(
            presenting_concern=PresentingConcern(primary_concern="Something different.")
        )
    )
    assert base.prompt_version != changed.prompt_version


def test_warns_on_bad_rubric_weights():
    scenario = _jordan_scenario(rubric=[RubricItem(category="Empathy", weight=85)])
    result = ScenarioPromptBuilder().build_client_prompt(scenario)
    assert any("85" in w for w in result.warnings)


def test_warns_and_ignores_crisis_request():
    scenario = _jordan_scenario(safety_rules=SafetyRules(crisis_content_allowed=True))
    result = ScenarioPromptBuilder().build_client_prompt(scenario)
    assert any("crisis" in w.lower() for w in result.warnings)
    assert "Do not introduce crisis" in result.prompt_text


def test_empty_disclosure_warns_and_uses_default():
    scenario = _jordan_scenario(disclosure_rules=DisclosureRules())
    result = ScenarioPromptBuilder().build_client_prompt(scenario)
    assert any("disclosure" in w.lower() for w in result.warnings)
    assert "do not reveal everything at once" in result.prompt_text.lower()
