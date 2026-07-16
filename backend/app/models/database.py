"""
PatentPilot Database Module.

Manages the async MongoDB connection via the motor driver.
"""

import logging

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.config import settings

logger = logging.getLogger(__name__)

# Module-level state
_client: AsyncIOMotorClient | None = None
_db: AsyncIOMotorDatabase | None = None


async def init_db() -> None:
    """
    Initialize the MongoDB connection.

    Creates an AsyncIOMotorClient and stores a reference to the
    configured database.
    """
    global _client, _db
    logger.info("Connecting to MongoDB at %s ...", settings.MONGODB_URI)
    _client = AsyncIOMotorClient(settings.MONGODB_URI)
    _db = _client[settings.MONGODB_DB_NAME]

    # Verify connectivity
    try:
        await _client.admin.command("ping")
        logger.info("MongoDB connection established — database: %s", settings.MONGODB_DB_NAME)
    except Exception as exc:
        logger.warning("MongoDB ping failed (server may not be running): %s", exc)


async def close_db() -> None:
    """Close the MongoDB connection."""
    global _client, _db
    if _client is not None:
        _client.close()
        logger.info("MongoDB connection closed.")
    _client = None
    _db = None


def get_db() -> AsyncIOMotorDatabase:
    """
    Return the current database reference.

    Raises RuntimeError if init_db() has not been called.
    """
    if _db is None:
        raise RuntimeError("Database not initialised. Call init_db() first.")
    return _db


def get_analyses_collection():
    """Return the 'analyses' collection from the active database."""
    return get_db()["analyses"]
