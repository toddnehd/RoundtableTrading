from __future__ import annotations

import asyncpg

from src.data.models import FinancialData


class FinancialRepository:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def get_recent(self, stock_code: str, limit: int = 8) -> list[FinancialData]:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT stock_code, quarter, revenue, operating_income, net_income,
                       per, pbr, roe, debt_ratio, eps, bps, fs_div
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
    )
