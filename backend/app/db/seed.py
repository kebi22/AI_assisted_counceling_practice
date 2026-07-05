"""Idempotent database seeding for Version 1.

Seeds one demo student, one demo faculty member, and the Module 1 scenario.
Safe to run multiple times: existing rows (matched by email/slug) are reused.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.prompts.module1_client import MODULE1_CLIENT_SYSTEM_PROMPT
from app.ai.prompts.module1_evaluator import MODULE1_RUBRIC
from app.core.constants import ScenarioStatus, UserRole
from app.core.logging import get_logger
from app.core.security import DEMO_FACULTY, DEMO_STUDENT
from app.crud import scenario as scenario_crud
from app.crud import user as user_crud

logger = get_logger(__name__)

MODULE1_SLUG = "module1_overwhelmed_teacher"

MODULE1_FIRST_CLIENT_MESSAGE = (
    "I guess I'm here because I've just been feeling really overwhelmed with work. "
    "I don't know if talking about it will actually help, though."
)

MODULE1_SCENARIO = {
    "module_number": 1,
    "title": "Module 1: Overwhelmed Teacher",
    "slug": MODULE1_SLUG,
    "description": (
        "You will speak with Jordan, a 29-year-old middle school teacher who feels "
        "overwhelmed and emotionally drained at work. Jordan is cooperative but "
        "hesitant and may only open up if you use empathy, reflection, and "
        "open-ended questions."
    ),
    "difficulty": "Easy",
    "client_name": "Jordan",
    "client_profile": {
        "age": 29,
        "occupation": "middle school teacher",
        "presenting_concern": "feeling overwhelmed and emotionally drained at work",
        "disposition": "cooperative but hesitant",
        "first_client_message": MODULE1_FIRST_CLIENT_MESSAGE,
        "skills": [
            "Empathy",
            "Reflection",
            "Open-ended questions",
            "Validation",
            "Pacing",
        ],
    },
    "student_goal": (
        "Demonstrate basic counseling microskills, including empathy, reflection, "
        "open-ended questioning, validation, and appropriate pacing."
    ),
    "system_prompt": MODULE1_CLIENT_SYSTEM_PROMPT,
    "rubric_json": MODULE1_RUBRIC,
    "is_active": True,
    "status": ScenarioStatus.PUBLISHED,
    "created_by": "seed",
}


async def seed_demo_users(db: AsyncSession) -> None:
    if await user_crud.get_user_by_email(db, DEMO_STUDENT.email) is None:
        await user_crud.create_user(
            db, name=DEMO_STUDENT.name, email=DEMO_STUDENT.email, role=UserRole.STUDENT
        )
        logger.info("Seeded demo student.")
    if await user_crud.get_user_by_email(db, DEMO_FACULTY.email) is None:
        await user_crud.create_user(
            db, name=DEMO_FACULTY.name, email=DEMO_FACULTY.email, role=UserRole.FACULTY
        )
        logger.info("Seeded demo faculty.")


async def seed_module1_scenario(db: AsyncSession) -> None:
    if await scenario_crud.get_scenario_by_slug(db, MODULE1_SLUG) is None:
        await scenario_crud.create_scenario(db, **MODULE1_SCENARIO)
        logger.info("Seeded Module 1 scenario.")


async def seed_database(db: AsyncSession) -> None:
    """Seed users and scenario in one transaction."""
    await seed_demo_users(db)
    await seed_module1_scenario(db)
    await db.commit()
