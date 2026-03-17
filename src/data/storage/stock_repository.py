from __future__ import annotations

import asyncpg
from loguru import logger

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

    async def save(self, stocks: list[Stock]) -> None:
        async with self._pool.acquire() as conn:
            for stock in stocks:
                await conn.execute(
                    """
                    INSERT INTO stocks (stock_code, stock_name, market, sector, industry, is_active)
                    VALUES ($1, $2, $3, $4, $5, true)
                    ON CONFLICT (stock_code) DO UPDATE
                    SET stock_name = EXCLUDED.stock_name,
                        market = EXCLUDED.market,
                        sector = EXCLUDED.sector,
                        industry = EXCLUDED.industry,
                        updated_at = NOW()
                    """,
                    stock.stock_code,
                    stock.stock_name,
                    stock.market,
                    stock.sector,
                    stock.industry,
                )
        logger.info(f"Saved {len(stocks)} stocks to database")

    async def save_corp_code(self, stock_code: str, corp_code: str) -> None:
        async with self._pool.acquire() as conn:
            await conn.execute(
                "UPDATE stocks SET corp_code = $1 WHERE stock_code = $2",
                corp_code,
                stock_code,
            )
        logger.debug(f"Saved corp_code {corp_code} for {stock_code}")

    async def get_corp_code(self, stock_code: str) -> str | None:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT corp_code FROM stocks WHERE stock_code = $1",
                stock_code,
            )
        return row["corp_code"] if row and row["corp_code"] else None
