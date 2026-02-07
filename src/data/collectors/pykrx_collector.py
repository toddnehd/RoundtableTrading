from typing import cast

import FinanceDataReader  # type: ignore[import-untyped]
import pandas as pd
from loguru import logger
from pykrx import stock  # type: ignore[import-untyped]

from src.data.models import DailyPrice, Stock


class PyKrxCollector:
    """pykrx + FinanceDataReader를 이용한 한국 주식 데이터 수집

    Note:
        2026년 1월 KRX 정책 변경으로 pykrx의 get_market_ticker_list가 더 이상 작동하지 않음.
        종목 리스트는 FinanceDataReader를 사용하고, OHLCV 데이터는 pykrx를 사용합니다.
    """

    def get_stock_list(self, market: str = "KOSPI") -> list[Stock]:
        """종목 리스트 조회 (FinanceDataReader 사용)

        Args:
            market: 'KOSPI' 또는 'KOSDAQ'

        Returns:
            Stock 객체 리스트
        """
        try:
            df = FinanceDataReader.StockListing(market)

            stocks = []
            for _, row in df.iterrows():
                stocks.append(
                    Stock(
                        stock_code=row["Code"],
                        stock_name=row["Name"],
                        market=market,
                    )
                )

            logger.info(f"Retrieved {len(stocks)} stocks from {market}")
            return stocks

        except Exception as e:
            logger.error(f"Failed to get stock list from {market}: {e}")
            return []

    def get_ohlcv(self, stock_code: str, start_date: str, end_date: str) -> list[DailyPrice]:
        """일봉 데이터 조회

        Args:
            stock_code: 종목 코드
            start_date: 시작일 (YYYYMMDD)
            end_date: 종료일 (YYYYMMDD)

        Returns:
            DailyPrice 객체 리스트
        """
        try:
            df = stock.get_market_ohlcv_by_date(start_date, end_date, stock_code)

            if df.empty:
                logger.warning(f"No data for {stock_code}")
                return []

            prices = []
            for date_idx, row in df.iterrows():
                # date_idx is pd.Timestamp from DatetimeIndex
                date_val = cast(pd.Timestamp, date_idx).date()
                prices.append(
                    DailyPrice(
                        stock_code=stock_code,
                        date=date_val,
                        open_price=int(row["시가"]),
                        high_price=int(row["고가"]),
                        low_price=int(row["저가"]),
                        close_price=int(row["종가"]),
                        volume=int(row["거래량"]),
                    )
                )

            logger.info(f"Retrieved {len(prices)} days of data for {stock_code}")
            return prices

        except Exception as e:
            logger.error(f"Failed to get OHLCV for {stock_code}: {e}")
            return []

    def validate_data(self, prices: list[DailyPrice]) -> tuple[bool, list[str]]:
        """데이터 유효성 검증

        Args:
            prices: 검증할 DailyPrice 리스트

        Returns:
            (is_valid, issues) 튜플
        """
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
