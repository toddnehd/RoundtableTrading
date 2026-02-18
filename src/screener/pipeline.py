"""Pipeline to convert ScreeningResult to AnalysisData.

Bridges the screener output to agent input format.
"""

from datetime import date, timedelta

import asyncpg
from loguru import logger

from src.agents.base import AnalysisData
from src.config import settings
from src.data.models import DailyPrice, FinancialData
from src.screener.models import ScreeningResult


class ScreeningPipeline:
    """Converts screening results to analysis-ready data."""

    def __init__(self, pool: asyncpg.Pool | None = None):
        self._pool = pool
        self._own_pool = False

    async def connect(self) -> None:
        if self._pool is None:
            self._pool = await asyncpg.create_pool(settings.database_url)
            self._own_pool = True
            logger.info("Pipeline database pool created")

    async def close(self) -> None:
        if self._own_pool and self._pool:
            await self._pool.close()
            logger.info("Pipeline database pool closed")

    async def to_analysis_data(
        self,
        result: ScreeningResult,
        lookback_days: int = 60,
    ) -> AnalysisData:
        """Convert ScreeningResult to AnalysisData.

        Args:
            result: Screening result to convert.
            lookback_days: Number of days of price history to fetch.

        Returns:
            AnalysisData ready for agent analysis.
        """
        if not self._pool:
            raise RuntimeError("Pipeline not connected. Call connect() first.")

        async with self._pool.acquire() as conn:
            prices = await self._fetch_prices(conn, result.stock_code, lookback_days)
            financials = await self._fetch_financials(conn, result.stock_code)

        metadata = {
            "screening_score": str(result.score),
            "screening_reasons": ",".join(r.value for r in result.reasons),
        }
        for key, value in result.metrics.items():
            metadata[f"metric_{key}"] = str(round(value, 4))

        return AnalysisData(
            stock_code=result.stock_code,
            stock_name=result.stock_name,
            prices=prices,
            financials=financials,
            metadata=metadata,
        )

    async def to_analysis_data_batch(
        self,
        results: list[ScreeningResult],
        lookback_days: int = 60,
    ) -> list[AnalysisData]:
        """Convert multiple screening results to AnalysisData.

        Args:
            results: List of screening results.
            lookback_days: Number of days of price history.

        Returns:
            List of AnalysisData objects.
        """
        return [await self.to_analysis_data(result, lookback_days) for result in results]

    async def _fetch_prices(
        self,
        conn: asyncpg.Connection,
        stock_code: str,
        lookback_days: int,
    ) -> list[DailyPrice]:
        end_date = date.today()
        start_date = end_date - timedelta(days=lookback_days)

        query = """
            SELECT stock_code, date, open_price, high_price, low_price,
                   close_price, volume, trading_value, market_cap
            FROM daily_prices
            WHERE stock_code = $1
                AND date BETWEEN $2 AND $3
            ORDER BY date DESC
        """

        rows = await conn.fetch(query, stock_code, start_date, end_date)

        return [
            DailyPrice(
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
            for row in rows
        ]

    async def _fetch_financials(
        self,
        conn: asyncpg.Connection,
        stock_code: str,
    ) -> list[FinancialData]:
        query = """
            SELECT stock_code, quarter, revenue, operating_income, net_income,
                   per, pbr, roe, debt_ratio
            FROM financial_data
            WHERE stock_code = $1
            ORDER BY quarter DESC
            LIMIT 8
        """

        try:
            rows = await conn.fetch(query, stock_code)
        except Exception:
            return []

        return [
            FinancialData(
                stock_code=row["stock_code"],
                quarter=row["quarter"],
                revenue=row["revenue"],
                operating_income=row["operating_income"],
                net_income=row["net_income"],
                per=row["per"],
                pbr=row["pbr"],
                roe=row["roe"],
                debt_ratio=row["debt_ratio"],
            )
            for row in rows
        ]


async def screening_to_analysis(
    results: list[ScreeningResult],
    lookback_days: int = 60,
) -> list[AnalysisData]:
    """Convenience function to convert screening results.

    Args:
        results: Screening results to convert.
        lookback_days: Price history lookback period.

    Returns:
        List of AnalysisData objects.
    """
    pipeline = ScreeningPipeline()
    try:
        await pipeline.connect()
        return await pipeline.to_analysis_data_batch(results, lookback_days)
    finally:
        await pipeline.close()
