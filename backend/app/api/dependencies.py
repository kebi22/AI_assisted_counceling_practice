"""Reusable FastAPI dependencies.

Version 1 uses mock authentication. The dependency interface is shaped so a real
authentication scheme can replace ``get_current_user`` without changing call
sites or services.

To exercise faculty endpoints with the mock, send the header ``X-Demo-Role:
faculty``. Without it, requests are treated as the demo student.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthorizationError
from app.core.security import DEMO_FACULTY, DEMO_STUDENT, CurrentUser
from app.db.session import get_db_session


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async for session in get_db_session():
        yield session


async def get_current_user(
    x_demo_role: str | None = Header(default=None, alias="X-Demo-Role"),
) -> CurrentUser:
    """Return the current principal based on the mock demo-role header."""
    if x_demo_role and x_demo_role.strip().lower() == "faculty":
        return DEMO_FACULTY
    return DEMO_STUDENT


async def get_current_student(
    user: CurrentUser = Depends(get_current_user),
) -> CurrentUser:
    if not user.is_student:
        raise AuthorizationError("Student access is required.")
    return user


async def get_current_faculty(
    user: CurrentUser = Depends(get_current_user),
) -> CurrentUser:
    if not user.is_faculty:
        raise AuthorizationError("Faculty access is required.")
    return user
