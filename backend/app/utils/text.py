"""Text helpers."""

import re

_TAG_RE = re.compile(r"<[^>]+>")


def strip_html(value: str) -> str:
    """Remove HTML tags from user-provided text.

    Student input must not contain HTML (see Backend.md security requirements).
    """
    return _TAG_RE.sub("", value).strip()


def truncate(value: str, max_length: int) -> str:
    """Truncate ``value`` to ``max_length`` characters without cutting mid-space."""
    if len(value) <= max_length:
        return value
    return value[:max_length].rstrip()
