"""Base agent module for trading analysis.

This module provides the abstract base class for all trading analysis agents,
along with common data types used across agents.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum

from loguru import logger

from src.agents.llm.base import LLMClient, LLMResponse
from src.data.models import DailyPrice, FinancialData


class Opinion(str, Enum):
    """Trading opinion type."""

    BUY = "매수"
    NEUTRAL = "중립"
    SELL = "매도"


@dataclass
class AnalysisData:
    """Input data for agent analysis.

    Args:
        stock_code: Stock code (e.g., "005930").
        stock_name: Stock name (e.g., "삼성전자").
        prices: List of daily price data.
        financials: List of financial data (optional).
        metadata: Additional context data.
        analysis_date: Date of the latest DB data used for analysis. Defaults to today if None.
    """

    stock_code: str
    stock_name: str
    prices: list[DailyPrice] = field(default_factory=list)
    financials: list[FinancialData] = field(default_factory=list)
    metadata: dict[str, str] = field(default_factory=dict)
    analysis_date: date | None = None


def format_analysis_date(data: "AnalysisData") -> str:
    today = datetime.now().date()
    ref = data.analysis_date if data.analysis_date else today
    lag = (today - ref).days
    if lag == 0:
        return ref.strftime("%Y년 %m월 %d일 (오늘)")
    return ref.strftime(f"%Y년 %m월 %d일 (오늘로부터 {lag}일 전 데이터 기준)")


@dataclass
class AgentOpinion:
    """Agent analysis result.

    Attributes:
        agent_name: Name of the agent.
        opinion: Trading opinion (BUY/NEUTRAL/SELL).
        confidence: Confidence score (0-100).
        reasoning: List of reasoning points.
        timestamp: Analysis timestamp.
        raw_response: Raw LLM response text.
        model: LLM model used for analysis.
    """

    agent_name: str
    opinion: Opinion
    confidence: int
    reasoning: list[str]
    timestamp: datetime = field(default_factory=datetime.now)
    raw_response: str | None = None
    model: str | None = None


class AgentAnalysisError(Exception):
    """Raised when agent analysis fails."""

    pass


class BaseAgent(ABC):
    """Abstract base class for trading analysis agents.

    All trading agents must inherit from this class and implement
    the abstract methods: get_system_prompt(), prepare_prompt(), parse_response().

    Attributes:
        name: Agent name for identification.
        llm: LLM client for text generation.
        weight: Agent weight for consensus calculation (default: 1.0).
    """

    def __init__(self, name: str, llm_client: LLMClient) -> None:
        """Initialize the agent.

        Args:
            name: Agent name.
            llm_client: LLM client instance.
        """
        self.name = name
        self.llm = llm_client
        self.weight = 1.0

    @abstractmethod
    def get_system_prompt(self) -> str:
        """Return the system prompt for this agent.

        Returns:
            System prompt string that defines the agent's role and behavior.
        """
        ...

    @abstractmethod
    async def prepare_prompt(self, data: AnalysisData) -> str:
        """Prepare the user prompt for analysis.

        Args:
            data: Analysis input data.

        Returns:
            User prompt string to send to the LLM.
        """
        ...

    @abstractmethod
    def parse_response(self, content: str) -> AgentOpinion:
        """Parse LLM response into AgentOpinion.

        Args:
            content: Raw LLM response text.

        Returns:
            Parsed AgentOpinion object.

        Raises:
            AgentAnalysisError: If parsing fails.
        """
        ...

    async def analyze(self, data: AnalysisData) -> AgentOpinion:
        """Perform stock analysis.

        Args:
            data: Analysis input data containing stock info and prices.

        Returns:
            AgentOpinion with analysis results.

        Raises:
            AgentAnalysisError: If LLM call or parsing fails.
        """
        logger.info(f"[{self.name}] 분석 시작: {data.stock_code} ({data.stock_name})")

        # 1. LLM 호출
        try:
            system_prompt = self.get_system_prompt()
            user_prompt = await self.prepare_prompt(data)
            llm_response: LLMResponse = await self.llm.generate(
                prompt=user_prompt,
                system=system_prompt,
            )
        except Exception as e:
            logger.error(f"[{self.name}] LLM 호출 실패 ({data.stock_code}): {e}")
            raise AgentAnalysisError(f"LLM call failed: {e}") from e

        # 2. 응답 파싱
        try:
            opinion = self.parse_response(llm_response.content)
        except AgentAnalysisError:
            raise
        except Exception as e:
            logger.error(f"[{self.name}] 응답 파싱 실패 ({data.stock_code}): {e}")
            raise AgentAnalysisError(f"Parse failed: {e}") from e

        # 3. 메타데이터 보강
        opinion.agent_name = self.name
        opinion.timestamp = datetime.now()
        opinion.raw_response = llm_response.content
        opinion.model = llm_response.model

        logger.info(
            f"[{self.name}] 분석 완료: {data.stock_code} -> "
            f"{opinion.opinion.value} (확신도: {opinion.confidence})"
        )
        return opinion
