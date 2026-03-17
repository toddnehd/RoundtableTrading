"""Expanded model tests for Wave 1-2 features.

Tests for FinancialData extended fields, MacroSnapshot, InvestorFlow,
NewsItem, and Disclosure models.
"""

from datetime import date

from src.data.models import Disclosure, FinancialData, InvestorFlow, MacroSnapshot, NewsItem


class TestFinancialDataExtendedFields:
    """Tests for FinancialData 14 extended fields."""

    def test_financial_data_14_extended_fields(self):
        """All 14 extended fields should be stored correctly."""
        f = FinancialData(
            stock_code="005930",
            quarter="2025Q3",
            operating_margin=15.0,
            net_margin=12.0,
            roa=8.0,
            ebitda=5000.0,
            current_ratio=150.0,
            quick_ratio=120.0,
            interest_coverage=10.0,
            capital_retention_ratio=60.0,
            ev_ebitda=8.5,
            dps=500.0,
            dividend_yield=2.0,
            revenue_growth=5.0,
            operating_income_growth=7.0,
            net_income_growth=6.0,
        )
        assert f.operating_margin == 15.0
        assert f.net_margin == 12.0
        assert f.roa == 8.0
        assert f.ebitda == 5000.0
        assert f.current_ratio == 150.0
        assert f.quick_ratio == 120.0
        assert f.interest_coverage == 10.0
        assert f.capital_retention_ratio == 60.0
        assert f.ev_ebitda == 8.5
        assert f.dps == 500.0
        assert f.dividend_yield == 2.0
        assert f.revenue_growth == 5.0
        assert f.operating_income_growth == 7.0
        assert f.net_income_growth == 6.0

    def test_financial_data_extended_fields_default_none(self):
        """Extended fields should default to None when not provided."""
        f = FinancialData(stock_code="005930", quarter="2025Q3")
        assert f.operating_margin is None
        assert f.net_margin is None
        assert f.roa is None
        assert f.ebitda is None
        assert f.current_ratio is None
        assert f.quick_ratio is None
        assert f.interest_coverage is None
        assert f.capital_retention_ratio is None
        assert f.ev_ebitda is None
        assert f.dps is None
        assert f.dividend_yield is None
        assert f.revenue_growth is None
        assert f.operating_income_growth is None
        assert f.net_income_growth is None

    def test_financial_data_partial_extended_fields(self):
        """Setting only some extended fields should leave others as None."""
        f = FinancialData(
            stock_code="000660",
            quarter="2025Q1",
            operating_margin=20.0,
            ebitda=3000.0,
        )
        assert f.operating_margin == 20.0
        assert f.ebitda == 3000.0
        assert f.net_margin is None
        assert f.revenue_growth is None

    def test_financial_data_stock_code_and_quarter_required(self):
        """stock_code and quarter are required fields."""
        f = FinancialData(stock_code="035420", quarter="2024Q4")
        assert f.stock_code == "035420"
        assert f.quarter == "2024Q4"

    def test_financial_data_negative_growth_values(self):
        """Negative growth values should be stored correctly."""
        f = FinancialData(
            stock_code="005930",
            quarter="2025Q2",
            revenue_growth=-3.5,
            operating_income_growth=-10.2,
            net_income_growth=-8.7,
        )
        assert f.revenue_growth == -3.5
        assert f.operating_income_growth == -10.2
        assert f.net_income_growth == -8.7


