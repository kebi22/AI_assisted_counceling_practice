"""Structured output contracts for the AI layer.

The evaluation contract lives in ``app.schemas.evaluation`` so it can be reused
by both the AI agent and the API responses.
"""

from dataclasses import dataclass

from app.core.constants import Speaker


@dataclass(frozen=True)
class ConversationMessage:
    """A single turn passed to the scenario agent."""

    speaker: Speaker
    content: str
