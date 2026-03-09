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
    operating_margin: float | None = None  # 영업이익률 (%)
    net_margin: float | None = None  # 순이익률 (%)
    roa: float | None = None  # 총자산이익률 (%)
    ebitda: float | None = None  # EBITDA (원)
    current_ratio: float | None = None  # 유동비율 (%)
    quick_ratio: float | None = None  # 당좌비율 (%)
    interest_coverage: float | None = None  # 이자보상배율
    capital_retention_ratio: float | None = None  # 자본유보율 (%)
    ev_ebitda: float | None = None  # EV/EBITDA
    dps: float | None = None  # 주당배당금 (원)
    dividend_yield: float | None = None  # 배당수익률 (%)
    revenue_growth: float | None = None  # 매출성장률 (%)
    operating_income_growth: float | None = None  # 영업이익성장률 (%)
    net_income_growth: float | None = None  # 순이익성장률 (%)


@dataclass
class MacroSnapshot:
    """거시경제 스냅샷 (DB 캐시)"""

    date: date
    base_rate: float | None = None  # 한국은행 기준금리 (%)
    usd_krw: float | None = None  # 원달러 환율
    cpi_yoy: float | None = None  # 소비자물가 전년비 (%)
    kospi: float | None = None  # KOSPI 지수
    kosdaq: float | None = None  # KOSDAQ 지수
    export_yoy: float | None = None  # 수출증가율 전년비 (%)


@dataclass
class InvestorFlow:
    """투자자별 수급 (DB 캐시)"""

    stock_code: str
    date: date
    foreign_net: int | None = None  # 외국인 순매수 (주)
    institution_net: int | None = None  # 기관 순매수 (주)
    retail_net: int | None = None  # 개인 순매수 (주)


@dataclass
class NewsItem:
    """뉴스 헤드라인 (런타임 조회)"""

    title: str
    published_at: str  # ISO 날짜 문자열
    url: str
    source: str = ""


@dataclass
class Disclosure:
    """공시 목록 (런타임 조회)"""

    rcept_no: str  # DART 접수번호
    report_nm: str  # 보고서명
    rcept_dt: str  # 접수일 (YYYYMMDD)
    corp_name: str = ""
