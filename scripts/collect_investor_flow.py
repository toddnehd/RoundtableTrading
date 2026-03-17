#!/usr/bin/env python
"""투자자별 수급 배치 수집 스크립트.

Usage:
    PYTHONPATH=. uv run python scripts/collect_investor_flow.py --stock 005930 --start 2024-01-01
    PYTHONPATH=. uv run python scripts/collect_investor_flow.py --help
"""

import argparse
import asyncio
from datetime import datetime

from loguru import logger

from src.data.collectors.kis_collector import KisCollector
from src.data.storage.db_manager import DatabaseManager
from src.data.storage.investor_flow_repository import InvestorFlowRepository


async def collect_investor_flow(stock_code: str, start: str, end: str) -> None:
    start_ymd = datetime.strptime(start, "%Y-%m-%d").date().strftime("%Y%m%d")
    end_ymd = datetime.strptime(end, "%Y-%m-%d").date().strftime("%Y%m%d")

    db = DatabaseManager()
    await db.connect()
    if db.pool is None:
        raise RuntimeError("Database not connected")

    try:
        investor_repo = InvestorFlowRepository(db.pool)
        kis = KisCollector()

        flows = await kis.get_investor_trading(stock_code, start_ymd, end_ymd)
        if flows:
            await investor_repo.save(flows)
            logger.info(f"{stock_code}: {len(flows)}건 수급 저장 완료")
        else:
            logger.warning(f"{stock_code}: 수급 데이터 없음")

    except Exception as e:
        logger.exception(f"수집 실패: {e}")
        raise
    finally:
        await db.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="투자자별 수급 배치 수집")
    parser.add_argument("--stock", required=True, help="종목 코드 (예: 005930)")
    parser.add_argument("--start", required=True, help="시작일 (YYYY-MM-DD)")
    parser.add_argument(
        "--end",
        default=None,
        help="종료일 (YYYY-MM-DD, 기본값: 오늘)",
    )
    args = parser.parse_args()
    end = args.end or datetime.now().strftime("%Y-%m-%d")
    asyncio.run(collect_investor_flow(args.stock, args.start, end))


if __name__ == "__main__":
    main()
