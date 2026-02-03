import asyncpg
from loguru import logger

from src.config import settings
from src.data.models import DailyPrice, Stock


class DatabaseManager:
    """데이터베이스 관리 (asyncpg 기반)"""

    def __init__(self):
        self.pool: asyncpg.Pool | None = None

    async def connect(self):
        """연결 풀 생성"""
        self.pool = await asyncpg.create_pool(settings.database_url)
        logger.info("Database connection pool created")

    async def close(self):
        """연결 풀 종료"""
        if self.pool:
            await self.pool.close()
            logger.info("Database connection pool closed")

    async def save_stocks(self, stocks: list[Stock]):
        """종목 정보 저장

        Args:
            stocks: 저장할 Stock 객체 리스트
        """
        if not self.pool:
            raise RuntimeError("Database not connected")

        async with self.pool.acquire() as conn:
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

    async def save_daily_prices(self, prices: list[DailyPrice]):
        """일봉 데이터 저장

        Args:
            prices: 저장할 DailyPrice 객체 리스트
        """
        if not self.pool:
            raise RuntimeError("Database not connected")

        async with self.pool.acquire() as conn:
            await conn.executemany(
                """
                INSERT INTO daily_prices (stock_code, date, open_price, high_price, low_price, close_price, volume, trading_value, market_cap)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                ON CONFLICT (stock_code, date) DO UPDATE
                SET open_price = EXCLUDED.open_price,
                    high_price = EXCLUDED.high_price,
                    low_price = EXCLUDED.low_price,
                    close_price = EXCLUDED.close_price,
                    volume = EXCLUDED.volume,
                    trading_value = EXCLUDED.trading_value,
                    market_cap = EXCLUDED.market_cap
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

        logger.info(f"Saved {len(prices)} price records to database")

    async def get_latest_date(self, stock_code: str) -> str | None:
        """특정 종목의 최신 데이터 날짜 조회

        Args:
            stock_code: 종목 코드

        Returns:
            최신 날짜 (YYYY-MM-DD) 또는 None
        """
        if not self.pool:
            raise RuntimeError("Database not connected")

        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT MAX(date) as latest_date
                FROM daily_prices
                WHERE stock_code = $1
                """,
                stock_code,
            )

            if row and row["latest_date"]:
                return str(row["latest_date"].strftime("%Y%m%d"))
            return None

    async def stock_exists(self, stock_code: str) -> bool:
        """종목 존재 여부 확인

        Args:
            stock_code: 종목 코드

        Returns:
            존재 여부
        """
        if not self.pool:
            raise RuntimeError("Database not connected")

        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT COUNT(*) as count
                FROM stocks
                WHERE stock_code = $1
                """,
                stock_code,
            )

            return row["count"] > 0 if row else False
