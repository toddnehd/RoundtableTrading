from datetime import date, timedelta
from unittest.mock import AsyncMock

import pytest

from src.agents.base import (
    AgentAnalysisError,
    AgentOpinion,
    AnalysisData,
    BaseAgent,
    Opinion,
)
from src.agents.llm.base import LLMClient, LLMResponse
from src.agents.technical import TechnicalAnalysisAgent
from src.data.models import DailyPrice


class DummyAgent(BaseAgent):
    def get_system_prompt(self) -> str:
        return "You are a test agent."

    async def prepare_prompt(self, data: AnalysisData) -> str:
        return f"Analyze {data.stock_code}"

    def parse_response(self, content: str) -> AgentOpinion:
        return AgentOpinion(
            agent_name="",
            opinion=Opinion.BUY,
            confidence=80,
            reasoning=["reason1", "reason2", "reason3"],
        )


@pytest.fixture
def mock_llm() -> AsyncMock:
    client = AsyncMock(spec=LLMClient)
    client.generate.return_value = LLMResponse(
        content="의견: 매수\n신뢰도: 85\n근거1: 상승 추세\n근거2: RSI 양호\n근거3: 거래량 증가",
        model="test-model",
        usage={"input_tokens": 10, "output_tokens": 20},
    )
    return client


@pytest.fixture
def sample_prices() -> list[DailyPrice]:
    base_date = date(2025, 12, 1)
    return [
        DailyPrice(
            stock_code="005930",
            date=base_date + timedelta(days=i),
            open_price=70000 + i * 100,
            high_price=71000 + i * 100,
            low_price=69000 + i * 100,
            close_price=70500 + i * 100,
            volume=1000000 + i * 10000,
        )
        for i in range(60)
    ]


@pytest.fixture
def sample_analysis_data(sample_prices: list[DailyPrice]) -> AnalysisData:
    return AnalysisData(
        stock_code="005930",
        stock_name="삼성전자",
        prices=sample_prices,
    )


class TestOpinionEnum:
    def test_opinion_values(self):
        assert Opinion.BUY.value == "매수"
        assert Opinion.NEUTRAL.value == "중립"
        assert Opinion.SELL.value == "매도"

    def test_opinion_is_string(self):
        assert isinstance(Opinion.BUY, str)
        assert Opinion.BUY == "매수"


class TestAnalysisData:
    def test_creation_minimal(self):
        data = AnalysisData(stock_code="005930", stock_name="삼성전자")
        assert data.stock_code == "005930"
        assert data.stock_name == "삼성전자"
        assert data.prices == []
        assert data.financials == []
        assert data.metadata == {}

    def test_creation_with_prices(self, sample_prices: list[DailyPrice]):
        data = AnalysisData(
            stock_code="005930",
            stock_name="삼성전자",
            prices=sample_prices,
        )
        assert len(data.prices) == 60


class TestAgentOpinion:
    def test_creation(self):
        opinion = AgentOpinion(
            agent_name="test",
            opinion=Opinion.BUY,
            confidence=85,
            reasoning=["reason1", "reason2"],
        )
        assert opinion.agent_name == "test"
        assert opinion.opinion == Opinion.BUY
        assert opinion.confidence == 85
        assert len(opinion.reasoning) == 2
        assert opinion.raw_response is None
        assert opinion.model is None


class TestBaseAgent:
    async def test_analyze_success(self, mock_llm: AsyncMock, sample_analysis_data: AnalysisData):
        agent = DummyAgent(name="test", llm_client=mock_llm)

        result = await agent.analyze(sample_analysis_data)

        assert result.agent_name == "test"
        assert result.opinion == Opinion.BUY
        assert result.confidence == 80
        assert result.model == "test-model"
        assert result.raw_response is not None
        mock_llm.generate.assert_called_once()

    async def test_analyze_llm_failure(
        self, mock_llm: AsyncMock, sample_analysis_data: AnalysisData
    ):
        mock_llm.generate.side_effect = Exception("API timeout")
        agent = DummyAgent(name="test", llm_client=mock_llm)

        with pytest.raises(AgentAnalysisError, match="LLM call failed"):
            await agent.analyze(sample_analysis_data)

    def test_agent_weight_default(self, mock_llm: AsyncMock):
        agent = DummyAgent(name="test", llm_client=mock_llm)
        assert agent.weight == 1.0


