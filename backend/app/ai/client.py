"""Reusable Gemini client wrapper for Developer API and Vertex AI."""

from __future__ import annotations

import time
from typing import Any, TypeVar

from pydantic import BaseModel

from app.core.config import settings
from app.core.exceptions import AIServiceError
from app.core.logging import get_logger, log_ai_call

logger = get_logger(__name__)

_T = TypeVar("_T", bound=BaseModel)

# Per-call timeout in milliseconds (Google Gen AI SDK uses ms for http timeouts).
_REQUEST_TIMEOUT_MS = 30_000


class GeminiClient:
    """Thin async wrapper around the Google Gen AI SDK."""

    def __init__(self) -> None:
        self._client: Any | None = None

    def _get_client(self) -> Any:
        if not settings.gemini_configured:
            raise AIServiceError(
                f"Gemini provider {settings.ai_provider!r} is not configured."
            )
        if self._client is None:
            try:
                from google import genai
                from google.genai import types

                http_options = types.HttpOptions(timeout=_REQUEST_TIMEOUT_MS)
                if settings.ai_provider == "vertex_ai":
                    self._client = genai.Client(
                        vertexai=True,
                        project=settings.google_cloud_project,
                        location=settings.google_cloud_location,
                        http_options=http_options,
                    )
                elif settings.ai_provider == "gemini_developer_api":
                    self._client = genai.Client(
                        api_key=settings.gemini_api_key,
                        http_options=http_options,
                    )
                else:
                    raise AIServiceError(
                        f"Unsupported Gemini provider: {settings.ai_provider!r}."
                    )
            except ImportError as exc:  # pragma: no cover - depends on environment
                raise AIServiceError("Google Gen AI SDK is not installed.") from exc
        return self._client

    async def generate_text(
        self,
        *,
        model: str,
        system_instruction: str,
        prompt: str,
        max_output_tokens: int = 512,
        disable_thinking: bool = False,
        session_id: str | None = None,
    ) -> str:
        """Generate a plain-text completion.

        ``disable_thinking`` turns off the "thinking" budget on Gemini 2.5+
        models. Those reasoning tokens otherwise count against
        ``max_output_tokens`` and can truncate short replies (finish reason
        ``MAX_TOKENS``), so it should be set for simple roleplay turns.
        """
        from google.genai import types

        client = self._get_client()
        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            max_output_tokens=max_output_tokens,
            temperature=0.8,
            thinking_config=(
                types.ThinkingConfig(thinking_budget=0) if disable_thinking else None
            ),
        )
        started = time.perf_counter()
        try:
            response = await client.aio.models.generate_content(
                model=model,
                contents=prompt,
                config=config,
            )
        except Exception as exc:  # noqa: BLE001 - re-raised as domain error with logging
            log_ai_call(
                logger,
                agent="generate_text",
                model=model,
                duration_ms=(time.perf_counter() - started) * 1000,
                success=False,
                session_id=session_id,
            )
            raise AIServiceError("The AI service failed to generate a response.") from exc

        log_ai_call(
            logger,
            agent="generate_text",
            model=model,
            duration_ms=(time.perf_counter() - started) * 1000,
            success=True,
            session_id=session_id,
        )
        text = (response.text or "").strip()
        if not text:
            raise AIServiceError("The AI service returned an empty response.")
        return text

    async def transcribe_audio(
        self,
        *,
        model: str,
        audio_bytes: bytes,
        mime_type: str,
        session_id: str | None = None,
    ) -> str:
        """Transcribe a student audio clip to plain text.

        Used at the edge of the audio pipeline; the transcript then flows into
        the unchanged text turn pipeline.
        """
        from google.genai import types

        client = self._get_client()
        config = types.GenerateContentConfig(
            temperature=0.0,
            max_output_tokens=1024,
            thinking_config=types.ThinkingConfig(thinking_budget=0),
        )
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_bytes(data=audio_bytes, mime_type=mime_type),
                    types.Part.from_text(
                        text=(
                            "Transcribe the spoken words in this audio verbatim. "
                            "Return only the transcript text, with no commentary, "
                            "labels, or timestamps."
                        )
                    ),
                ],
            )
        ]
        started = time.perf_counter()
        try:
            response = await client.aio.models.generate_content(
                model=model, contents=contents, config=config
            )
        except Exception as exc:  # noqa: BLE001
            log_ai_call(
                logger,
                agent="transcribe_audio",
                model=model,
                duration_ms=(time.perf_counter() - started) * 1000,
                success=False,
                session_id=session_id,
            )
            raise AIServiceError("Speech-to-text failed.") from exc

        log_ai_call(
            logger,
            agent="transcribe_audio",
            model=model,
            duration_ms=(time.perf_counter() - started) * 1000,
            success=True,
            session_id=session_id,
        )
        text = (response.text or "").strip()
        if not text:
            raise AIServiceError("Speech-to-text returned an empty transcript.")
        return text

    async def synthesize_speech(
        self,
        *,
        model: str,
        text: str,
        voice: str,
        session_id: str | None = None,
    ) -> bytes:
        """Synthesize spoken audio for the client's reply.

        Returns raw PCM (16-bit, 24kHz mono) bytes as produced by the Gemini
        TTS models. The caller is responsible for wrapping into a container
        (e.g. WAV) if needed for the browser.
        """
        from google.genai import types

        client = self._get_client()
        config = types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice)
                )
            ),
        )
        started = time.perf_counter()
        try:
            response = await client.aio.models.generate_content(
                model=model, contents=text, config=config
            )
        except Exception as exc:  # noqa: BLE001
            log_ai_call(
                logger,
                agent="synthesize_speech",
                model=model,
                duration_ms=(time.perf_counter() - started) * 1000,
                success=False,
                session_id=session_id,
            )
            raise AIServiceError("Text-to-speech failed.") from exc

        log_ai_call(
            logger,
            agent="synthesize_speech",
            model=model,
            duration_ms=(time.perf_counter() - started) * 1000,
            success=True,
            session_id=session_id,
        )
        try:
            data = response.candidates[0].content.parts[0].inline_data.data
        except (AttributeError, IndexError, TypeError) as exc:
            raise AIServiceError("Text-to-speech returned no audio.") from exc
        if not data:
            raise AIServiceError("Text-to-speech returned empty audio.")
        return data

    async def generate_structured(
        self,
        *,
        model: str,
        system_instruction: str,
        prompt: str,
        schema: type[_T],
        enforce_schema: bool = False,
        session_id: str | None = None,
    ) -> _T:
        """Generate structured output validated against a Pydantic schema."""
        from google.genai import types

        client = self._get_client()
        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            response_mime_type="application/json",
            response_schema=schema if enforce_schema else None,
            temperature=0.4,
            max_output_tokens=4096,
            thinking_config=types.ThinkingConfig(thinking_budget=0),
        )
        started = time.perf_counter()
        try:
            response = await client.aio.models.generate_content(
                model=model,
                contents=prompt,
                config=config,
            )
        except Exception as exc:  # noqa: BLE001 - re-raised as domain error with logging
            log_ai_call(
                logger,
                agent="generate_structured",
                model=model,
                duration_ms=(time.perf_counter() - started) * 1000,
                success=False,
                session_id=session_id,
            )
            raise AIServiceError("The AI evaluation service failed.") from exc

        log_ai_call(
            logger,
            agent="generate_structured",
            model=model,
            duration_ms=(time.perf_counter() - started) * 1000,
            success=True,
            session_id=session_id,
        )

        parsed = getattr(response, "parsed", None)
        if isinstance(parsed, schema):
            return parsed
        if parsed is not None:
            try:
                return schema.model_validate(parsed)
            except Exception as exc:  # noqa: BLE001
                raise AIServiceError(
                    "The AI evaluation returned malformed structured output."
                ) from exc
        # Fall back to validating the raw JSON text.
        raw_text = response.text or ""
        try:
            return schema.model_validate_json(raw_text)
        except Exception as exc:  # noqa: BLE001
            raise AIServiceError("The AI evaluation returned malformed output.") from exc


# Module-level singleton reused across requests.
gemini_client = GeminiClient()
