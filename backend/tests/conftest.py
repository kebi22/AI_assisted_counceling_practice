"""Shared pytest fixtures.

Tests run against an in-memory SQLite database (cross-dialect column types are
used in the models) and never call the live Gemini API.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

from app.api.dependencies import get_db
from app.core.constants import UserRole
from app.crud import simulation_session as session_crud
from app.crud import user as user_crud
from app.db import seed as seed_module
from app.db.base import Base
from app.main import app

TEST_DATABASE_URL = "sqlite+aiosqlite://"


@pytest_asyncio.fixture
async def db_engine():
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def session_factory(db_engine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(bind=db_engine, expire_on_commit=False, autoflush=False)


@pytest_asyncio.fixture
async def db_session(session_factory) -> AsyncGenerator[AsyncSession, None]:
    async with session_factory() as session:
        yield session


@pytest_asyncio.fixture
async def seeded(session_factory) -> None:
    async with session_factory() as session:
        await seed_module.seed_database(session)


@pytest_asyncio.fixture
async def client(session_factory, seeded) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def scenario_id(client) -> str:
    """Return the seeded Module 1 scenario id."""
    response = await client.get("/api/v1/scenarios")
    assert response.status_code == 200
    return response.json()[0]["id"]


async def create_other_student_session(
    session_factory, scenario_id_value: str
) -> uuid.UUID:
    """Create a session owned by a different student. Returns the session id."""
    async with session_factory() as session:
        other = await user_crud.create_user(
            session,
            name="Other Student",
            email="other.student@example.edu",
            role=UserRole.STUDENT,
        )
        sim = await session_crud.create_session(
            session,
            student_id=other.id,
            scenario_id=uuid.UUID(scenario_id_value),
        )
        await session.commit()
        return sim.id
