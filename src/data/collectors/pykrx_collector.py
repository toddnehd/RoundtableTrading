from typing import cast

import FinanceDataReader  # type: ignore[import-untyped]
import pandas as pd
from loguru import logger
from pykrx import stock  # type: ignore[import-untyped]

from src.data.models import DailyPrice, Stock


class PyKrxCollector:
    """pykrx + FinanceDataReader를 이용한 한국 주식 OHLCV 및 종목 리스트 수집.

    투자자별 수급·지수 데이터는 KisCollector를 사용.
    """

    def get_stock_list(self, market: str = "KOSPI") -> list[Stock]:
        try:
            df = FinanceDataReader.StockListing(market)
            stocks = [
                Stock(
                    stock_code=str(row["Code"]),
                    stock_name=str(row["Name"]),
                    market=market,
                )
                for _, row in df.iterrows()
            ]
            logger.info(f"Retrieved {len(stocks)} stocks from {market}")
            return stocks
        except Exception as e:
            logger.error(f"Failed to get stock list from {market}: {e}")
            return []

    def get_ohlcv(self, stock_code: str, start_date: str, end_date: str) -> list[DailyPrice]:
        try:
            df = stock.get_market_ohlcv_by_date(start_date, end_date, stock_code)
            if df.empty:
                logger.warning(f"No OHLCV data for {stock_code}")
                return []

            prices = [
                DailyPrice(
                    stock_code=stock_code,
                    date=cast(pd.Timestamp, date_idx).date(),
                    open_price=int(row["시가"]),
                    high_price=int(row["고가"]),
                    low_price=int(row["저가"]),
                    close_price=int(row["종가"]),
                    volume=int(row["거래량"]),
                )
                for date_idx, row in df.iterrows()
            ]
            logger.info(f"Retrieved {len(prices)} days of OHLCV for {stock_code}")
            return prices
        except Exception as e:
            logger.error(f"Failed to get OHLCV for {stock_code}: {e}")
            return []

    def validate_data(self, prices: list[DailyPrice]) -> tuple[bool, list[str]]:
        issues = []

        if not prices:
            issues.append("데이터 없음")
            return False, issues

        for i in range(1, len(prices)):
            prev_close = prices[i - 1].close_price
            curr_close = prices[i].close_price
            change_pct = abs((curr_close - prev_close) / prev_close)
            if change_pct > 0.3:
                issues.append(f"가격 급변 감지: {prices[i].date} ({change_pct:.1%})")

        zero_volume_dates = [p.date for p in prices if p.volume == 0]
        if zero_volume_dates:
            issues.append(f"거래량 0: {len(zero_volume_dates)}일")

        for price in prices:
            if not (price.low_price <= price.open_price <= price.high_price):
                issues.append(f"가격 범위 오류: {price.date} 시가")
            if not (price.low_price <= price.close_price <= price.high_price):
                issues.append(f"가격 범위 오류: {price.date} 종가")

        return len(issues) == 0, issues
