"""Application-specific exceptions.

Services raise these domain exceptions. The API layer registers handlers that
translate them into appropriate HTTP responses (see ``app/main.py``).
"""


class AppError(Exception):
    """Base class for all application errors."""

    def __init__(self, message: str = "An application error occurred.") -> None:
        self.message = message
        super().__init__(message)


class ResourceNotFoundError(AppError):
    """A requested resource does not exist."""


class AuthorizationError(AppError):
    """The current user is not allowed to perform this action."""


class SessionStateError(AppError):
    """An operation is invalid for the session's current status."""


class ValidationError(AppError):
    """Faculty-supplied data failed a business-rule validation check."""


class ConflictError(AppError):
    """The action conflicts with the current state of the resource."""


class MinimumMessagesError(AppError):
    """The session has not met the minimum student-message requirement."""


class MessageLimitError(AppError):
    """The session has reached its maximum message count."""


class AIServiceError(AppError):
    """The AI provider failed or returned an unusable response."""


class EvaluationValidationError(AppError):
    """The structured evaluation returned by the model failed validation."""
