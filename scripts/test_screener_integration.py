#!/usr/bin/env python
"""Integration test for stock screener.

Usage:
    uv run python -m scripts.test_screener_integration
"""

import asyncio

from loguru import logger

from src.screener import RuleBasedScreener, ScreeningCriteria


async def main():
    logger.info("=== Stock Screener Integration Test ===")

    screener = RuleBasedScreener()
    await screener.connect()

    try:
        criteria = ScreeningCriteria(
            min_volume=50_000,
            min_volume_surge_ratio=1.3,
            min_price=1_000,
            markets=["KOSPI", "KOSDAQ"],
            lookback_days=20,
        )

        logger.info(
            f"Screening with criteria: min_volume={criteria.min_volume}, "
            f"min_surge_ratio={criteria.min_volume_surge_ratio}"
        )

        results = await screener.screen(criteria, limit=10)

        logger.info(f"Found {len(results)} stocks matching criteria")
        print("\n" + "=" * 80)
        print(f"{'Code':<10} {'Name':<20} {'Market':<8} {'Score':>8} {'Reasons'}")
        print("=" * 80)

        for result in results:
            reasons_str = ", ".join(r.value for r in result.reasons)
            print(
                f"{result.stock_code:<10} {result.stock_name:<20} "
                f"{result.market:<8} {result.score:>8.2f} {reasons_str}"
            )

            if result.latest_price:
                price = result.latest_price
                print(f"           Close: {price.close_price:,} | Volume: {price.volume:,}")

            if result.metrics:
                vol_ratio = result.metrics.get("volume_ratio", 0)
                change_5d = result.metrics.get("price_change_5d_pct", 0)
                print(f"           Vol Ratio: {vol_ratio:.2f}x | 5D Change: {change_5d:+.2f}%")
            print("-" * 80)

        print("\n=== Screening Complete ===")

    finally:
        await screener.close()


if __name__ == "__main__":
    asyncio.run(main())
