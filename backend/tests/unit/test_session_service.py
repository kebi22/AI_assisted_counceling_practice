"""Unit tests for session-service business rules."""

import uuid

import pytest

from app.core.exceptions import (
    AuthorizationError,
    ResourceNotFoundError,
    SessionStateError,
)
from app.core.constants import SessionStatus
from app.services.session_service import SessionService


class _FakeSession:
    def __init__(self, student_id, status=SessionStatus.ACTIVE):
        self.student_id = student_id
        self.status = status


def test_require_owned_session_missing():
    with pytest.raises(ResourceNotFoundError):
        SessionService._require_owned_session(None, uuid.uuid4())


def test_require_owned_session_wrong_owner():
    owner = uuid.uuid4()
    other = uuid.uuid4()
    with pytest.raises(AuthorizationError):
        SessionService._require_owned_session(_FakeSession(owner), other)


def test_require_owned_active_session_rejects_completed():
    owner = uuid.uuid4()
    service = SessionService()
    session = _FakeSession(owner, status=SessionStatus.COMPLETED)
    with pytest.raises(SessionStateError):
        service._require_owned_active_session(session, owner)


def test_require_owned_active_session_allows_active():
    owner = uuid.uuid4()
    service = SessionService()
    session = _FakeSession(owner, status=SessionStatus.ACTIVE)
    # Should not raise.
    service._require_owned_active_session(session, owner)