class TestTechnicalAnalysisAgent:
    def test_agent_name(self, mock_llm: AsyncMock):
        agent = TechnicalAnalysisAgent(llm_client=mock_llm)
        assert agent.name == "기술적분석"

    def test_system_prompt_contains_key_elements(self, mock_llm: AsyncMock):
        agent = TechnicalAnalysisAgent(llm_client=mock_llm)
        prompt = agent.get_system_prompt()

        assert "기술적 분석 전문가" in prompt
        assert "의견:" in prompt
        assert "신뢰도:" in prompt
        assert "근거" in prompt

    async def test_prepare_prompt(self, mock_llm: AsyncMock, sample_analysis_data: AnalysisData):
        agent = TechnicalAnalysisAgent(llm_client=mock_llm)

        prompt = await agent.prepare_prompt(sample_analysis_data)

        assert "삼성전자" in prompt
        assert "005930" in prompt
        assert "5일선" in prompt
        assert "RSI" in prompt
        assert "MACD" in prompt

    async def test_prepare_prompt_no_prices_raises_error(self, mock_llm: AsyncMock):
        agent = TechnicalAnalysisAgent(llm_client=mock_llm)
        data = AnalysisData(stock_code="005930", stock_name="삼성전자", prices=[])

        with pytest.raises(AgentAnalysisError, match="No price data"):
            await agent.prepare_prompt(data)

    def test_parse_response_buy(self, mock_llm: AsyncMock):
        agent = TechnicalAnalysisAgent(llm_client=mock_llm)
        content = """의견: 매수
신뢰도: 85
근거1: 5일선이 20일선을 상향 돌파
근거2: RSI가 과매도 구간에서 반등
근거3: 거래량이 평균 대비 1.5배 증가"""

        opinion = agent.parse_response(content)

        assert opinion.opinion == Opinion.BUY
        assert opinion.confidence == 85
        assert len(opinion.reasoning) == 3

    def test_parse_response_sell(self, mock_llm: AsyncMock):
        agent = TechnicalAnalysisAgent(llm_client=mock_llm)
        content = """의견: 매도
신뢰도: 70
근거1: 하락 추세
근거2: RSI 과매수
근거3: 거래량 감소"""

        opinion = agent.parse_response(content)

        assert opinion.opinion == Opinion.SELL
        assert opinion.confidence == 70

    def test_parse_response_neutral(self, mock_llm: AsyncMock):
        agent = TechnicalAnalysisAgent(llm_client=mock_llm)
        content = """의견: 중립
신뢰도: 50
근거1: 횡보 구간
근거2: 지표 혼조
근거3: 관망 필요"""

        opinion = agent.parse_response(content)

        assert opinion.opinion == Opinion.NEUTRAL
        assert opinion.confidence == 50

    def test_parse_response_invalid_defaults_to_neutral(self, mock_llm: AsyncMock):
        agent = TechnicalAnalysisAgent(llm_client=mock_llm)
        content = "This is an invalid response format"

        opinion = agent.parse_response(content)

        assert opinion.opinion == Opinion.NEUTRAL
        assert opinion.confidence == 50

    def test_parse_response_confidence_clamped(self, mock_llm: AsyncMock):
        agent = TechnicalAnalysisAgent(llm_client=mock_llm)
        content = """의견: 매수
신뢰도: 150
근거1: test"""

        opinion = agent.parse_response(content)

        assert opinion.confidence == 100

    async def test_analyze_full_flow(self, mock_llm: AsyncMock, sample_analysis_data: AnalysisData):
        agent = TechnicalAnalysisAgent(llm_client=mock_llm)

        result = await agent.analyze(sample_analysis_data)

        assert result.agent_name == "기술적분석"
        assert result.opinion == Opinion.BUY
        assert result.confidence == 85
        assert result.model == "test-model"
        assert len(result.reasoning) == 3


class TestTechnicalIndicators:
    def test_moving_average_calculation(self, mock_llm: AsyncMock, sample_prices: list[DailyPrice]):
        agent = TechnicalAnalysisAgent(llm_client=mock_llm)

        indicators = agent._calculate_indicators(sample_prices)

        assert "ma5" in indicators
        assert "ma20" in indicators
        assert "ma60" in indicators
        assert indicators["ma5"] > 0
        assert indicators["ma20"] > 0
        assert indicators["ma60"] > 0

    def test_rsi_calculation(self, mock_llm: AsyncMock, sample_prices: list[DailyPrice]):
        agent = TechnicalAnalysisAgent(llm_client=mock_llm)

        indicators = agent._calculate_indicators(sample_prices)

        assert "rsi" in indicators
        assert 0 <= indicators["rsi"] <= 100

    def test_macd_calculation(self, mock_llm: AsyncMock, sample_prices: list[DailyPrice]):
        agent = TechnicalAnalysisAgent(llm_client=mock_llm)

        indicators = agent._calculate_indicators(sample_prices)

        assert "macd" in indicators

    def test_volume_ratio_calculation(self, mock_llm: AsyncMock, sample_prices: list[DailyPrice]):
        agent = TechnicalAnalysisAgent(llm_client=mock_llm)

        indicators = agent._calculate_indicators(sample_prices)

        assert "volume_ratio" in indicators
        assert indicators["volume_ratio"] > 0
