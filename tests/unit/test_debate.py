from datetime import date
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.agents import AgentOpinion, AnalysisData, Opinion
from src.data.models import DailyPrice
from src.debate import ConsensusLevel, DebateEngine, DebateResult


@pytest.fixture
def sample_prices():
    return [
        DailyPrice(
            "005930", date(2024, 1, i), 75000 + i * 100, 76000, 74000, 75500 + i * 50, 10000000
        )
        for i in range(1, 61)
    ]


@pytest.fixture
def sample_data(sample_prices):
    return AnalysisData(
        stock_code="005930",
        stock_name="삼성전자",
        prices=sample_prices,
    )


@pytest.fixture
def mock_llm():
    llm = MagicMock()
    llm.generate = AsyncMock(
        return_value=MagicMock(content="의견: 매수\n신뢰도: 75\n근거1: 테스트", model="test-model")
    )
    return llm


def test_debate_result_creation():
    result = DebateResult(
        stock_code="005930",
        stock_name="삼성전자",
        final_opinion=Opinion.BUY,
        confidence=75,
        consensus_level=ConsensusLevel.STRONG,
        individual_opinions=[],
        moderator_opinion=None,
        reasoning=["테스트 근거"],
    )

    assert result.stock_code == "005930"
    assert result.final_opinion == Opinion.BUY
    assert result.confidence == 75
    assert result.consensus_level == ConsensusLevel.STRONG


def test_consensus_level_values():
    assert ConsensusLevel.STRONG.value == "강한 합의"
    assert ConsensusLevel.MODERATE.value == "보통 합의"
    assert ConsensusLevel.WEAK.value == "약한 합의"
    assert ConsensusLevel.DIVIDED.value == "의견 분산"


def test_debate_engine_instantiation(mock_llm):
    engine = DebateEngine(mock_llm)

    assert engine.technical is not None
    assert engine.fundamental is not None
    assert engine.market is not None
    assert engine.risk is not None
    assert engine.moderator is not None


def test_calculate_consensus_strong():
    engine = DebateEngine(MagicMock())

    opinions = [
        AgentOpinion("Agent1", Opinion.BUY, 80, ["reason"]),
        AgentOpinion("Agent2", Opinion.BUY, 75, ["reason"]),
        AgentOpinion("Agent3", Opinion.BUY, 70, ["reason"]),
        AgentOpinion("Agent4", Opinion.BUY, 65, ["reason"]),
    ]

    consensus = engine._calculate_consensus(opinions)
    assert consensus == ConsensusLevel.STRONG


def test_calculate_consensus_moderate():
    engine = DebateEngine(MagicMock())

    opinions = [
        AgentOpinion("Agent1", Opinion.BUY, 80, ["reason"]),
        AgentOpinion("Agent2", Opinion.BUY, 75, ["reason"]),
        AgentOpinion("Agent3", Opinion.NEUTRAL, 70, ["reason"]),
        AgentOpinion("Agent4", Opinion.SELL, 65, ["reason"]),
    ]

    consensus = engine._calculate_consensus(opinions)
    assert consensus == ConsensusLevel.MODERATE


def test_calculate_consensus_divided():
    engine = DebateEngine(MagicMock())

    opinions = [
        AgentOpinion("Agent1", Opinion.BUY, 80, ["reason"]),
        AgentOpinion("Agent2", Opinion.SELL, 75, ["reason"]),
        AgentOpinion("Agent3", Opinion.NEUTRAL, 70, ["reason"]),
    ]

    consensus = engine._calculate_consensus(opinions)
    assert consensus in [ConsensusLevel.WEAK, ConsensusLevel.DIVIDED]


def test_calculate_consensus_empty():
    engine = DebateEngine(MagicMock())

    consensus = engine._calculate_consensus([])
    assert consensus == ConsensusLevel.DIVIDED


def test_determine_final_opinion_strong_consensus():
    engine = DebateEngine(MagicMock())

    opinions = [
        AgentOpinion("Agent1", Opinion.BUY, 80, ["reason"]),
    ]
    moderator = AgentOpinion("Moderator", Opinion.BUY, 85, ["reason"])

    final, confidence = engine._determine_final_opinion(opinions, moderator, ConsensusLevel.STRONG)

    assert final == Opinion.BUY
    assert confidence == 85


def test_determine_final_opinion_moderate_consensus():
    engine = DebateEngine(MagicMock())

    opinions = [
        AgentOpinion("Agent1", Opinion.BUY, 80, ["reason"]),
    ]
    moderator = AgentOpinion("Moderator", Opinion.BUY, 80, ["reason"])

    final, confidence = engine._determine_final_opinion(
        opinions, moderator, ConsensusLevel.MODERATE
    )

    assert final == Opinion.BUY
    assert confidence == 72


def test_determine_final_opinion_no_opinions():
    engine = DebateEngine(MagicMock())

    moderator = AgentOpinion("Moderator", Opinion.NEUTRAL, 50, ["reason"])

    final, confidence = engine._determine_final_opinion([], moderator, ConsensusLevel.DIVIDED)

    assert final == Opinion.NEUTRAL
    assert confidence == 30


def test_compile_reasoning():
    engine = DebateEngine(MagicMock())

    opinions = [
        AgentOpinion("기술적분석", Opinion.BUY, 80, ["강한 상승 추세"]),
        AgentOpinion("펀더멘털분석", Opinion.BUY, 75, ["저평가 상태"]),
        AgentOpinion("리스크분석", Opinion.NEUTRAL, 50, ["보통 리스크"]),
    ]
    moderator = AgentOpinion("사회자", Opinion.BUY, 78, ["종합적 매수 추천"])

    reasoning = engine._compile_reasoning(opinions, moderator)

    assert len(reasoning) <= 5
    assert any("기술적분석" in r for r in reasoning)
    assert any("펀더멘털분석" in r for r in reasoning)
    assert any("종합" in r for r in reasoning)
