from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass
class Stock:
    """종목 기본 정보"""

    stock_code: str
    stock_name: str
    market: str  # 'KOSPI' or 'KOSDAQ'
    sector: Optional[str] = None
    industry: Optional[str] = None


@dataclass
class DailyPrice:
    """일봉 데이터"""

    stock_code: str
    date: date
    open_price: int
    high_price: int
    low_price: int
    close_price: int
    volume: int
    trading_value: Optional[int] = None
    market_cap: Optional[int] = None


@dataclass
class FinancialData:
    """재무 데이터"""

    stock_code: str
    quarter: str  # '2024Q3'
    revenue: Optional[float] = None
    operating_income: Optional[float] = None
    net_income: Optional[float] = None
    per: Optional[float] = None  # 주가수익비율
    pbr: Optional[float] = None  # 주가순자산비율
    roe: Optional[float] = None  # 자기자본이익률
    debt_ratio: Optional[float] = None  # 부채비율
