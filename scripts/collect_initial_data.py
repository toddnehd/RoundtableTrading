import asyncio
from datetime import datetime, timedelta

from loguru import logger

from src.data.collectors.pykrx_collector import PyKrxCollector
from src.data.storage.db_manager import DatabaseManager


async def collect_initial_data():
    """초기 데이터 수집 (3년치)"""
    collector = PyKrxCollector()
    db = DatabaseManager()

    try:
        await db.connect()

        end_date = datetime.now()
        start_date = end_date - timedelta(days=365 * 3)

        start_str = start_date.strftime("%Y%m%d")
        end_str = end_date.strftime("%Y%m%d")

        logger.info(f"Collecting data from {start_str} to {end_str}")

        for market in ["KOSPI", "KOSDAQ"]:
            logger.info(f"Processing {market} market")

            stocks = collector.get_stock_list(market)
            if not stocks:
                logger.warning(f"No stocks found for {market}")
                continue

            await db.save_stocks(stocks)
            logger.info(f"Saved {len(stocks)} {market} stocks")

            for i, stock in enumerate(stocks, 1):
                logger.info(
                    f"Collecting data for {stock.stock_name} ({stock.stock_code}) "
                    f"[{i}/{len(stocks)}]"
                )

                prices = collector.get_ohlcv(stock.stock_code, start_str, end_str)

                if not prices:
                    logger.warning(f"No price data for {stock.stock_code}")
                    continue

                is_valid, issues = collector.validate_data(prices)
                if not is_valid:
                    logger.warning(f"Data validation issues for {stock.stock_code}: {issues}")

                await db.save_daily_prices(prices)

                await asyncio.sleep(0.1)

        logger.info("Initial data collection completed")

    except Exception as e:
        logger.error(f"Failed to collect initial data: {e}")
        raise

    finally:
        await db.close()


if __name__ == "__main__":
    asyncio.run(collect_initial_data())
