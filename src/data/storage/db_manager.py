from __future__ import annotations

from datetime import date

import asyncpg
from loguru import logger

from src.config import settings
from src.data.models import DailyPrice, FinancialData, InvestorFlow, MacroSnapshot, Stock


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
                     per, pbr, roe, debt_ratio, eps, bps, fs_div,
                     operating_margin, net_margin, roa, ebitda,
                     current_ratio, quick_ratio, interest_coverage, capital_retention_ratio,
                     ev_ebitda, dps, dividend_yield,
                     revenue_growth, operating_income_growth, net_income_growth,
                     updated_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12,
                        $13, $14, $15, $16, $17, $18, $19, $20, $21, $22, $23,
                        $24, $25, $26, NOW())
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
                    fs_div = EXCLUDED.fs_div,
                    operating_margin = EXCLUDED.operating_margin,
                    net_margin = EXCLUDED.net_margin,
                    roa = EXCLUDED.roa,
                    ebitda = EXCLUDED.ebitda,
                    current_ratio = EXCLUDED.current_ratio,
                    quick_ratio = EXCLUDED.quick_ratio,
                    interest_coverage = EXCLUDED.interest_coverage,
                    capital_retention_ratio = EXCLUDED.capital_retention_ratio,
                    ev_ebitda = EXCLUDED.ev_ebitda,
                    dps = EXCLUDED.dps,
                    dividend_yield = EXCLUDED.dividend_yield,
                    revenue_growth = EXCLUDED.revenue_growth,
                    operating_income_growth = EXCLUDED.operating_income_growth,
                    net_income_growth = EXCLUDED.net_income_growth,
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
                        f.fs_div,
                        f.operating_margin,
                        f.net_margin,
                        f.roa,
                        f.ebitda,
                        f.current_ratio,
                        f.quick_ratio,
                        f.interest_coverage,
                        f.capital_retention_ratio,
                        f.ev_ebitda,
                        f.dps,
                        f.dividend_yield,
                        f.revenue_growth,
                        f.operating_income_growth,
                        f.net_income_growth,
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
                       per, pbr, roe, debt_ratio, eps, bps, fs_div,
                       operating_margin, net_margin, roa, ebitda,
                       current_ratio, quick_ratio, interest_coverage, capital_retention_ratio,
                       ev_ebitda, dps, dividend_yield,
                       revenue_growth, operating_income_growth, net_income_growth
                FROM financial_data
                WHERE stock_code = $1
                ORDER BY quarter DESC
                LIMIT $2
                """,
                stock_code,
                limit,
            )

        def _float(v: object) -> float | None:
            if v is None:
                return None
            return float(v)  # type: ignore[arg-type]

        return [
            FinancialData(
                stock_code=row["stock_code"],
                quarter=row["quarter"],
                revenue=_float(row["revenue"]),
                operating_income=_float(row["operating_income"]),
                net_income=_float(row["net_income"]),
                per=_float(row["per"]),
                pbr=_float(row["pbr"]),
                roe=_float(row["roe"]),
                debt_ratio=_float(row["debt_ratio"]),
                eps=_float(row["eps"]),
                bps=_float(row["bps"]),
                fs_div=row["fs_div"],
                operating_margin=_float(row["operating_margin"]),
                net_margin=_float(row["net_margin"]),
                roa=_float(row["roa"]),
                ebitda=_float(row["ebitda"]),
                current_ratio=_float(row["current_ratio"]),
                quick_ratio=_float(row["quick_ratio"]),
                interest_coverage=_float(row["interest_coverage"]),
                capital_retention_ratio=_float(row["capital_retention_ratio"]),
                ev_ebitda=_float(row["ev_ebitda"]),
                dps=_float(row["dps"]),
                dividend_yield=_float(row["dividend_yield"]),
                revenue_growth=_float(row["revenue_growth"]),
                operating_income_growth=_float(row["operating_income_growth"]),
                net_income_growth=_float(row["net_income_growth"]),
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

    async def save_macro_indicators(self, snapshots: list[MacroSnapshot]) -> None:
        """Save macro economic indicators to database using UPSERT.

        Args:
            snapshots: List of MacroSnapshot objects to save
        """
        if not self.pool:
            raise RuntimeError("Database not connected")

        async with self.pool.acquire() as conn:
            await conn.executemany(
                """
                INSERT INTO macro_indicators
                    (date, base_rate, usd_krw, cpi_yoy, kospi, kosdaq, export_yoy)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (date) DO UPDATE
                SET base_rate = EXCLUDED.base_rate,
                    usd_krw = EXCLUDED.usd_krw,
                    cpi_yoy = EXCLUDED.cpi_yoy,
                    kospi = EXCLUDED.kospi,
                    kosdaq = EXCLUDED.kosdaq,
                    export_yoy = EXCLUDED.export_yoy
                """,
                [
                    (
                        s.date,
                        s.base_rate,
                        s.usd_krw,
                        s.cpi_yoy,
                        s.kospi,
                        s.kosdaq,
                        s.export_yoy,
                    )
                    for s in snapshots
                ],
            )
        logger.info(f"Saved {len(snapshots)} macro indicator records to database")

    async def get_macro_snapshot(self, target_date: date) -> MacroSnapshot | None:
        """Get the most recent macro snapshot on or before target_date.

        Args:
            target_date: Reference date to look up

        Returns:
            Most recent MacroSnapshot or None if not found
        """
        if not self.pool:
            raise RuntimeError("Database not connected")

        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT date, base_rate, usd_krw, cpi_yoy, kospi, kosdaq, export_yoy
                FROM macro_indicators
                WHERE date <= $1
                ORDER BY date DESC
                LIMIT 1
                """,
                target_date,
            )

        if row is None:
            return None

        def _float(v: object) -> float | None:
            if v is None:
                return None
            return float(v)  # type: ignore[arg-type]

        return MacroSnapshot(
            date=row["date"],
            base_rate=_float(row["base_rate"]),
            usd_krw=_float(row["usd_krw"]),
            cpi_yoy=_float(row["cpi_yoy"]),
            kospi=_float(row["kospi"]),
            kosdaq=_float(row["kosdaq"]),
            export_yoy=_float(row["export_yoy"]),
        )

    async def save_investor_trading(self, flows: list[InvestorFlow]) -> None:
        """Save investor trading flow data to database using UPSERT.

        Args:
            flows: List of InvestorFlow objects to save
        """
        if not self.pool:
            raise RuntimeError("Database not connected")

        async with self.pool.acquire() as conn:
            await conn.executemany(
                """
                INSERT INTO investor_trading
                    (stock_code, date, foreign_net, institution_net, retail_net)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (stock_code, date) DO UPDATE
                SET foreign_net = EXCLUDED.foreign_net,
                    institution_net = EXCLUDED.institution_net,
                    retail_net = EXCLUDED.retail_net
                """,
                [
                    (
                        f.stock_code,
                        f.date,
                        f.foreign_net,
                        f.institution_net,
                        f.retail_net,
                    )
                    for f in flows
                ],
            )
        logger.info(f"Saved {len(flows)} investor trading records to database")

    async def get_investor_trading(self, stock_code: str, limit: int = 20) -> list[InvestorFlow]:
        """Get investor trading flow data for a stock.

        Args:
            stock_code: KRX stock code
            limit: Maximum number of records to return

        Returns:
            List of InvestorFlow objects ordered by date descending
        """
        if not self.pool:
            raise RuntimeError("Database not connected")

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT stock_code, date, foreign_net, institution_net, retail_net
                FROM investor_trading
                WHERE stock_code = $1
                ORDER BY date DESC
                LIMIT $2
                """,
                stock_code,
                limit,
            )

        def _int(v: object) -> int | None:
            if v is None:
                return None
            return int(v)  # type: ignore[arg-type, no-any-return, call-overload]

        return [
            InvestorFlow(
                stock_code=row["stock_code"],
                date=row["date"],
                foreign_net=_int(row["foreign_net"]),
                institution_net=_int(row["institution_net"]),
                retail_net=_int(row["retail_net"]),
            )
            for row in rows
        ]

    async def save_market_indices(self, data: list[tuple[date, float, float]]) -> None:
        """Save market index data (KOSPI/KOSDAQ) to database using UPSERT.

        Args:
            data: List of (date, kospi, kosdaq) tuples
        """
        if not self.pool:
            raise RuntimeError("Database not connected")

        async with self.pool.acquire() as conn:
            await conn.executemany(
                """
                INSERT INTO market_indices (date, kospi, kosdaq)
                VALUES ($1, $2, $3)
                ON CONFLICT (date) DO UPDATE
                SET kospi = EXCLUDED.kospi,
                    kosdaq = EXCLUDED.kosdaq
                """,
                data,
            )
        logger.info(f"Saved {len(data)} market index records to database")
