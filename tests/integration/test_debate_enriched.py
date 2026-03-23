from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock

from src.agents.base import AnalysisData
from src.data.models import (
    DailyPrice,
    FinancialData,
    InvestorFlow,
    MacroSnapshot,
    NewsItem,
)
from src.debate import DebateEngine


def _make_mock_llm() -> MagicMock:
    llm = MagicMock()
    llm.generate = AsyncMock(
        return_value=MagicMock(
            content="Step 1 밸류에이션: PER 15 적정\n"
            "Step 2 수익성: ROE 18% 우수\n"
            "Step 3 안정성: 부채비율 50% 안정\n"
            "Step 4 성장성: 매출 5% 성장\n"
            "Step 5 업종비교: 업종 평균 대비 양호\n"
            "Step 6 맥락: 금리 인하 수혜\n"
            "의견: 매수\n신뢰도: 75\n근거1: PER 저평가\n근거2: ROE 우수\n근거3: 성장세 유지",
            model="test-model",
        )
    )
    return llm


def _make_sample_data() -> AnalysisData:
    start = date(2026, 1, 1)
    prices = [
        DailyPrice(
            stock_code="005930",
            date=start + timedelta(days=i),
            open_price=70000,
            high_price=72000,
            low_price=69000,
            close_price=71000,
            volume=10_000_000,
        )
        for i in range(60)
    ]
    financials = [
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
            ebitda=12_000_000_000_000,
            current_ratio=160.0,
            interest_coverage=10.0,
            revenue_growth=5.0,
        )
    ]
    return AnalysisData(
        stock_code="005930",
        stock_name="삼성전자",
        prices=prices,
        financials=financials,
    )


class TestDebateEngineEnrichedIntegration:
    async def test_debate_runs_without_enrichment(self):
        llm = _make_mock_llm()
        engine = DebateEngine(llm)
        data = _make_sample_data()

        result = await engine.debate(data)

        assert result.stock_code == "005930"
        assert result.stock_name == "삼성전자"
        assert result.final_opinion is not None
        assert 0 <= result.confidence <= 100

    async def test_debate_enriches_macro_when_repo_provided(self):
        llm = _make_mock_llm()
        macro_snapshot = MacroSnapshot(
            date=date(2026, 3, 7), base_rate=3.25, usd_krw=1350.0, kospi=2700.0
        )
        macro_repo = MagicMock()
        macro_repo.get_latest = AsyncMock(return_value=macro_snapshot)

        engine = DebateEngine(llm, macro_repo=macro_repo)
        data = _make_sample_data()
        result = await engine.debate(data)

        macro_repo.get_latest.assert_called_once()
        assert result.stock_code == "005930"

    async def test_debate_enriches_investor_flow_when_repo_provided(self):
        llm = _make_mock_llm()
        flows = [
            InvestorFlow(
                stock_code="005930",
                date=date(2026, 3, 7),
                foreign_net=500_000,
                institution_net=-100_000,
            )
        ]
        investor_repo = MagicMock()
        investor_repo.get_recent = AsyncMock(return_value=flows)

        engine = DebateEngine(llm, investor_flow_repo=investor_repo)
        data = _make_sample_data()
        result = await engine.debate(data)

        investor_repo.get_recent.assert_called_once_with("005930", limit=20)
        assert result.stock_code == "005930"

    async def test_debate_enriches_news_when_collector_provided(self):
        llm = _make_mock_llm()
        news = [
            NewsItem(
                title="삼성전자 1분기 실적 호조",
                published_at="2026-03-07T09:00:00",
                url="https://example.com/news/1",
                source="example.com",
            )
        ]
        news_collector = MagicMock()
        news_collector.get_news = AsyncMock(return_value=news)

        engine = DebateEngine(llm, news_collector=news_collector)
        data = _make_sample_data()
        result = await engine.debate(data)

        news_collector.get_news.assert_called_once()
        assert result.stock_code == "005930"

    async def test_debate_enriches_all_sources_in_parallel(self):
        llm = _make_mock_llm()
        macro_repo = MagicMock()
        macro_repo.get_latest = AsyncMock(
            return_value=MacroSnapshot(date=date(2026, 3, 7), base_rate=3.25)
        )
        investor_repo = MagicMock()
        investor_repo.get_recent = AsyncMock(return_value=[])
        news_collector = MagicMock()
        news_collector.get_news = AsyncMock(return_value=[])

        engine = DebateEngine(
            llm,
            macro_repo=macro_repo,
            investor_flow_repo=investor_repo,
            news_collector=news_collector,
        )
        data = _make_sample_data()
        result = await engine.debate(data)

        macro_repo.get_latest.assert_called_once()
        investor_repo.get_recent.assert_called_once()
        news_collector.get_news.assert_called_once()
        assert result.final_opinion is not None

    async def test_debate_proceeds_when_all_enrichment_fails(self):
        llm = _make_mock_llm()
        macro_repo = MagicMock()
        macro_repo.get_latest = AsyncMock(side_effect=Exception("DB 연결 실패"))
        news_collector = MagicMock()
        news_collector.get_news = AsyncMock(side_effect=Exception("API 오류"))

        engine = DebateEngine(llm, macro_repo=macro_repo, news_collector=news_collector)
        data = _make_sample_data()
        result = await engine.debate(data)

        assert result.stock_code == "005930"
        assert result.final_opinion is not None

    async def test_debate_result_includes_enriched_data_in_prompt(self):
        llm = _make_mock_llm()

        macro_repo = MagicMock()
        macro_repo.get_latest = AsyncMock(
            return_value=MacroSnapshot(
                date=date(2026, 3, 7),
                base_rate=3.25,
                usd_krw=1350.0,
                kospi=2700.0,
            )
        )
        investor_repo = MagicMock()
        investor_repo.get_recent = AsyncMock(
            return_value=[
                InvestorFlow(
                    stock_code="005930",
                    date=date(2026, 3, 7),
                    foreign_net=500_000,
                )
            ]
        )
        news_collector = MagicMock()
        news_collector.get_news = AsyncMock(
            return_value=[
                NewsItem(
                    title="삼성전자 반도체 호조",
                    published_at="2026-03-07",
                    url="https://example.com",
                )
            ]
        )

        engine = DebateEngine(
            llm,
            macro_repo=macro_repo,
            investor_flow_repo=investor_repo,
            news_collector=news_collector,
        )
        data = _make_sample_data()
        await engine.debate(data)

        assert macro_repo.get_latest.called
        assert investor_repo.get_recent.called
        assert news_collector.get_news.called
