"""Unit tests for prompt construction and scenario-agent sanitization."""

from app.ai.output_models import ConversationMessage
from app.ai.prompts.module1_client import CLIENT_FALLBACK_RESPONSE
from app.ai.scenario_agent import ScenarioAgent
from app.core.constants import Speaker


def test_build_prompt_labels_speakers():
    conversation = [
        ConversationMessage(speaker=Speaker.CLIENT, content="I feel overwhelmed."),
        ConversationMessage(speaker=Speaker.STUDENT, content="Tell me more."),
    ]
    prompt = ScenarioAgent._build_prompt(conversation)
    assert "Jordan: I feel overwhelmed." in prompt
    assert "Counselor: Tell me more." in prompt
    assert prompt.rstrip().endswith("Jordan:")


def test_sanitize_rejects_leaked_rubric():
    agent = ScenarioAgent()
    cleaned = agent._sanitize("Here is the rubric you should score against.")
    assert cleaned == CLIENT_FALLBACK_RESPONSE


def test_sanitize_passes_normal_reply():
    agent = ScenarioAgent()
    reply = "Honestly, it has been a really hard few weeks."
    assert agent._sanitize(reply) == reply
