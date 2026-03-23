from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

from src.agents.base import AnalysisData
from src.data.models import DailyPrice, Disclosure, InvestorFlow, MacroSnapshot, NewsItem
from src.debate import DebateEngine


def _make_llm() -> MagicMock:
    llm = MagicMock()
    llm.generate = AsyncMock(
        return_value=MagicMock(
            content="의견: 중립\n신뢰도: 50\n근거1: 테스트",
            model="test-model",
        )
    )
    return llm


def _make_data() -> AnalysisData:
    prices = [
        DailyPrice(
            stock_code="005930",
            date=date(2026, 3, i + 1),
            open_price=70000,
            high_price=72000,
            low_price=69000,
            close_price=71000,
            volume=10_000_000,
        )
        for i in range(10)
    ]
    return AnalysisData(stock_code="005930", stock_name="삼성전자", prices=prices)


class TestEnrichGracefulDegradation:
    async def test_enrich_returns_unchanged_when_no_dependencies(self):
        engine = DebateEngine(_make_llm())
        data = _make_data()
        result = await engine._enrich(data)

        assert result.macro is None
        assert result.investor_flow == []
        assert result.news_headlines == []
        assert result.disclosures == []

    async def test_enrich_populates_macro_when_repo_provided(self):
        snapshot = MacroSnapshot(date=date(2026, 3, 7), base_rate=3.25, kospi=2700.0)
        macro_repo = MagicMock()
        macro_repo.get_latest = AsyncMock(return_value=snapshot)

        engine = DebateEngine(_make_llm(), macro_repo=macro_repo)
        data = _make_data()
        result = await engine._enrich(data)

        assert result.macro is not None
        assert result.macro.base_rate == 3.25

    async def test_enrich_populates_investor_flow_when_repo_provided(self):
        flows = [InvestorFlow(stock_code="005930", date=date(2026, 3, 7), foreign_net=500_000)]
        investor_repo = MagicMock()
        investor_repo.get_recent = AsyncMock(return_value=flows)

        engine = DebateEngine(_make_llm(), investor_flow_repo=investor_repo)
        data = _make_data()
        result = await engine._enrich(data)

        assert len(result.investor_flow) == 1
        assert result.investor_flow[0].foreign_net == 500_000

    async def test_enrich_populates_news_when_collector_provided(self):
        news = [NewsItem(title="삼성 호실적", published_at="2026-03-07", url="https://ex.com")]
        news_collector = MagicMock()
        news_collector.get_news = AsyncMock(return_value=news)

        engine = DebateEngine(_make_llm(), news_collector=news_collector)
        data = _make_data()
        result = await engine._enrich(data)

        assert len(result.news_headlines) == 1
        assert result.news_headlines[0].title == "삼성 호실적"

    async def test_enrich_returns_empty_macro_when_fetcher_raises(self):
        macro_repo = MagicMock()
        macro_repo.get_latest = AsyncMock(side_effect=Exception("DB 오류"))

        engine = DebateEngine(_make_llm(), macro_repo=macro_repo)
        data = _make_data()
        result = await engine._enrich(data)

        assert result.macro is None

    async def test_enrich_returns_empty_flow_when_fetcher_raises(self):
        investor_repo = MagicMock()
        investor_repo.get_recent = AsyncMock(side_effect=Exception("DB 오류"))

        engine = DebateEngine(_make_llm(), investor_flow_repo=investor_repo)
        data = _make_data()
        result = await engine._enrich(data)

        assert result.investor_flow == []

    async def test_enrich_returns_empty_news_when_collector_raises(self):
        news_collector = MagicMock()
        news_collector.get_news = AsyncMock(side_effect=Exception("API 오류"))

        engine = DebateEngine(_make_llm(), news_collector=news_collector)
        data = _make_data()
        result = await engine._enrich(data)

        assert result.news_headlines == []

    async def test_enrich_preserves_original_data_immutability(self):
        macro_repo = MagicMock()
        macro_repo.get_latest = AsyncMock(
            return_value=MacroSnapshot(date=date(2026, 3, 7), base_rate=3.25)
        )

        engine = DebateEngine(_make_llm(), macro_repo=macro_repo)
        data = _make_data()
        original_id = id(data)
        result = await engine._enrich(data)

        assert id(result) != original_id
        assert data.macro is None


class TestFetchDisclosures:
    async def test_returns_empty_when_no_dart_api_key(self):
        engine = DebateEngine(_make_llm())
        data = _make_data()

        with patch("src.debate.engine.settings") as mock_settings:
            mock_settings.dart_api_key = ""
            result = await engine._fetch_disclosures(data)

        assert result == []

    async def test_returns_empty_when_no_pool(self):
        engine = DebateEngine(_make_llm())
        data = _make_data()

        with patch("src.debate.engine.settings") as mock_settings:
            mock_settings.dart_api_key = "test_key"
            result = await engine._fetch_disclosures(data)

        assert result == []

    async def test_returns_empty_when_corp_code_not_found(self):
        conn = AsyncMock()
        conn.fetchrow = AsyncMock(return_value=None)
        pool = MagicMock()
        pool.acquire.return_value.__aenter__ = AsyncMock(return_value=conn)
        pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)

        engine = DebateEngine(_make_llm(), pool=pool)
        data = _make_data()

        with patch("src.debate.engine.settings") as mock_settings:
            mock_settings.dart_api_key = "test_key"
            result = await engine._fetch_disclosures(data)

        assert result == []

    async def test_parses_dart_list_response(self):
        fake_corp_code_row = MagicMock()
        fake_corp_code_row.__getitem__ = MagicMock(return_value="00126380")
        fake_corp_code_row.__bool__ = MagicMock(return_value=True)

        conn = AsyncMock()
        conn.fetchrow = AsyncMock(return_value=fake_corp_code_row)
        pool = MagicMock()
        pool.acquire.return_value.__aenter__ = AsyncMock(return_value=conn)
        pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)

        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {
            "status": "000",
            "list": [
                {
                    "rcept_no": "20260307001",
                    "report_nm": "분기보고서",
                    "rcept_dt": "20260307",
                    "corp_name": "삼성전자",
                }
            ],
        }

        with (
            patch("src.debate.engine.settings") as mock_settings,
            patch("httpx.AsyncClient") as mock_client_cls,
        ):
            mock_settings.dart_api_key = "test_key"
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_resp)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_cls.return_value = mock_client

            engine = DebateEngine(_make_llm(), pool=pool)
            data = _make_data()
            result = await engine._fetch_disclosures(data)

        assert len(result) == 1
        assert isinstance(result[0], Disclosure)
        assert result[0].report_nm == "분기보고서"
