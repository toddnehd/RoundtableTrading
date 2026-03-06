from __future__ import annotations

import asyncpg

from src.data.models import Stock


class StockRepository:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def get(self, stock_code: str) -> Stock | None:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT stock_code, stock_name, market, sector, industry FROM stocks WHERE stock_code = $1",
                stock_code,
            )
        if not row:
            return None
        return Stock(
            stock_code=row["stock_code"],
            stock_name=row["stock_name"],
            market=row["market"],
            sector=row["sector"],
            industry=row["industry"],
        )

    async def exists(self, stock_code: str) -> bool:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT 1 FROM stocks WHERE stock_code = $1",
                stock_code,
            )
        return row is not None
