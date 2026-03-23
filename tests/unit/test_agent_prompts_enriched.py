from datetime import date
from unittest.mock import MagicMock

from src.agents.base import AnalysisData
from src.agents.fundamental import FundamentalAnalysisAgent
from src.agents.market import MarketSentimentAgent
from src.agents.risk import RiskAssessmentAgent
from src.agents.technical import TechnicalAnalysisAgent
from src.data.models import (
    DailyPrice,
    Disclosure,
    FinancialData,
    InvestorFlow,
    MacroSnapshot,
    NewsItem,
)


def _prices(n: int = 30) -> list[DailyPrice]:
    return [
        DailyPrice(
            stock_code="005930",
            date=date(2026, 1, i + 1),
            open_price=70000,
            high_price=72000,
            low_price=69000,
            close_price=71000,
            volume=10_000_000,
        )
        for i in range(n)
    ]


def _financials() -> list[FinancialData]:
    return [
        FinancialData(
            stock_code="005930",
            quarter="2025Q3",
            revenue=80_000_000_000_000,
            operating_income=10_000_000_000_000,
            net_income=8_000_000_000_000,
            per=15.0,
            pbr=1.2,
            roe=18.0,
            debt_ratio=50.0,
            eps=5000.0,
            bps=40000.0,
            fs_div="CFS",
            operating_margin=12.5,
            net_margin=10.0,
            roa=8.0,
            ebitda=12_000_000_000_000,
            ev_ebitda=8.5,
            current_ratio=160.0,
            quick_ratio=130.0,
            interest_coverage=10.0,
            capital_retention_ratio=60.0,
            dps=1500.0,
            dividend_yield=2.1,
            revenue_growth=5.0,
            operating_income_growth=8.0,
            net_income_growth=7.0,
        )
    ]


class TestFundamentalPromptEnriched:
    def test_cot_steps_present_in_system_prompt(self):
        agent = FundamentalAnalysisAgent(MagicMock())

        assert "Step 1 밸류에이션" in agent.SYSTEM_PROMPT
        assert "Step 6 맥락" in agent.SYSTEM_PROMPT

    async def test_extended_fields_in_prompt(self):
        llm = MagicMock()
        agent = FundamentalAnalysisAgent(llm)
        data = AnalysisData(
            stock_code="005930",
            stock_name="삼성전자",
            prices=_prices(),
            financials=_financials(),
        )
        prompt = await agent.prepare_prompt(data)

        assert "EV/EBITDA" in prompt
        assert "영업이익률" in prompt
        assert "유동비율" in prompt
        assert "이자보상배율" in prompt

    async def test_growth_rates_in_prompt(self):
        llm = MagicMock()
        agent = FundamentalAnalysisAgent(llm)
        data = AnalysisData(
            stock_code="005930",
            stock_name="삼성전자",
            prices=_prices(),
            financials=_financials(),
        )
        prompt = await agent.prepare_prompt(data)

        assert "성장률" in prompt
        assert "+5.0%" in prompt

    async def test_sector_comparison_in_prompt(self):
        llm = MagicMock()
        agent = FundamentalAnalysisAgent(llm)
        data = AnalysisData(
            stock_code="005930",
            stock_name="삼성전자",
            prices=_prices(),
            financials=_financials(),
            metadata={
                "sector_per_avg": "18.5",
                "sector_pbr_avg": "1.8",
                "sector_roe_avg": "12.0",
                "sector_op_margin_avg": "15.0",
                "peer_count": "12",
            },
        )
        prompt = await agent.prepare_prompt(data)

        assert "업종비교" in prompt
        assert "18.5" in prompt

    async def test_sector_comparison_handles_invalid_metadata(self):
        llm = MagicMock()
        agent = FundamentalAnalysisAgent(llm)
        data = AnalysisData(
            stock_code="005930",
            stock_name="삼성전자",
            prices=_prices(),
            financials=_financials(),
            metadata={"sector_per_avg": "N/A", "sector_pbr_avg": "없음", "peer_count": ""},
        )
        prompt = await agent.prepare_prompt(data)

        assert isinstance(prompt, str)

    async def test_macro_context_in_prompt(self):
        llm = MagicMock()
        agent = FundamentalAnalysisAgent(llm)
        data = AnalysisData(
            stock_code="005930",
            stock_name="삼성전자",
            prices=_prices(),
            financials=_financials(),
            macro=MacroSnapshot(date=date(2026, 3, 7), base_rate=3.25, usd_krw=1350.0, cpi_yoy=2.1),
        )
        prompt = await agent.prepare_prompt(data)

        assert "거시경제" in prompt
        assert "3.25%" in prompt

    async def test_disclosures_in_prompt(self):
        llm = MagicMock()
        agent = FundamentalAnalysisAgent(llm)
        data = AnalysisData(
            stock_code="005930",
            stock_name="삼성전자",
            prices=_prices(),
            financials=_financials(),
            disclosures=[Disclosure(rcept_no="001", report_nm="분기보고서", rcept_dt="20260307")],
        )
        prompt = await agent.prepare_prompt(data)

        assert "최근 공시" in prompt
        assert "분기보고서" in prompt

    async def test_no_enriched_sections_when_data_empty(self):
        llm = MagicMock()
        agent = FundamentalAnalysisAgent(llm)
        data = AnalysisData(
            stock_code="005930",
            stock_name="삼성전자",
            prices=_prices(),
            financials=_financials(),
        )
        prompt = await agent.prepare_prompt(data)

        assert "거시경제" not in prompt
        assert "최근 공시" not in prompt


