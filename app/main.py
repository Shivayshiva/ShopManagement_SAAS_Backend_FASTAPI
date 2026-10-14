from fastapi import FastAPI

from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging
from app.core.middleware import register_middleware
from app.infrastructure.database.health import check_database
from app.modules.identity.router import router as identity_router

configure_logging()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
)

register_middleware(app)
register_exception_handlers(app)
app.include_router(identity_router)


@app.get("/", include_in_schema=False)
async def root():
    return {
        "message": settings.APP_NAME,
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
async def health_check():
    database = await check_database()
    status = "healthy" if database["status"] in {"healthy", "skipped"} else "unhealthy"
    return {
        "status": status,
        "database": database,
    }
