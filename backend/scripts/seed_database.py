"""Seed the database with demo users and the Module 1 scenario.

Usage:
    python -m scripts.seed_database
"""

import asyncio

from app.core.logging import configure_logging, get_logger
from app.db.seed import seed_database
from app.db.session import AsyncSessionFactory

logger = get_logger(__name__)


async def main() -> None:
    configure_logging()
    async with AsyncSessionFactory() as session:
        await seed_database(session)
    logger.info("Seeding complete.")


if __name__ == "__main__":
    asyncio.run(main())