class TestMacroSnapshot:
    """Tests for MacroSnapshot model."""

    def test_macro_snapshot_creation(self):
        """MacroSnapshot with all fields should be created correctly."""
        m = MacroSnapshot(
            date=date(2026, 3, 7),
            base_rate=3.5,
            usd_krw=1350.0,
            cpi_yoy=2.1,
            kospi=2700.0,
            kosdaq=900.0,
            export_yoy=5.0,
        )
        assert m.date == date(2026, 3, 7)
        assert m.base_rate == 3.5
        assert m.usd_krw == 1350.0
        assert m.cpi_yoy == 2.1
        assert m.kospi == 2700.0
        assert m.kosdaq == 900.0
        assert m.export_yoy == 5.0

    def test_macro_snapshot_optional_fields(self):
        """Optional fields should default to None."""
        m = MacroSnapshot(date=date(2026, 3, 7))
        assert m.base_rate is None
        assert m.usd_krw is None
        assert m.cpi_yoy is None
        assert m.kospi is None
        assert m.kosdaq is None
        assert m.export_yoy is None

    def test_macro_snapshot_date_required(self):
        """date field is required."""
        m = MacroSnapshot(date=date(2026, 1, 1))
        assert m.date == date(2026, 1, 1)

    def test_macro_snapshot_partial_fields(self):
        """Setting only some optional fields should leave others as None."""
        m = MacroSnapshot(date=date(2026, 3, 7), kospi=2700.0, base_rate=3.5)
        assert m.kospi == 2700.0
        assert m.base_rate == 3.5
        assert m.kosdaq is None
        assert m.export_yoy is None


class TestInvestorFlow:
    """Tests for InvestorFlow model."""

    def test_investor_flow_creation(self):
        """InvestorFlow with all fields should be created correctly."""
        f = InvestorFlow(
            stock_code="005930",
            date=date(2026, 3, 7),
            foreign_net=1000000,
            institution_net=-500000,
            retail_net=-500000,
        )
        assert f.stock_code == "005930"
        assert f.date == date(2026, 3, 7)
        assert f.foreign_net == 1000000
        assert f.institution_net == -500000
        assert f.retail_net == -500000

    def test_investor_flow_optional_fields(self):
        """Optional fields should default to None."""
        f = InvestorFlow(stock_code="005930", date=date(2026, 3, 7))
        assert f.foreign_net is None
        assert f.institution_net is None
        assert f.retail_net is None

    def test_investor_flow_negative_values(self):
        """Negative net values (net selling) should be stored correctly."""
        f = InvestorFlow(
            stock_code="000660",
            date=date(2026, 3, 7),
            foreign_net=-200000,
            institution_net=-300000,
            retail_net=500000,
        )
        assert f.foreign_net == -200000
        assert f.institution_net == -300000
        assert f.retail_net == 500000


class TestNewsItem:
    """Tests for NewsItem model."""

    def test_news_item_creation(self):
        """NewsItem with all fields should be created correctly."""
        n = NewsItem(
            title="삼성전자 실적 호조",
            published_at="2026-03-07T10:00:00",
            url="https://example.com/news",
            source="example.com",
        )
        assert n.title == "삼성전자 실적 호조"
        assert n.published_at == "2026-03-07T10:00:00"
        assert n.url == "https://example.com/news"
        assert n.source == "example.com"

    def test_news_item_default_source(self):
        """source should default to empty string."""
        n = NewsItem(title="테스트", published_at="2026-03-07", url="https://example.com")
        assert n.source == ""

    def test_news_item_required_fields(self):
        """title, published_at, url are required fields."""
        n = NewsItem(
            title="뉴스 제목",
            published_at="2026-03-07",
            url="https://news.example.com/article/123",
        )
        assert n.title == "뉴스 제목"
        assert n.published_at == "2026-03-07"
        assert n.url == "https://news.example.com/article/123"


class TestDisclosure:
    """Tests for Disclosure model."""

    def test_disclosure_creation(self):
        """Disclosure with all fields should be created correctly."""
        d = Disclosure(
            rcept_no="20260307000123",
            report_nm="주요사항보고서",
            rcept_dt="20260307",
            corp_name="삼성전자",
        )
        assert d.rcept_no == "20260307000123"
        assert d.report_nm == "주요사항보고서"
        assert d.rcept_dt == "20260307"
        assert d.corp_name == "삼성전자"

    def test_disclosure_default_corp_name(self):
        """corp_name should default to empty string."""
        d = Disclosure(rcept_no="123", report_nm="공시", rcept_dt="20260307")
        assert d.corp_name == ""

    def test_disclosure_required_fields(self):
        """rcept_no, report_nm, rcept_dt are required fields."""
        d = Disclosure(
            rcept_no="20260307000456",
            report_nm="배당결정",
            rcept_dt="20260307",
        )
        assert d.rcept_no == "20260307000456"
        assert d.report_nm == "배당결정"
        assert d.rcept_dt == "20260307"
