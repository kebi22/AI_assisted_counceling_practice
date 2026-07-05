"""Pagination helpers (reserved for future list endpoints)."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Page:
    limit: int = 50
    offset: int = 0

    def clamped(self, max_limit: int = 200) -> "Page":
        return Page(limit=min(self.limit, max_limit), offset=max(self.offset, 0))
