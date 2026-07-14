"""Schemas for audio-mode turns (speech I/O around the text pipeline)."""

import uuid

from pydantic import BaseModel

from app.schemas.message import MessageResponse


class SendAudioMessageResponse(BaseModel):
    """Result of a spoken student turn.

    ``transcript`` is what the student's speech was transcribed to (shown for
    transparency/confirmation). ``message`` is the client's text reply, and
    ``audio_base64`` is that reply synthesized to speech (base64 WAV).
    """

    session_id: uuid.UUID
    transcript: str
    message: MessageResponse
    audio_base64: str
    audio_mime_type: str = "audio/wav"
