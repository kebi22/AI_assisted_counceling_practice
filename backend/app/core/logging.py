"""Structured application logging configuration.

Never log API keys, raw model credentials, or full student transcripts in
production. Helper functions here intentionally accept only identifiers and
durations rather than free-form content.
"""

import logging
import sys

from app.core.config import settings

_CONFIGURED = False


def configure_logging() -> None:
    """Configure root logging once for the application."""
    global _CONFIGURED
    if _CONFIGURED:
        return

    level = logging.DEBUG if settings.debug else logging.INFO
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s %(levelname)s [%(name)s] %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S%z",
        )
    )

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)

    # Quiet noisy third-party loggers in development.
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    """Return a namespaced logger."""
    return logging.getLogger(name)


def log_ai_call(
    logger: logging.Logger,
    *,
    agent: str,
    model: str,
    duration_ms: float,
    success: bool,
    session_id: str | None = None,
) -> None:
    """Log an AI call with timing metadata but no transcript content."""
    logger.info(
        "ai_call agent=%s model=%s session_id=%s duration_ms=%.1f success=%s",
        agent,
        model,
        session_id or "-",
        duration_ms,
        success,
    )
