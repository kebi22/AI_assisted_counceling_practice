"""Session endpoints: create, fetch, send message, complete."""

import uuid

from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_student, get_db
from app.core.security import CurrentUser
from app.schemas.audio import SendAudioMessageResponse
from app.schemas.message import MessageCreate, SendMessageResponse
from app.schemas.session import (
    SessionCompleteRequest,
    SessionCreate,
    SessionDetailResponse,
    StudentSessionSummary,
)
from app.services.session_service import session_service

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("", response_model=SessionDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    payload: SessionCreate,
    db: AsyncSession = Depends(get_db),
    student: CurrentUser = Depends(get_current_student),
) -> SessionDetailResponse:
    return await session_service.start_session(
        db, student, payload.scenario_id, payload.modality
    )


@router.get("", response_model=list[StudentSessionSummary])
async def list_my_sessions(
    db: AsyncSession = Depends(get_db),
    student: CurrentUser = Depends(get_current_student),
) -> list[StudentSessionSummary]:
    return await session_service.list_my_sessions(db, student)


@router.get("/{session_id}", response_model=SessionDetailResponse)
async def get_session(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    student: CurrentUser = Depends(get_current_student),
) -> SessionDetailResponse:
    return await session_service.get_student_session(db, student, session_id)


@router.post(
    "/{session_id}/messages",
    response_model=SendMessageResponse,
    status_code=status.HTTP_201_CREATED,
)
async def send_message(
    session_id: uuid.UUID,
    payload: MessageCreate,
    db: AsyncSession = Depends(get_db),
    student: CurrentUser = Depends(get_current_student),
) -> SendMessageResponse:
    return await session_service.send_student_message(
        db, student, session_id, payload.content
    )


@router.post(
    "/{session_id}/audio-messages",
    response_model=SendAudioMessageResponse,
    status_code=status.HTTP_201_CREATED,
)
async def send_audio_message(
    session_id: uuid.UUID,
    audio: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    student: CurrentUser = Depends(get_current_student),
) -> SendAudioMessageResponse:
    """Spoken student turn: audio in -> STT -> text pipeline -> TTS reply out."""
    audio_bytes = await audio.read()
    return await session_service.send_student_audio_message(
        db,
        student,
        session_id,
        audio_bytes=audio_bytes,
        mime_type=audio.content_type or "audio/webm",
    )


@router.post("/{session_id}/complete", response_model=SessionDetailResponse)
async def complete_session(
    session_id: uuid.UUID,
    payload: SessionCompleteRequest | None = None,
    db: AsyncSession = Depends(get_db),
    student: CurrentUser = Depends(get_current_student),
) -> SessionDetailResponse:
    """Complete a session; video sessions may attach a nonverbal metrics summary."""
    return await session_service.complete_session(
        db,
        student,
        session_id,
        nonverbal_summary=payload.nonverbal_summary if payload else None,
    )
