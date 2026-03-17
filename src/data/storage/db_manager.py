from __future__ import annotations

import asyncpg
from loguru import logger

from src.config import settings


class DatabaseManager:
    def __init__(self):
        self.pool: asyncpg.Pool | None = None

    async def connect(self) -> None:
        self.pool = await asyncpg.create_pool(settings.database_url)
        logger.info("Database connection pool created")

    async def close(self) -> None:
        if self.pool:
            await self.pool.close()
            logger.info("Database connection pool closed")
