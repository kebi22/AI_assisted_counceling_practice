"""Simulation session schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel

from app.core.constants import SessionStatus
from app.schemas.common import ORMModel
from app.schemas.evaluation import EvaluationResponse
from app.schemas.message import MessageResponse


class SessionCreate(BaseModel):
    scenario_id: uuid.UUID


class SessionResponse(ORMModel):
    id: uuid.UUID
    student_id: uuid.UUID
    scenario_id: uuid.UUID
    scenario_version_id: uuid.UUID | None = None
    status: SessionStatus
    student_message_count: int
    started_at: datetime | None
    ended_at: datetime | None
    created_at: datetime


class SessionDetailResponse(SessionResponse):
    scenario_title: str
    client_name: str
    student_name: str
    messages: list[MessageResponse]
    evaluation: EvaluationResponse | None = None


class StudentSessionSummary(BaseModel):
    """One row in the student's "previous attempts" list."""

    session_id: uuid.UUID
    scenario_title: str
    status: SessionStatus
    overall_score: float | None
    created_at: datetime
    completed_at: datetime | None


class FacultySessionSummary(BaseModel):
    """One row in the faculty session list."""

    session_id: uuid.UUID
    student_name: str
    scenario_title: str
    status: SessionStatus
    overall_score: float | None
    completed_at: datetime | None
    review_status: str | None


class FacultySessionDetail(SessionDetailResponse):
    faculty_comment: str = ""
    review_status: str | None = None
    adjusted_score: float | None = None
    prompt_trace: dict | None = None
