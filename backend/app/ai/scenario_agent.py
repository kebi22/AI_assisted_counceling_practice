"""Scenario agent: generates the simulated client's next reply via Gemini."""

from __future__ import annotations

from app.ai.client import GeminiClient, gemini_client
from app.ai.output_models import ConversationMessage
from app.ai.prompts.module1_client import CLIENT_FALLBACK_RESPONSE
from app.core.config import settings
from app.core.constants import Speaker
from app.core.exceptions import AIServiceError
from app.core.logging import get_logger

logger = get_logger(__name__)

# Phrases that suggest the model broke character or leaked instructions.
_DISALLOWED_FRAGMENTS = ("rubric", "as an ai", "language model", "system prompt")


class ScenarioAgent:
    """Produces the AI-client message for a counseling simulation turn."""

    def __init__(self, client: GeminiClient | None = None) -> None:
        self._client = client or gemini_client

    async def generate_client_response(
        self,
        *,
        scenario_prompt: str,
        conversation: list[ConversationMessage],
        client_name: str = "Jordan",
        session_id: str | None = None,
    ) -> str:
        """Return only the simulated client's next message.

        Falls back to a safe canned response if Gemini is unconfigured or fails,
        so a single AI hiccup does not break the practice session.
        """
        prompt = self._build_prompt(conversation, client_name=client_name)
        try:
            text = await self._client.generate_text(
                model=settings.gemini_client_model,
                system_instruction=scenario_prompt,
                prompt=prompt,
                max_output_tokens=400,
                disable_thinking=True,
                session_id=session_id,
            )
        except AIServiceError:
            logger.warning("Scenario agent falling back for session_id=%s", session_id or "-")
            return CLIENT_FALLBACK_RESPONSE

        return self._sanitize(text)

    @staticmethod
    def _build_prompt(
        conversation: list[ConversationMessage], client_name: str = "Jordan"
    ) -> str:
        lines: list[str] = [
            "Continue the counseling practice conversation below. "
            f"Reply as the client ({client_name}) with a single natural response.",
            "",
            "Conversation so far:",
        ]
        for turn in conversation:
            speaker = "Counselor" if turn.speaker == Speaker.STUDENT else client_name
            lines.append(f"{speaker}: {turn.content}")
        lines.append(f"{client_name}:")
        return "\n".join(lines)

    def _sanitize(self, text: str) -> str:
        cleaned = text.strip()
        if not cleaned:
            return CLIENT_FALLBACK_RESPONSE

        lowered = cleaned.lower()
        if any(fragment in lowered for fragment in _DISALLOWED_FRAGMENTS):
            logger.warning("Scenario agent response rejected for disallowed content.")
            return CLIENT_FALLBACK_RESPONSE

        max_len = settings.ai_response_max_length
        if len(cleaned) > max_len:
            cleaned = cleaned[:max_len].rstrip()
        return cleaned


scenario_agent = ScenarioAgent()
