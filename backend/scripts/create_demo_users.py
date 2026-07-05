"""Create only the demo users (student + faculty).

Usage:
    python -m scripts.create_demo_users
"""

import asyncio

from app.core.logging import configure_logging, get_logger
from app.db.seed import seed_demo_users
from app.db.session import AsyncSessionFactory

logger = get_logger(__name__)


async def main() -> None:
    configure_logging()
    async with AsyncSessionFactory() as session:
        await seed_demo_users(session)
        await session.commit()
    logger.info("Demo users ready.")


if __name__ == "__main__":
    asyncio.run(main())
