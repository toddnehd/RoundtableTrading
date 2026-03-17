"""Pipeline to convert ScreeningResult to AnalysisData.

Bridges the screener output to agent input format.
"""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING

import asyncpg
from loguru import logger

from src.agents.base import AnalysisData
from src.config import settings
from src.data.freshness import get_collectible_end_date
from src.data.storage import FinancialRepository, PriceRepository
from src.screener.models import ScreeningResult

if TYPE_CHECKING:
    from src.data.collectors.pykrx_collector import PyKrxCollector


class ScreeningPipeline:
    """Converts screening results to analysis-ready data."""

    def __init__(
        self,
        pool: asyncpg.Pool | None = None,
        collector: PyKrxCollector | None = None,
    ):
        self._pool = pool
        self._own_pool = False
        self._collector = collector

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

        end_date = get_collectible_end_date()
        start_date = end_date - timedelta(days=lookback_days)

        price_repo = PriceRepository(self._pool, self._collector)
        financial_repo = FinancialRepository(self._pool)

        prices = await price_repo.get_range(result.stock_code, start_date, end_date)
        financials = await financial_repo.get_recent(result.stock_code, limit=8)

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

    async def get_sector_comparison(self, stock_code: str, sector: str) -> dict[str, float | None]:
        """동일 섹터 기업들의 재무지표 평균 조회.

        대상 종목의 최신 분기와 동일 분기의 동종업 재무 데이터를 집계.
        대상 종목에 financial_data가 없거나 동종업이 없으면 모든 값이 None.

        Args:
            stock_code: 6자리 KRX 종목 코드
            sector: 섹터 분류명

        Returns:
            sector_per_avg, sector_pbr_avg, sector_roe_avg,
            sector_op_margin_avg (float | None), peer_count (float | None) 딕셔너리
        """
        if not self._pool:
            raise RuntimeError("Pipeline not connected. Call connect() first.")

        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT
                    AVG(f.per)              AS sector_per_avg,
                    AVG(f.pbr)              AS sector_pbr_avg,
                    AVG(f.roe)              AS sector_roe_avg,
                    AVG(f.operating_margin) AS sector_op_margin_avg,
                    COUNT(*)                AS peer_count
                FROM financial_data f
                JOIN stocks s ON f.stock_code = s.stock_code
                WHERE s.sector = $1
                  AND f.stock_code != $2
                  AND f.quarter = (
                      SELECT MAX(quarter) FROM financial_data WHERE stock_code = $2
                  )
                """,
                sector,
                stock_code,
            )

        def _f(v: object) -> float | None:
            return float(v) if v is not None else None  # type: ignore[arg-type]

        if row is None:
            return {
                k: None
                for k in (
                    "sector_per_avg",
                    "sector_pbr_avg",
                    "sector_roe_avg",
                    "sector_op_margin_avg",
                    "peer_count",
                )
            }

        return {
            "sector_per_avg": _f(row["sector_per_avg"]),
            "sector_pbr_avg": _f(row["sector_pbr_avg"]),
            "sector_roe_avg": _f(row["sector_roe_avg"]),
            "sector_op_margin_avg": _f(row["sector_op_margin_avg"]),
            "peer_count": _f(row["peer_count"]),
        }

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
