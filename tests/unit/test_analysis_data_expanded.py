"""Tests for AnalysisData enriched typed fields (Wave 2 expansion)."""

from datetime import date

from src.agents.base import AnalysisData
from src.data.models import Disclosure, InvestorFlow, MacroSnapshot, NewsItem


class TestAnalysisDataMacroField:
    """Tests for AnalysisData.macro field."""

    def test_analysis_data_macro_field(self):
        """macro field should store and expose MacroSnapshot correctly."""
        macro = MacroSnapshot(date=date(2026, 3, 7), base_rate=3.5)
        data = AnalysisData(stock_code="005930", stock_name="삼성전자", macro=macro)
        assert data.macro is not None
        assert data.macro.base_rate == 3.5

    def test_analysis_data_macro_defaults_none(self):
        """macro should default to None when not provided."""
        data = AnalysisData(stock_code="005930", stock_name="삼성전자")
        assert data.macro is None


class TestAnalysisDataInvestorFlow:
    """Tests for AnalysisData.investor_flow field."""

    def test_analysis_data_investor_flow(self):
        """investor_flow should store and expose InvestorFlow list correctly."""
        flows = [InvestorFlow(stock_code="005930", date=date(2026, 3, 7), foreign_net=1000000)]
        data = AnalysisData(stock_code="005930", stock_name="삼성전자", investor_flow=flows)
        assert len(data.investor_flow) == 1
        assert data.investor_flow[0].foreign_net == 1000000

    def test_analysis_data_investor_flow_defaults_empty(self):
        """investor_flow should default to empty list when not provided."""
        data = AnalysisData(stock_code="005930", stock_name="삼성전자")
        assert data.investor_flow == []

    def test_analysis_data_investor_flow_multiple_records(self):
        """investor_flow should support multiple InvestorFlow records."""
        flows = [
            InvestorFlow(stock_code="005930", date=date(2026, 3, 5), foreign_net=500000),
            InvestorFlow(stock_code="005930", date=date(2026, 3, 6), foreign_net=-200000),
            InvestorFlow(stock_code="005930", date=date(2026, 3, 7), foreign_net=1000000),
        ]
        data = AnalysisData(stock_code="005930", stock_name="삼성전자", investor_flow=flows)
        assert len(data.investor_flow) == 3
        assert data.investor_flow[2].foreign_net == 1000000


class TestAnalysisDataNewsHeadlines:
    """Tests for AnalysisData.news_headlines field."""

    def test_analysis_data_news_headlines(self):
        """news_headlines should store and expose NewsItem list correctly."""
        news = [NewsItem(title="삼성전자 호실적", published_at="2026-03-07", url="https://ex.com")]
        data = AnalysisData(stock_code="005930", stock_name="삼성전자", news_headlines=news)
        assert len(data.news_headlines) == 1
        assert data.news_headlines[0].title == "삼성전자 호실적"

    def test_analysis_data_news_headlines_defaults_empty(self):
        """news_headlines should default to empty list when not provided."""
        data = AnalysisData(stock_code="005930", stock_name="삼성전자")
        assert data.news_headlines == []

    def test_analysis_data_news_headlines_source_field(self):
        """news_headlines should preserve source field of each NewsItem."""
        news = [
            NewsItem(
                title="긍정적 뉴스",
                published_at="2026-03-07",
                url="https://ex.com",
                source="news.example.com",
            )
        ]
        data = AnalysisData(stock_code="005930", stock_name="삼성전자", news_headlines=news)
        assert data.news_headlines[0].source == "news.example.com"


class TestAnalysisDataDisclosures:
    """Tests for AnalysisData.disclosures field."""

    def test_analysis_data_disclosures(self):
        """disclosures should store and expose Disclosure list correctly."""
        disclosures = [Disclosure(rcept_no="123", report_nm="공시", rcept_dt="20260307")]
        data = AnalysisData(stock_code="005930", stock_name="삼성전자", disclosures=disclosures)
        assert len(data.disclosures) == 1

    def test_analysis_data_disclosures_defaults_empty(self):
        """disclosures should default to empty list when not provided."""
        data = AnalysisData(stock_code="005930", stock_name="삼성전자")
        assert data.disclosures == []


class TestAnalysisDataAllEnrichedFields:
    """Tests for AnalysisData with all enriched fields together."""

    def test_analysis_data_all_enriched_fields_together(self):
        """All enriched fields should be stored and accessible together."""
        macro = MacroSnapshot(date=date(2026, 3, 7), kospi=2700.0)
        flows = [InvestorFlow(stock_code="005930", date=date(2026, 3, 7), foreign_net=500000)]
        news = [NewsItem(title="긍정적 뉴스", published_at="2026-03-07", url="https://ex.com")]
        disclosures = [Disclosure(rcept_no="001", report_nm="배당공시", rcept_dt="20260307")]

        data = AnalysisData(
            stock_code="005930",
            stock_name="삼성전자",
            macro=macro,
            investor_flow=flows,
            news_headlines=news,
            disclosures=disclosures,
        )
        assert data.macro is not None
        assert data.macro.kospi == 2700.0
        assert data.investor_flow[0].foreign_net == 500000
        assert data.news_headlines[0].title == "긍정적 뉴스"
        assert data.disclosures[0].report_nm == "배당공시"

    def test_analysis_data_enriched_fields_independent_of_existing_fields(self):
        """Enriched fields should coexist with original prices/financials fields."""
        from datetime import date as d

        from src.data.models import DailyPrice

        prices = [
            DailyPrice(
                stock_code="005930",
                date=d(2026, 3, 7),
                open_price=70000,
                high_price=72000,
                low_price=69500,
                close_price=71000,
                volume=5000000,
            )
        ]
        macro = MacroSnapshot(date=date(2026, 3, 7), base_rate=3.5)

        data = AnalysisData(
            stock_code="005930",
            stock_name="삼성전자",
            prices=prices,
            macro=macro,
        )
        assert len(data.prices) == 1
        assert data.macro is not None
        assert data.macro.base_rate == 3.5
        assert data.investor_flow == []
        assert data.news_headlines == []
        assert data.disclosures == []
