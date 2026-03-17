from __future__ import annotations

import asyncpg
from loguru import logger

from src.data.models import FinancialData


class FinancialRepository:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def save(self, financials: list[FinancialData]) -> None:
        async with self._pool.acquire() as conn:
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

    async def get_recent(self, stock_code: str, limit: int = 8) -> list[FinancialData]:
        async with self._pool.acquire() as conn:
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
        return [_row_to_financial(row) for row in rows]


def _row_to_financial(row: asyncpg.Record) -> FinancialData:
    def _float(v: object) -> float | None:
        if v is None:
            return None
        return float(v)  # type: ignore[arg-type]

    return FinancialData(
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
