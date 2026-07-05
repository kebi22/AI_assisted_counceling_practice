"""Unit tests for evaluation-agent prompt assembly."""

from app.ai.evaluation_agent import EvaluationAgent


def test_evaluation_prompt_includes_version_and_state_context():
    prompt = EvaluationAgent._build_prompt(
        transcript="Counselor (student): It sounds exhausting.",
        rubric={"empathy": "Ability to acknowledge client feelings"},
        template_metadata={
            "template_key": "microskills_progressive_disclosure",
            "template_version": "1.0.0",
            "scenario_version_id": "version-1",
        },
        learning_objectives=[{"name": "Demonstrate empathy"}],
        state_history=[
            {
                "turn": 1,
                "detected_behaviors": ["accurate_empathy"],
                "engagement_level": 3,
            }
        ],
    )

    assert "microskills_progressive_disclosure" in prompt
    assert "Demonstrate empathy" in prompt
    assert "accurate_empathy" in prompt
    assert "It sounds exhausting" in prompt
