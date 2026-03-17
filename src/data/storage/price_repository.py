from __future__ import annotations

import asyncio
from datetime import date
from typing import TYPE_CHECKING

import asyncpg
from loguru import logger

from src.data.freshness import calc_collection_range, get_collectible_end_date
from src.data.models import DailyPrice

if TYPE_CHECKING:
    from src.data.collectors.pykrx_collector import PyKrxCollector


class PriceRepository:
    def __init__(self, pool: asyncpg.Pool, collector: PyKrxCollector | None = None) -> None:
        self._pool = pool
        self._collector = collector

    async def ensure_fresh(self, stock_code: str) -> None:
        if self._collector is None:
            return

        collectible_end = get_collectible_end_date()
        db_latest = await self._get_latest_date_str(stock_code)
        collection_range = calc_collection_range(db_latest, collectible_end)

        if collection_range is None:
            return

        start, end = collection_range
        start_str = start.strftime("%Y%m%d")
        end_str = end.strftime("%Y%m%d")

        logger.info(f"{stock_code}: {start_str} ~ {end_str} 데이터 수집 시작")

        try:
            prices = await asyncio.to_thread(
                self._collector.get_ohlcv, stock_code, start_str, end_str
            )
            if not prices:
                logger.info(f"{stock_code}: 해당 기간 거래일 없음 (공휴일/휴장)")
                return
            await self._save(prices)
            logger.info(f"{stock_code}: {len(prices)}건 수집 완료 (최신: {prices[-1].date})")
        except Exception as e:
            logger.warning(f"{stock_code}: 수집 실패, 기존 데이터로 계속 - {e}")

    async def get_recent(self, stock_code: str, days: int = 60) -> list[DailyPrice]:
        await self.ensure_fresh(stock_code)
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT stock_code, date, open_price, high_price, low_price,
                       close_price, volume, trading_value, market_cap
                FROM daily_prices
                WHERE stock_code = $1
                ORDER BY date DESC
                LIMIT $2
                """,
                stock_code,
                days,
            )
        return [_row_to_price(row) for row in reversed(rows)]

    async def get_range(self, stock_code: str, start: date, end: date) -> list[DailyPrice]:
        await self.ensure_fresh(stock_code)
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT stock_code, date, open_price, high_price, low_price,
                       close_price, volume, trading_value, market_cap
                FROM daily_prices
                WHERE stock_code = $1
                  AND date BETWEEN $2 AND $3
                ORDER BY date DESC
                """,
                stock_code,
                start,
                end,
            )
        return [_row_to_price(row) for row in rows]

    async def get_bulk(
        self, stock_codes: list[str], start: date, end: date
    ) -> dict[str, list[DailyPrice]]:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT stock_code, date, open_price, high_price, low_price,
                       close_price, volume, trading_value, market_cap
                FROM daily_prices
                WHERE stock_code = ANY($1)
                  AND date BETWEEN $2 AND $3
                ORDER BY stock_code, date DESC
                """,
                stock_codes,
                start,
                end,
            )
        result: dict[str, list[DailyPrice]] = {}
        for row in rows:
            code = row["stock_code"]
            result.setdefault(code, []).append(_row_to_price(row))
        return result

    async def get_latest_date(self, stock_code: str) -> date | None:
        db_latest_str = await self._get_latest_date_str(stock_code)
        if db_latest_str is None:
            return None
        from datetime import datetime

        return datetime.strptime(db_latest_str, "%Y%m%d").date()

    async def _get_latest_date_str(self, stock_code: str) -> str | None:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT MAX(date) AS latest FROM daily_prices WHERE stock_code = $1",
                stock_code,
            )
        if row and row["latest"]:
            latest: date = row["latest"]
            return latest.strftime("%Y%m%d")
        return None

    async def save(self, prices: list[DailyPrice]) -> None:
        await self._save(prices)
        logger.info(f"Saved {len(prices)} price records to database")

    async def _save(self, prices: list[DailyPrice]) -> None:
        async with self._pool.acquire() as conn:
            await conn.executemany(
                """
                INSERT INTO daily_prices
                    (stock_code, date, open_price, high_price, low_price,
                     close_price, volume, trading_value, market_cap)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                ON CONFLICT (stock_code, date) DO UPDATE
                SET open_price    = EXCLUDED.open_price,
                    high_price    = EXCLUDED.high_price,
                    low_price     = EXCLUDED.low_price,
                    close_price   = EXCLUDED.close_price,
                    volume        = EXCLUDED.volume,
                    trading_value = EXCLUDED.trading_value,
                    market_cap    = EXCLUDED.market_cap
                """,
                [
                    (
                        p.stock_code,
                        p.date,
                        p.open_price,
                        p.high_price,
                        p.low_price,
                        p.close_price,
                        p.volume,
                        p.trading_value,
                        p.market_cap,
                    )
                    for p in prices
                ],
            )


def _row_to_price(row: asyncpg.Record) -> DailyPrice:
    return DailyPrice(
        stock_code=row["stock_code"],
        date=row["date"],
        open_price=row["open_price"],
        high_price=row["high_price"],
        low_price=row["low_price"],
        close_price=row["close_price"],
        volume=row["volume"],
        trading_value=row["trading_value"],
        market_cap=row["market_cap"],
    )
