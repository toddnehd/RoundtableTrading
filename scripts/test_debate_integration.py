#!/usr/bin/env python
"""Integration test for DebateEngine with real LLM.

Usage:
    # Test with sample data (no DB needed)
    uv run python scripts/test_debate_integration.py

    # Test with real DB data
    uv run python scripts/test_debate_integration.py --stock 005930

    # Choose LLM provider
    uv run python scripts/test_debate_integration.py --provider ollama
    uv run python scripts/test_debate_integration.py --provider openai
"""

import argparse
import asyncio
from datetime import date, timedelta

from loguru import logger

from src.agents.base import AnalysisData
from src.agents.llm import get_llm_client
from src.data.models import DailyPrice
from src.debate import DebateEngine, DebateResult


def create_sample_data() -> AnalysisData:
    base_date = date(2026, 1, 1)
    base_price = 72_000
    prices = []

    for i in range(60):
        trend = i * 80 if i < 40 else (60 - i) * 120
        noise = (i % 7 - 3) * 150
        close = base_price + trend + noise
        prices.append(
            DailyPrice(
                stock_code="005930",
                date=base_date + timedelta(days=i),
                open_price=close - 300,
                high_price=close + 500,
                low_price=close - 600,
                close_price=close,
                volume=12_000_000 + (i % 5) * 2_000_000,
            )
        )

    return AnalysisData(
        stock_code="005930",
        stock_name="삼성전자",
        prices=prices,
    )


async def load_data_from_db(stock_code: str) -> AnalysisData | None:
    try:
        from src.data.storage.db_manager import DatabaseManager

        db = DatabaseManager()
        await db.connect()

        if not db.pool:
            return None

        try:
            async with db.pool.acquire() as conn:
                stock = await conn.fetchrow(
                    "SELECT stock_code, stock_name FROM stocks WHERE stock_code = $1",
                    stock_code,
                )
                if not stock:
                    logger.error(f"종목 {stock_code} 없음")
                    return None

                rows = await conn.fetch(
                    """
                    SELECT stock_code, date, open_price, high_price, low_price,
                           close_price, volume, market_cap
                    FROM daily_prices
                    WHERE stock_code = $1
                    ORDER BY date DESC
                    LIMIT 60
                    """,
                    stock_code,
                )

                if not rows:
                    logger.error(f"{stock_code} 가격 데이터 없음")
                    return None

                prices = [
                    DailyPrice(
                        stock_code=row["stock_code"],
                        date=row["date"],
                        open_price=row["open_price"],
                        high_price=row["high_price"],
                        low_price=row["low_price"],
                        close_price=row["close_price"],
                        volume=row["volume"],
                        market_cap=row["market_cap"],
                    )
                    for row in reversed(rows)
                ]

                return AnalysisData(
                    stock_code=stock["stock_code"],
                    stock_name=stock["stock_name"],
                    prices=prices,
                )
        finally:
            await db.close()

    except Exception as e:
        logger.warning(f"DB 로드 실패: {e}")
        return None


def print_debate_result(result: DebateResult) -> None:
    print("\n" + "=" * 60)
    print(f"  토론 결과: {result.stock_name} ({result.stock_code})")
    print("=" * 60)
    print(f"  최종 의견  : {result.final_opinion.value}")
    print(f"  확신도     : {result.confidence}")
    print(f"  합의 수준  : {result.consensus_level.value}")
    print("-" * 60)

    print("  [개별 에이전트 의견]")
    for op in result.individual_opinions:
        bar = "█" * (op.confidence // 10) + "░" * (10 - op.confidence // 10)
        print(f"  {op.agent_name:<10} {op.opinion.value:<4}  {bar}  {op.confidence}점")
        for reason in op.reasoning[:2]:
            print(f"               → {reason}")

    if result.moderator_opinion:
        mod = result.moderator_opinion
        print("-" * 60)
        print(f"  [사회자 종합]  {mod.opinion.value}  (확신도: {mod.confidence})")
        for reason in mod.reasoning[:3]:
            print(f"    • {reason}")

    print("-" * 60)
    print("  [핵심 근거]")
    for reason in result.reasoning:
        print(f"    • {reason}")
    print("=" * 60)


async def run_test(provider: str, stock_code: str | None) -> None:
    logger.info(f"=== DebateEngine 통합 테스트 (provider: {provider}) ===")

    if stock_code:
        logger.info(f"{stock_code} DB 데이터 로드 중...")
        data = await load_data_from_db(stock_code)
        if not data:
            logger.warning("샘플 데이터로 대체합니다")
            data = create_sample_data()
    else:
        logger.info("샘플 데이터 사용 (삼성전자)")
        data = create_sample_data()

    logger.info(f"분석 대상: {data.stock_name} ({data.stock_code}), {len(data.prices)}일 데이터")

    try:
        llm_client = get_llm_client(provider)
        logger.info(f"LLM 모델: {llm_client.get_model()}")
    except ValueError as e:
        logger.error(f"LLM 클라이언트 생성 실패: {e}")
        return

    engine = DebateEngine(llm_client)

    logger.info("토론 시작 (4개 에이전트 병렬 분석 중)...")
    try:
        result = await engine.debate(data)
        print_debate_result(result)

    except Exception as e:
        logger.exception(f"토론 실패: {e}")


def main():
    parser = argparse.ArgumentParser(description="DebateEngine 통합 테스트")
    parser.add_argument(
        "--provider",
        choices=["anthropic", "openai", "ollama"],
        default="anthropic",
        help="LLM provider",
    )
    parser.add_argument(
        "--stock",
        type=str,
        help="종목 코드 (DB에서 로드)",
    )
    args = parser.parse_args()

    asyncio.run(run_test(args.provider, args.stock))


if __name__ == "__main__":
    main()
