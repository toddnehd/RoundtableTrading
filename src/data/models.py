from dataclasses import dataclass
from datetime import date


@dataclass
class Stock:
    """종목 기본 정보"""

    stock_code: str
    stock_name: str
    market: str  # 'KOSPI' or 'KOSDAQ'
    sector: str | None = None
    industry: str | None = None


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
    trading_value: int | None = None
    market_cap: int | None = None


@dataclass
class FinancialData:
    """재무 데이터"""

    stock_code: str
    quarter: str  # '2024Q3'
    revenue: float | None = None
    operating_income: float | None = None
    net_income: float | None = None
    per: float | None = None  # 주가수익비율
    pbr: float | None = None  # 주가순자산비율
    roe: float | None = None  # 자기자본이익률
    debt_ratio: float | None = None  # 부채비율
    eps: float | None = None
    bps: float | None = None
    fs_div: str | None = None  # Financial statement division: 'CFS' or 'OFS'
