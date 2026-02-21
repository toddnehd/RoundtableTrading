#!/usr/bin/env python
"""DART API를 통한 재무 데이터 수집 스크립트.

Usage:
    PYTHONPATH=. uv run python scripts/collect_financial_data.py --stock 005930
    PYTHONPATH=. uv run python scripts/collect_financial_data.py --stock 005930 --year 2024 --report 11011
"""

import argparse
import asyncio
from datetime import datetime

from loguru import logger

from src.config import settings
from src.data.collectors.dart_collector import DartCollector
from src.data.collectors.dart_corp_code import DartCorpCodeMapper
from src.data.collectors.dart_errors import DartAPIError, DartNoDataError
from src.data.storage.db_manager import DatabaseManager


async def collect_financial_data(stock_code: str, bsns_year: str, reprt_code: str) -> None:
    """Collect and save financial data for a stock.

    Args:
        stock_code: KRX 6-digit stock code
        bsns_year: Business year (e.g., "2024")
        reprt_code: Report code (11011=Q4, 11012=Q2, 11013=Q1, 11014=Q3)
    """
    if not settings.dart_api_key:
        logger.error("DART_API_KEY가 설정되지 않았습니다. .env 파일을 확인하세요.")
        return

    db = DatabaseManager()
    await db.connect()

    try:
        # corp_code 조회 (DB에 없으면 DART에서 다운로드)
        corp_code = await db.get_corp_code(stock_code)

        if not corp_code:
            logger.info(f"{stock_code} corp_code 없음. DART에서 다운로드 중...")
            mapper = DartCorpCodeMapper()
            await mapper.download_and_parse(settings.dart_api_key)
            corp_code = mapper.get_corp_code(stock_code)

            if not corp_code:
                logger.error(f"{stock_code}의 corp_code를 찾을 수 없습니다.")
                return

            await db.save_corp_code(stock_code, corp_code)
            logger.info(f"corp_code 저장 완료: {stock_code} → {corp_code}")

        # 현재 주가 조회 (PER/PBR 계산용)
        current_price: int | None = None
        if db.pool:
            async with db.pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT close_price FROM daily_prices WHERE stock_code = $1 ORDER BY date DESC LIMIT 1",
                    stock_code,
                )
                if row:
                    current_price = row["close_price"]

        # 재무 데이터 수집
        collector = DartCollector(api_key=settings.dart_api_key)
        logger.info(f"{stock_code} 재무 데이터 수집 중 ({bsns_year}, {reprt_code})...")

        financial_data = await collector.get_financial_data(
            corp_code=corp_code,
            stock_code=stock_code,
            bsns_year=bsns_year,
            reprt_code=reprt_code,
            current_price=current_price,
        )

        if financial_data is None:
            logger.warning(f"{stock_code}: 재무 데이터 없음 (금융업 또는 데이터 미제공)")
            return

        # DB 저장
        await db.save_financial_data([financial_data])
        logger.info(
            f"{stock_code} ({bsns_year}) 재무 데이터 수집 완료: "
            f"매출={financial_data.revenue}, ROE={financial_data.roe}"
        )

    except DartNoDataError as e:
        logger.warning(f"데이터 없음: {e}")
    except DartAPIError as e:
        logger.error(f"DART API 오류: {e}")
    except Exception as e:
        logger.exception(f"수집 실패: {e}")
    finally:
        await db.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="DART API 재무 데이터 수집")
    parser.add_argument("--stock", required=True, help="종목 코드 (예: 005930)")
    parser.add_argument(
        "--year",
        default=str(datetime.now().year - 1),
        help="사업연도 (기본값: 직전연도)",
    )
    parser.add_argument(
        "--report",
        default="11011",
        choices=["11011", "11012", "11013", "11014"],
        help="보고서 종류 (11011=사업보고서, 11012=반기, 11013=1분기, 11014=3분기)",
    )
    args = parser.parse_args()

    asyncio.run(collect_financial_data(args.stock, args.year, args.report))


if __name__ == "__main__":
    main()
