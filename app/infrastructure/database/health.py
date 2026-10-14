import logging

from sqlalchemy import text

from app.infrastructure.database.session import engine

logger = logging.getLogger(__name__)


async def check_database() -> dict[str, str]:
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
    except Exception:
        logger.exception("Database health check failed")
        return {"status": "unhealthy"}

    return {"status": "healthy"}
