"""Shared constants and enumerations used across the backend."""

from enum import StrEnum


class UserRole(StrEnum):
    STUDENT = "student"
    FACULTY = "faculty"
    ADMIN = "admin"


class ScenarioStatus(StrEnum):
    DRAFT = "draft"
    READY_FOR_TESTING = "ready_for_testing"
    PUBLISHED = "published"
    INACTIVE = "inactive"


class SessionStatus(StrEnum):
    ACTIVE = "active"
    COMPLETED = "completed"
    EVALUATING = "evaluating"
    EVALUATED = "evaluated"
    FAILED = "failed"
    REVIEWED = "reviewed"


class Speaker(StrEnum):
    CLIENT = "client"
    STUDENT = "student"
    SYSTEM = "system"


class ReviewStatus(StrEnum):
    PENDING = "pending"
    REVIEWED = "reviewed"
    NEEDS_REVISION = "needs_revision"


# Statuses that count as "completed" for faculty listing purposes.
FACULTY_VISIBLE_STATUSES: tuple[SessionStatus, ...] = (
    SessionStatus.COMPLETED,
    SessionStatus.EVALUATING,
    SessionStatus.EVALUATED,
    SessionStatus.FAILED,
    SessionStatus.REVIEWED,
)

AI_FEEDBACK_DISCLAIMER = (
    "AI-generated practice feedback is provided for educational support. "
    "Faculty review is required for formal evaluation."
)
