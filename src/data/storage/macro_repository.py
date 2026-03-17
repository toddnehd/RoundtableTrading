from __future__ import annotations

from datetime import date

import asyncpg

from src.data.models import MacroSnapshot


class MacroRepository:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def get_latest(self, target_date: date) -> MacroSnapshot | None:
        async with self._pool.acquire() as conn:
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
        return _row_to_macro(row)

    async def save(self, snapshots: list[MacroSnapshot]) -> None:
        async with self._pool.acquire() as conn:
            await conn.executemany(
                """
                INSERT INTO macro_indicators
                    (date, base_rate, usd_krw, cpi_yoy, kospi, kosdaq, export_yoy)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (date) DO UPDATE
                SET base_rate  = COALESCE(EXCLUDED.base_rate,  macro_indicators.base_rate),
                    usd_krw    = COALESCE(EXCLUDED.usd_krw,    macro_indicators.usd_krw),
                    cpi_yoy    = COALESCE(EXCLUDED.cpi_yoy,    macro_indicators.cpi_yoy),
                    kospi      = COALESCE(EXCLUDED.kospi,      macro_indicators.kospi),
                    kosdaq     = COALESCE(EXCLUDED.kosdaq,     macro_indicators.kosdaq),
                    export_yoy = COALESCE(EXCLUDED.export_yoy, macro_indicators.export_yoy)
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

    async def save_market_indices(self, data: list[tuple[date, float, float]]) -> None:
        async with self._pool.acquire() as conn:
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


def _row_to_macro(row: asyncpg.Record) -> MacroSnapshot:
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
