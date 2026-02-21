import asyncpg
from loguru import logger

from src.config import settings
from src.data.models import DailyPrice, FinancialData, Stock


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

    async def save_financial_data(self, financials: list[FinancialData]) -> None:
        """Save financial data to database using UPSERT.

        Args:
            financials: List of FinancialData objects to save
        """
        if not self.pool:
            raise RuntimeError("Database not connected")

        async with self.pool.acquire() as conn:
            await conn.executemany(
                """
                INSERT INTO financial_data
                    (stock_code, quarter, revenue, operating_income, net_income,
                     per, pbr, roe, debt_ratio, eps, bps, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, NOW())
                ON CONFLICT (stock_code, quarter) DO UPDATE
                SET revenue = EXCLUDED.revenue,
                    operating_income = EXCLUDED.operating_income,
                    net_income = EXCLUDED.net_income,
                    per = EXCLUDED.per,
                    pbr = EXCLUDED.pbr,
                    roe = EXCLUDED.roe,
                    debt_ratio = EXCLUDED.debt_ratio,
                    eps = EXCLUDED.eps,
                    bps = EXCLUDED.bps,
                    updated_at = NOW()
                """,
                [
                    (
                        f.stock_code,
                        f.quarter,
                        f.revenue,
                        f.operating_income,
                        f.net_income,
                        f.per,
                        f.pbr,
                        f.roe,
                        f.debt_ratio,
                        f.eps,
                        f.bps,
                    )
                    for f in financials
                ],
            )
        logger.info(f"Saved {len(financials)} financial records to database")

    async def get_financial_data(self, stock_code: str, limit: int = 8) -> list[FinancialData]:
        """Get financial data for a stock, ordered by quarter descending.

        Args:
            stock_code: KRX stock code
            limit: Maximum number of records to return

        Returns:
            List of FinancialData objects
        """
        if not self.pool:
            raise RuntimeError("Database not connected")

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT stock_code, quarter, revenue, operating_income, net_income,
                       per, pbr, roe, debt_ratio, eps, bps
                FROM financial_data
                WHERE stock_code = $1
                ORDER BY quarter DESC
                LIMIT $2
                """,
                stock_code,
                limit,
            )

        return [
            FinancialData(
                stock_code=row["stock_code"],
                quarter=row["quarter"],
                revenue=float(row["revenue"]) if row["revenue"] is not None else None,
                operating_income=float(row["operating_income"])
                if row["operating_income"] is not None
                else None,
                net_income=float(row["net_income"]) if row["net_income"] is not None else None,
                per=float(row["per"]) if row["per"] is not None else None,
                pbr=float(row["pbr"]) if row["pbr"] is not None else None,
                roe=float(row["roe"]) if row["roe"] is not None else None,
                debt_ratio=float(row["debt_ratio"]) if row["debt_ratio"] is not None else None,
                eps=float(row["eps"]) if row["eps"] is not None else None,
                bps=float(row["bps"]) if row["bps"] is not None else None,
            )
            for row in rows
        ]

    async def save_corp_code(self, stock_code: str, corp_code: str) -> None:
        """Save DART corp_code for a stock.

        Args:
            stock_code: KRX stock code
            corp_code: DART 8-digit company code
        """
        if not self.pool:
            raise RuntimeError("Database not connected")

        async with self.pool.acquire() as conn:
            await conn.execute(
                "UPDATE stocks SET corp_code = $1 WHERE stock_code = $2",
                corp_code,
                stock_code,
            )
        logger.debug(f"Saved corp_code {corp_code} for {stock_code}")

    async def get_corp_code(self, stock_code: str) -> str | None:
        """Get DART corp_code for a stock.

        Args:
            stock_code: KRX stock code

        Returns:
            DART corp_code or None if not found
        """
        if not self.pool:
            raise RuntimeError("Database not connected")

        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT corp_code FROM stocks WHERE stock_code = $1",
                stock_code,
            )

        return row["corp_code"] if row and row["corp_code"] else None
