from contextlib import asynccontextmanager

from fastapi_limiter import FastAPILimiter

from config import settings
from db.session import engine
from db.redis import redis
from utils import logger, scheduler


@asynccontextmanager
async def lifespan(app):
    """Asynchronous context manager to manage the lifespan of the application."""
    logger.info("Application started.....")

    scheduler.start()
    await FastAPILimiter.init(redis)
    yield

    # Graceful shutdown
    logger.info("Shutting down scheduler...")
    scheduler.shutdown()
    await redis.aclose()
    await engine.dispose()
    logger.info("Shutdown complete.")