class TestTechnicalPromptEnriched:
    async def test_investor_flow_section_in_prompt(self):
        llm = MagicMock()
        agent = TechnicalAnalysisAgent(llm)
        flows = [
            InvestorFlow(
                stock_code="005930",
                date=date(2026, 3, i + 1),
                foreign_net=500_000 + i * 10_000,
                institution_net=-100_000,
                retail_net=-400_000,
            )
            for i in range(5)
        ]
        data = AnalysisData(
            stock_code="005930",
            stock_name="삼성전자",
            prices=_prices(30),
            investor_flow=flows,
        )
        prompt = await agent.prepare_prompt(data)

        assert "투자자별 수급" in prompt
        assert "외국인" in prompt

    async def test_no_investor_section_when_flow_empty(self):
        llm = MagicMock()
        agent = TechnicalAnalysisAgent(llm)
        data = AnalysisData(
            stock_code="005930",
            stock_name="삼성전자",
            prices=_prices(30),
        )
        prompt = await agent.prepare_prompt(data)

        assert "투자자별 수급" not in prompt


class TestMarketPromptEnriched:
    async def test_macro_section_in_prompt(self):
        llm = MagicMock()
        agent = MarketSentimentAgent(llm)
        data = AnalysisData(
            stock_code="005930",
            stock_name="삼성전자",
            prices=_prices(30),
            macro=MacroSnapshot(
                date=date(2026, 3, 7), base_rate=3.25, usd_krw=1350.0, kospi=2700.0
            ),
        )
        prompt = await agent.prepare_prompt(data)

        assert "거시경제" in prompt
        assert "3.25" in prompt
        assert "KOSPI" in prompt

    async def test_investor_flow_section_in_prompt(self):
        llm = MagicMock()
        agent = MarketSentimentAgent(llm)
        flows = [
            InvestorFlow(
                stock_code="005930",
                date=date(2026, 3, 7),
                foreign_net=1_000_000,
                institution_net=-500_000,
            )
        ]
        data = AnalysisData(
            stock_code="005930",
            stock_name="삼성전자",
            prices=_prices(30),
            investor_flow=flows,
        )
        prompt = await agent.prepare_prompt(data)

        assert "투자자별 수급" in prompt

    async def test_news_section_in_prompt(self):
        llm = MagicMock()
        agent = MarketSentimentAgent(llm)
        data = AnalysisData(
            stock_code="005930",
            stock_name="삼성전자",
            prices=_prices(30),
            news_headlines=[
                NewsItem(
                    title="삼성전자 반도체 호조", published_at="2026-03-07", url="https://ex.com"
                )
            ],
        )
        prompt = await agent.prepare_prompt(data)

        assert "최근 뉴스" in prompt
        assert "삼성전자 반도체 호조" in prompt

    async def test_no_sections_when_data_empty(self):
        llm = MagicMock()
        agent = MarketSentimentAgent(llm)
        data = AnalysisData(
            stock_code="005930",
            stock_name="삼성전자",
            prices=_prices(30),
        )
        prompt = await agent.prepare_prompt(data)

        assert "거시경제" not in prompt
        assert "최근 뉴스" not in prompt


