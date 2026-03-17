#!/usr/bin/env python
"""거시경제 데이터 배치 수집 스크립트.

Usage:
    PYTHONPATH=. uv run python scripts/collect_macro_data.py --start 2024-01-01 --end 2026-03-17
    PYTHONPATH=. uv run python scripts/collect_macro_data.py --help
"""

import argparse
import asyncio
from datetime import datetime

from loguru import logger

from src.config import settings
from src.data.collectors.ecos_collector import EcosCollector
from src.data.collectors.kis_collector import KisCollector
from src.data.models import MacroSnapshot
from src.data.storage.db_manager import DatabaseManager
from src.data.storage.macro_repository import MacroRepository


async def collect_macro(start: str, end: str) -> None:
    start_dt = datetime.strptime(start, "%Y-%m-%d").date()
    end_dt = datetime.strptime(end, "%Y-%m-%d").date()
    start_ymd = start_dt.strftime("%Y%m%d")
    end_ymd = end_dt.strftime("%Y%m%d")

    db = DatabaseManager()
    await db.connect()
    if db.pool is None:
        raise RuntimeError("Database not connected")

    try:
        macro_repo = MacroRepository(db.pool)

        ecos = EcosCollector(settings.ecos_api_key)
        base_rates, usd_krws, cpis = await asyncio.gather(
            ecos.get_base_rate(start_ymd, end_ymd),
            ecos.get_usd_krw(start_ymd, end_ymd),
            ecos.get_cpi(start_ymd, end_ymd),
        )

        date_set = {d for d, _ in base_rates} | {d for d, _ in usd_krws} | {d for d, _ in cpis}
        br_map = dict(base_rates)
        fx_map = dict(usd_krws)
        cpi_map = dict(cpis)

        snapshots = [
            MacroSnapshot(
                date=d,
                base_rate=br_map.get(d),
                usd_krw=fx_map.get(d),
                cpi_yoy=cpi_map.get(d),
            )
            for d in sorted(date_set)
        ]

        if snapshots:
            await macro_repo.save(snapshots)
            logger.info(f"ECOS: {len(snapshots)}건 저장 완료")
        else:
            logger.warning("ECOS: 수집된 데이터 없음")

        kis = KisCollector()
        indices = await kis.get_market_index(start_ymd, end_ymd)
        if indices:
            await macro_repo.save_market_indices(indices)
            logger.info(f"KIS 지수: {len(indices)}건 저장 완료")
        else:
            logger.warning("KIS: 지수 데이터 없음")

    except Exception as e:
        logger.exception(f"수집 실패: {e}")
        raise
    finally:
        await db.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="거시경제 데이터 배치 수집")
    parser.add_argument("--start", required=True, help="시작일 (YYYY-MM-DD)")
    parser.add_argument("--end", default=None, help="종료일 (YYYY-MM-DD, 기본값: 오늘)")
    args = parser.parse_args()
    end = args.end or datetime.now().strftime("%Y-%m-%d")
    asyncio.run(collect_macro(args.start, end))


if __name__ == "__main__":
    main()
