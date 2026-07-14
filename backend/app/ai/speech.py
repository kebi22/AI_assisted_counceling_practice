"""Speech I/O layer for audio/video modes.

This is a deliberate seam: the rest of the app depends only on the
``SpeechAdapter`` protocol, so the Gemini implementation can later be swapped
for a browser-side STT + a different TTS vendor without touching the turn
pipeline. Audio is converted to/from text at the edges; the deterministic text
core is never bypassed.
"""

from __future__ import annotations

import io
import wave
from typing import Protocol

from app.ai.client import GeminiClient, gemini_client
from app.core.config import settings

# Gemini TTS models emit signed 16-bit little-endian PCM, 24kHz, mono.
_TTS_SAMPLE_RATE = 24_000
_TTS_SAMPLE_WIDTH = 2
_TTS_CHANNELS = 1


def pcm_to_wav(
    pcm_bytes: bytes,
    *,
    sample_rate: int = _TTS_SAMPLE_RATE,
    sample_width: int = _TTS_SAMPLE_WIDTH,
    channels: int = _TTS_CHANNELS,
) -> bytes:
    """Wrap raw PCM bytes in a WAV container the browser can play directly."""
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav:
        wav.setnchannels(channels)
        wav.setsampwidth(sample_width)
        wav.setframerate(sample_rate)
        wav.writeframes(pcm_bytes)
    return buffer.getvalue()


class SpeechResult:
    """Synthesized speech plus the container metadata needed to play it."""

    def __init__(self, wav_bytes: bytes, sample_rate: int = _TTS_SAMPLE_RATE) -> None:
        self.wav_bytes = wav_bytes
        self.sample_rate = sample_rate


class SpeechAdapter(Protocol):
    """Speech-to-text and text-to-speech boundary for audio/video modes."""

    async def transcribe(
        self, *, audio_bytes: bytes, mime_type: str, session_id: str | None = None
    ) -> str: ...

    async def synthesize(
        self, *, text: str, voice: str | None = None, session_id: str | None = None
    ) -> SpeechResult: ...


class GeminiSpeechAdapter:
    """SpeechAdapter backed by the Gemini API (single-vendor MVP)."""

    def __init__(self, client: GeminiClient | None = None) -> None:
        self._client = client or gemini_client

    async def transcribe(
        self, *, audio_bytes: bytes, mime_type: str, session_id: str | None = None
    ) -> str:
        return await self._client.transcribe_audio(
            model=settings.gemini_stt_model,
            audio_bytes=audio_bytes,
            mime_type=mime_type,
            session_id=session_id,
        )

    async def synthesize(
        self, *, text: str, voice: str | None = None, session_id: str | None = None
    ) -> SpeechResult:
        pcm = await self._client.synthesize_speech(
            model=settings.gemini_tts_model,
            text=text,
            voice=voice or settings.gemini_tts_voice,
            session_id=session_id,
        )
        return SpeechResult(pcm_to_wav(pcm))


# Module-level singleton; swap this binding to change speech providers.
speech_adapter: SpeechAdapter = GeminiSpeechAdapter()
