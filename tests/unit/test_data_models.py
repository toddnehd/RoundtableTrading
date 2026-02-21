from datetime import date

from src.data.models import DailyPrice, FinancialData, Stock


def test_stock_creation():
    stock = Stock(stock_code="005930", stock_name="삼성전자", market="KOSPI", sector="전기전자")

    assert stock.stock_code == "005930"
    assert stock.stock_name == "삼성전자"
    assert stock.market == "KOSPI"
    assert stock.sector == "전기전자"


def test_daily_price_creation():
    price = DailyPrice(
        stock_code="005930",
        date=date(2024, 1, 2),
        open_price=75000,
        high_price=76000,
        low_price=74500,
        close_price=75500,
        volume=10000000,
    )

    assert price.stock_code == "005930"
    assert price.close_price == 75500
    assert price.volume == 10000000


def test_daily_price_with_optional_fields():
    price = DailyPrice(
        stock_code="005930",
        date=date(2024, 1, 2),
        open_price=75000,
        high_price=76000,
        low_price=74500,
        close_price=75500,
        volume=10000000,
        trading_value=750000000000,
        market_cap=450000000000000,
    )

    assert price.trading_value == 750000000000
    assert price.market_cap == 450000000000000


def test_financial_data_with_eps_bps():
    f = FinancialData(
        stock_code="005930",
        quarter="2024Q4",
        eps=5000.0,
        bps=50000.0,
        revenue=300_000_000_000_000.0,
    )

    assert f.eps == 5000.0
    assert f.bps == 50000.0
    assert f.revenue == 300_000_000_000_000.0
    assert f.per is None  # 기본값 None 확인


def test_financial_data_defaults_none():
    f = FinancialData(stock_code="000660", quarter="2024Q3")

    assert f.eps is None
    assert f.bps is None
    assert f.roe is None