class TestRiskPromptEnriched:
    async def test_financial_risks_include_current_ratio(self):
        llm = MagicMock()
        agent = RiskAssessmentAgent(llm)
        data = AnalysisData(
            stock_code="005930",
            stock_name="삼성전자",
            prices=_prices(30),
            financials=[
                FinancialData(
                    stock_code="005930",
                    quarter="2025Q3",
                    debt_ratio=150.0,
                    current_ratio=90.0,
                    interest_coverage=0.8,
                    roe=3.0,
                )
            ],
        )
        prompt = await agent.prepare_prompt(data)

        assert "유동비율" in prompt
        assert "이자보상배율" in prompt

    async def test_investor_risks_shown_on_net_selling(self):
        llm = MagicMock()
        agent = RiskAssessmentAgent(llm)
        data = AnalysisData(
            stock_code="005930",
            stock_name="삼성전자",
            prices=_prices(30),
            investor_flow=[
                InvestorFlow(
                    stock_code="005930",
                    date=date(2026, 3, i + 1),
                    foreign_net=-200_000,
                    institution_net=-100_000,
                )
                for i in range(5)
            ],
        )
        prompt = await agent.prepare_prompt(data)

        assert "수급 리스크" in prompt
        assert "외국인" in prompt

    async def test_no_investor_risks_on_net_buying(self):
        llm = MagicMock()
        agent = RiskAssessmentAgent(llm)
        data = AnalysisData(
            stock_code="005930",
            stock_name="삼성전자",
            prices=_prices(30),
            investor_flow=[
                InvestorFlow(
                    stock_code="005930",
                    date=date(2026, 3, i + 1),
                    foreign_net=200_000,
                    institution_net=100_000,
                )
                for i in range(5)
            ],
        )
        prompt = await agent.prepare_prompt(data)

        assert "수급 리스크" not in prompt

    async def test_disclosure_risks_shown_for_risky_keywords(self):
        llm = MagicMock()
        agent = RiskAssessmentAgent(llm)
        data = AnalysisData(
            stock_code="005930",
            stock_name="삼성전자",
            prices=_prices(30),
            disclosures=[Disclosure(rcept_no="001", report_nm="유상증자결정", rcept_dt="20260307")],
        )
        prompt = await agent.prepare_prompt(data)

        assert "공시 리스크" in prompt
        assert "유상증자" in prompt

    async def test_no_disclosure_risks_for_routine_disclosures(self):
        llm = MagicMock()
        agent = RiskAssessmentAgent(llm)
        data = AnalysisData(
            stock_code="005930",
            stock_name="삼성전자",
            prices=_prices(30),
            disclosures=[Disclosure(rcept_no="001", report_nm="분기보고서", rcept_dt="20260307")],
        )
        prompt = await agent.prepare_prompt(data)

        assert "공시 리스크" not in prompt

    async def test_macro_risks_shown_for_high_rate(self):
        llm = MagicMock()
        agent = RiskAssessmentAgent(llm)
        data = AnalysisData(
            stock_code="005930",
            stock_name="삼성전자",
            prices=_prices(30),
            macro=MacroSnapshot(date=date(2026, 3, 7), base_rate=4.0, usd_krw=1450.0),
        )
        prompt = await agent.prepare_prompt(data)

        assert "거시경제 리스크" in prompt
        assert "고금리" in prompt
        assert "원화 약세" in prompt
