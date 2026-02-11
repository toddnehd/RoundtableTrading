#!/usr/bin/env python
"""Integration test script for TechnicalAnalysisAgent with real LLM.

Usage:
    # Test with Anthropic (default)
    uv run python scripts/test_agent_integration.py

    # Test with OpenAI
    uv run python scripts/test_agent_integration.py --provider openai

    # Test with specific stock from DB
    uv run python scripts/test_agent_integration.py --stock 005930
"""

import argparse
import asyncio
from datetime import date, timedelta

from loguru import logger

from src.agents.base import AnalysisData
from src.agents.llm import get_llm_client
from src.agents.technical import TechnicalAnalysisAgent
from src.data.models import DailyPrice


def create_sample_data() -> AnalysisData:
    """Create sample price data for testing."""
    base_date = date(2026, 1, 15)
    base_price = 72000

    prices = []
    for i in range(60):
        trend = i * 50 if i < 30 else (60 - i) * 50
        volatility = (i % 7 - 3) * 100
        close = base_price + trend + volatility

        prices.append(
            DailyPrice(
                stock_code="005930",
                date=base_date + timedelta(days=i),
                open_price=close - 200,
                high_price=close + 300,
                low_price=close - 400,
                close_price=close,
                volume=10000000 + (i % 5) * 1000000,
            )
        )

    return AnalysisData(
        stock_code="005930",
        stock_name="삼성전자",
        prices=prices,
    )


async def load_data_from_db(stock_code: str) -> AnalysisData | None:
    """Load real data from database."""
    try:
        from src.data.storage.db_manager import DatabaseManager

        db = DatabaseManager()
        await db.connect()

        if not db.pool:
            logger.error("Database pool not initialized")
            return None

        try:
            async with db.pool.acquire() as conn:
                stock = await conn.fetchrow(
                    "SELECT stock_code, stock_name FROM stocks WHERE stock_code = $1",
                    stock_code,
                )

                if not stock:
                    logger.error(f"Stock {stock_code} not found in database")
                    return None

                rows = await conn.fetch(
                    """
                    SELECT stock_code, date, open_price, high_price, low_price,
                           close_price, volume
                    FROM daily_prices
                    WHERE stock_code = $1
                    ORDER BY date DESC
                    LIMIT 60
                    """,
                    stock_code,
                )

                if not rows:
                    logger.error(f"No price data for {stock_code}")
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
        logger.warning(f"Failed to load from DB: {e}")
        return None


async def run_test(provider: str, stock_code: str | None) -> None:
    """Run integration test with specified provider."""
    logger.info("=== TechnicalAnalysisAgent Integration Test ===")
    logger.info(f"Provider: {provider}")

    if stock_code:
        logger.info(f"Loading data for {stock_code} from database...")
        data = await load_data_from_db(stock_code)
        if not data:
            logger.warning("Falling back to sample data")
            data = create_sample_data()
    else:
        logger.info("Using sample data (삼성전자)")
        data = create_sample_data()

    logger.info(f"Stock: {data.stock_name} ({data.stock_code})")
    logger.info(f"Price data: {len(data.prices)} days")
    logger.info(f"Latest price: {data.prices[-1].close_price:,}원")

    try:
        llm_client = get_llm_client(provider)
        logger.info(f"LLM model: {llm_client.get_model()}")
    except ValueError as e:
        logger.error(f"Failed to create LLM client: {e}")
        return

    agent = TechnicalAnalysisAgent(llm_client=llm_client)

    logger.info("Running analysis...")
    try:
        result = await agent.analyze(data)

        logger.info("=" * 50)
        logger.info("Analysis Result")
        logger.info("=" * 50)
        logger.info(f"Agent: {result.agent_name}")
        logger.info(f"Opinion: {result.opinion.value}")
        logger.info(f"Confidence: {result.confidence}")
        logger.info(f"Model: {result.model}")
        logger.info("Reasoning:")
        for i, reason in enumerate(result.reasoning, 1):
            logger.info(f"  {i}. {reason}")
        logger.info("=" * 50)

        if result.raw_response:
            logger.debug(f"Raw response:\n{result.raw_response}")

    except Exception as e:
        logger.exception(f"Analysis failed: {e}")


def main():
    parser = argparse.ArgumentParser(description="Test TechnicalAnalysisAgent")
    parser.add_argument(
        "--provider",
        choices=["anthropic", "openai", "ollama"],
        default="anthropic",
        help="LLM provider to use",
    )
    parser.add_argument(
        "--stock",
        type=str,
        help="Stock code to analyze (loads from DB)",
    )
    args = parser.parse_args()

    asyncio.run(run_test(args.provider, args.stock))


if __name__ == "__main__":
    main()
