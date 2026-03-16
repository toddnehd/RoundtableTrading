from __future__ import annotations

import asyncpg

from src.data.models import InvestorFlow


class InvestorFlowRepository:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def get_recent(self, stock_code: str, limit: int = 20) -> list[InvestorFlow]:
        async with self._pool.acquire() as conn:
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
        return [_row_to_flow(row) for row in rows]

    async def save(self, flows: list[InvestorFlow]) -> None:
        async with self._pool.acquire() as conn:
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


def _row_to_flow(row: asyncpg.Record) -> InvestorFlow:
    def _int(v: object) -> int | None:
        if v is None:
            return None
        return int(v)  # type: ignore[arg-type, no-any-return, call-overload]

    return InvestorFlow(
        stock_code=row["stock_code"],
        date=row["date"],
        foreign_net=_int(row["foreign_net"]),
        institution_net=_int(row["institution_net"]),
        retail_net=_int(row["retail_net"]),
    )
