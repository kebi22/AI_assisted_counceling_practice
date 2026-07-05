"""CRUD operations for users."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import UserRole
from app.db.models.user import User


async def get_user_by_id(db: AsyncSession, user_id: uuid.UUID) -> User | None:
    return await db.get(User, user_id)


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_first_user_by_role(db: AsyncSession, role: UserRole) -> User | None:
    result = await db.execute(
        select(User).where(User.role == role, User.is_active.is_(True)).limit(1)
    )
    return result.scalar_one_or_none()


async def create_user(
    db: AsyncSession,
    *,
    name: str,
    email: str,
    role: UserRole,
) -> User:
    user = User(name=name, email=email, role=role, is_active=True)
    db.add(user)
    await db.flush()
    return user
