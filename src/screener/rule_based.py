"""Rule-based stock screener implementation.

Screens stocks using SQL queries and pandas calculations.
No LLM required - pure algorithmic filtering.
"""

from datetime import date, timedelta

import asyncpg
from loguru import logger

from src.config import settings
from src.data.models import DailyPrice
from src.screener.models import (
    ScreeningCriteria,
    ScreeningReason,
    ScreeningResult,
)


class RuleBasedScreener:
    """Rule-based stock screener using SQL and pandas.

    Implements ScreenerProtocol for filtering stocks based on
    technical and volume criteria directly from database.
    """

    def __init__(self, pool: asyncpg.Pool | None = None):
        self._pool = pool
        self._own_pool = False

    async def connect(self) -> None:
        """Create connection pool if not provided."""
        if self._pool is None:
            self._pool = await asyncpg.create_pool(settings.database_url)
            self._own_pool = True
            logger.info("Screener database pool created")

    async def close(self) -> None:
        """Close connection pool if owned."""
        if self._own_pool and self._pool:
            await self._pool.close()
            logger.info("Screener database pool closed")

    async def screen(
        self,
        criteria: ScreeningCriteria,
        limit: int = 20,
    ) -> list[ScreeningResult]:
        """Screen stocks based on criteria.

        Args:
            criteria: Screening criteria to apply.
            limit: Maximum number of results to return.

        Returns:
            List of ScreeningResult sorted by score (descending).
        """
        if not self._pool:
            raise RuntimeError("Screener not connected. Call connect() first.")

        end_date = date.today()
        start_date = end_date - timedelta(days=criteria.lookback_days + 10)

        async with self._pool.acquire() as conn:
            candidates = await self._get_candidates(conn, criteria, start_date, end_date)

            if not candidates:
                logger.warning("No candidates found matching criteria")
                return []

            results = await self._calculate_metrics(
                conn, candidates, criteria, start_date, end_date
            )

            results.sort(key=lambda x: x.score, reverse=True)
            return results[:limit]

    async def _get_candidates(
        self,
        conn: asyncpg.Connection,
        criteria: ScreeningCriteria,
        start_date: date,
        end_date: date,
    ) -> list[dict]:
        """Get candidate stocks matching basic criteria."""
        markets_clause = ", ".join(f"'{m}'" for m in criteria.markets)

        query = f"""
            WITH recent_prices AS (
                SELECT
                    dp.stock_code,
                    s.stock_name,
                    s.market,
                    s.sector,
                    dp.date,
                    dp.close_price,
                    dp.volume,
                    dp.market_cap,
                    ROW_NUMBER() OVER (
                        PARTITION BY dp.stock_code ORDER BY dp.date DESC
                    ) as rn
                FROM daily_prices dp
                JOIN stocks s ON dp.stock_code = s.stock_code
                WHERE s.market IN ({markets_clause})
                    AND s.is_active = true
                    AND dp.date BETWEEN $1 AND $2
                    AND dp.close_price >= $3
                    {"AND dp.close_price <= $4" if criteria.max_price else ""}
            ),
            latest AS (
                SELECT * FROM recent_prices WHERE rn = 1
            ),
            avg_volume AS (
                SELECT
                    stock_code,
                    AVG(volume) as avg_vol_20d
                FROM recent_prices
                WHERE rn <= 20
                GROUP BY stock_code
            )
            SELECT
                l.stock_code,
                l.stock_name,
                l.market,
                l.sector,
                l.close_price,
                l.volume as latest_volume,
                l.market_cap,
                av.avg_vol_20d,
                CASE
                    WHEN av.avg_vol_20d > 0
                    THEN l.volume::float / av.avg_vol_20d
                    ELSE 0
                END as volume_surge_ratio
            FROM latest l
            JOIN avg_volume av ON l.stock_code = av.stock_code
            WHERE av.avg_vol_20d >= $5
            ORDER BY volume_surge_ratio DESC
            LIMIT 500
        """

        params = [start_date, end_date, criteria.min_price, criteria.min_volume]
        if criteria.max_price:
            params.insert(3, criteria.max_price)

        rows = await conn.fetch(query, *params)
        return [dict(row) for row in rows]

    async def _calculate_metrics(
        self,
        conn: asyncpg.Connection,
        candidates: list[dict],
        criteria: ScreeningCriteria,
        start_date: date,
        end_date: date,
    ) -> list[ScreeningResult]:
        """Calculate detailed metrics for candidates."""
        results = []
        stock_codes = [c["stock_code"] for c in candidates]

        price_data = await self._fetch_price_history(conn, stock_codes, start_date, end_date)

        for candidate in candidates:
            stock_code = candidate["stock_code"]
            prices = price_data.get(stock_code, [])

            if len(prices) < 5:
                continue

            metrics = self._compute_technical_metrics(prices)
            reasons = self._determine_screening_reasons(candidate, metrics, criteria)

            if not reasons:
                continue

            score = self._calculate_score(candidate, metrics, reasons)

            latest_price = prices[0] if prices else None

            results.append(
                ScreeningResult(
                    stock_code=stock_code,
                    stock_name=candidate["stock_name"],
                    market=candidate["market"],
                    reasons=reasons,
                    score=score,
                    metrics=metrics,
                    latest_price=latest_price,
                )
            )

        return results

    async def _fetch_price_history(
        self,
        conn: asyncpg.Connection,
        stock_codes: list[str],
        start_date: date,
        end_date: date,
    ) -> dict[str, list[DailyPrice]]:
        """Fetch price history for multiple stocks."""
        query = """
            SELECT
                stock_code, date, open_price, high_price, low_price,
                close_price, volume, trading_value, market_cap
            FROM daily_prices
            WHERE stock_code = ANY($1)
                AND date BETWEEN $2 AND $3
            ORDER BY stock_code, date DESC
        """

        rows = await conn.fetch(query, stock_codes, start_date, end_date)

        result: dict[str, list[DailyPrice]] = {}
        for row in rows:
            code = row["stock_code"]
            if code not in result:
                result[code] = []
            result[code].append(
                DailyPrice(
                    stock_code=code,
                    date=row["date"],
                    open_price=row["open_price"],
                    high_price=row["high_price"],
                    low_price=row["low_price"],
                    close_price=row["close_price"],
                    volume=row["volume"],
                    trading_value=row["trading_value"],
                    market_cap=row["market_cap"],
                )
            )

        return result

    def _compute_technical_metrics(self, prices: list[DailyPrice]) -> dict[str, float]:
        """Compute technical metrics from price data."""
        closes = [p.close_price for p in prices]
        volumes = [p.volume for p in prices]
        highs = [p.high_price for p in prices]
        lows = [p.low_price for p in prices]

        metrics: dict[str, float] = {}

        # Price change
        if len(closes) >= 2:
            metrics["price_change_1d_pct"] = (
                (closes[0] - closes[1]) / closes[1] * 100 if closes[1] else 0
            )

        if len(closes) >= 5:
            metrics["price_change_5d_pct"] = (
                (closes[0] - closes[4]) / closes[4] * 100 if closes[4] else 0
            )

        if len(closes) >= 20:
            metrics["price_change_20d_pct"] = (
                (closes[0] - closes[19]) / closes[19] * 100 if closes[19] else 0
            )

        # Moving averages
        if len(closes) >= 5:
            metrics["ma5"] = sum(closes[:5]) / 5

        if len(closes) >= 20:
            metrics["ma20"] = sum(closes[:20]) / 20

        # Volume metrics
        if len(volumes) >= 20:
            avg_vol = (
                sum(volumes[1:21]) / 20
                if len(volumes) > 20
                else sum(volumes[1:]) / (len(volumes) - 1)
            )
            metrics["volume_ratio"] = volumes[0] / avg_vol if avg_vol > 0 else 0

        # Volatility (ATR-like)
        if len(prices) >= 14:
            true_ranges = []
            for i in range(min(14, len(prices) - 1)):
                tr = max(
                    highs[i] - lows[i],
                    abs(highs[i] - closes[i + 1]),
                    abs(lows[i] - closes[i + 1]),
                )
                true_ranges.append(tr)
            metrics["atr_14"] = sum(true_ranges) / len(true_ranges)
            metrics["atr_pct"] = metrics["atr_14"] / closes[0] * 100 if closes[0] else 0

        # 52-week high/low proximity
        if len(closes) >= 60:
            high_60d = max(highs[:60])
            low_60d = min(lows[:60])
            metrics["high_60d"] = high_60d
            metrics["low_60d"] = low_60d
            metrics["pct_from_high"] = (closes[0] - high_60d) / high_60d * 100
            metrics["pct_from_low"] = (closes[0] - low_60d) / low_60d * 100

        return metrics

    def _determine_screening_reasons(
        self,
        candidate: dict,
        metrics: dict[str, float],
        criteria: ScreeningCriteria,
    ) -> list[ScreeningReason]:
        """Determine why this stock was selected."""
        reasons = []

        volume_ratio = candidate.get("volume_surge_ratio", 0)
        if volume_ratio >= criteria.min_volume_surge_ratio:
            reasons.append(ScreeningReason.VOLUME_SURGE)

        price_change_5d = metrics.get("price_change_5d_pct", 0)
        if price_change_5d >= 10:
            reasons.append(ScreeningReason.MOMENTUM)

        pct_from_high = metrics.get("pct_from_high", -100)
        if pct_from_high >= -3:
            reasons.append(ScreeningReason.NEW_HIGH)

        pct_from_low = metrics.get("pct_from_low", 100)
        if pct_from_low <= 5:
            reasons.append(ScreeningReason.OVERSOLD)

        ma5 = metrics.get("ma5", 0)
        ma20 = metrics.get("ma20", 0)
        if ma5 > ma20 > 0:
            reasons.append(ScreeningReason.GOLDEN_CROSS)
        elif ma20 > ma5 > 0:
            reasons.append(ScreeningReason.DEATH_CROSS)

        atr_pct = metrics.get("atr_pct", 0)
        if atr_pct >= 5:
            reasons.append(ScreeningReason.VOLATILITY)

        return reasons

    def _calculate_score(
        self,
        candidate: dict,
        metrics: dict[str, float],
        reasons: list[ScreeningReason],
    ) -> float:
        """Calculate overall screening score."""
        score = 0.0

        # Volume surge contribution (0-30 points)
        volume_ratio = candidate.get("volume_surge_ratio", 0)
        score += min(volume_ratio * 10, 30)

        # Momentum contribution (0-25 points)
        price_change_5d = metrics.get("price_change_5d_pct", 0)
        if price_change_5d > 0:
            score += min(price_change_5d * 2.5, 25)

        # Near high contribution (0-20 points)
        pct_from_high = metrics.get("pct_from_high", -100)
        if pct_from_high >= -10:
            score += 20 + pct_from_high

        # Reason count contribution (5 points each, max 25)
        score += min(len(reasons) * 5, 25)

        return float(round(score, 2))


async def screen_stocks(
    criteria: ScreeningCriteria | None = None,
    limit: int = 20,
) -> list[ScreeningResult]:
    """Convenience function to screen stocks.

    Args:
        criteria: Screening criteria (uses defaults if None).
        limit: Maximum results to return.

    Returns:
        List of screening results.
    """
    if criteria is None:
        criteria = ScreeningCriteria()

    screener = RuleBasedScreener()
    try:
        await screener.connect()
        return await screener.screen(criteria, limit)
    finally:
        await screener.close()
