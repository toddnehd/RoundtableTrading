"""Debate engine for multi-agent stock analysis."""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from loguru import logger

from src.agents import (
    AgentOpinion,
    AnalysisData,
    BaseAgent,
    FundamentalAnalysisAgent,
    MarketSentimentAgent,
    ModeratorAgent,
    Opinion,
    RiskAssessmentAgent,
    TechnicalAnalysisAgent,
)
from src.agents.llm.base import LLMClient


class ConsensusLevel(str, Enum):
    STRONG = "강한 합의"
    MODERATE = "보통 합의"
    WEAK = "약한 합의"
    DIVIDED = "의견 분산"


@dataclass
class DebateResult:
    """Result of multi-agent debate."""

    stock_code: str
    stock_name: str
    final_opinion: Opinion
    confidence: int
    consensus_level: ConsensusLevel
    individual_opinions: list[AgentOpinion]
    moderator_opinion: AgentOpinion | None
    reasoning: list[str]
    timestamp: datetime = field(default_factory=datetime.now)


class DebateEngine:
    """Orchestrates multi-agent debate for stock analysis."""

    def __init__(self, llm_client: LLMClient) -> None:
        self.llm = llm_client
        self.technical = TechnicalAnalysisAgent(llm_client)
        self.fundamental = FundamentalAnalysisAgent(llm_client)
        self.market = MarketSentimentAgent(llm_client)
        self.risk = RiskAssessmentAgent(llm_client)
        self.moderator = ModeratorAgent(llm_client)

    async def debate(self, data: AnalysisData) -> DebateResult:
        """Run multi-agent debate on stock data."""
        logger.info(f"토론 시작: {data.stock_name} ({data.stock_code})")

        opinions = await self._gather_opinions(data)

        consensus = self._calculate_consensus(opinions)

        self.moderator.set_opinions(opinions)
        moderator_opinion = await self.moderator.analyze(data)

        final_opinion, confidence = self._determine_final_opinion(
            opinions, moderator_opinion, consensus
        )

        reasoning = self._compile_reasoning(opinions, moderator_opinion)

        result = DebateResult(
            stock_code=data.stock_code,
            stock_name=data.stock_name,
            final_opinion=final_opinion,
            confidence=confidence,
            consensus_level=consensus,
            individual_opinions=opinions,
            moderator_opinion=moderator_opinion,
            reasoning=reasoning,
        )

        logger.info(
            f"토론 완료: {data.stock_code} -> {final_opinion.value} "
            f"(확신도: {confidence}, 합의: {consensus.value})"
        )

        return result

    async def _gather_opinions(self, data: AnalysisData) -> list[AgentOpinion]:
        """Gather opinions from all analysis agents in parallel."""
        tasks = [
            self._safe_analyze(self.technical, data),
            self._safe_analyze(self.fundamental, data),
            self._safe_analyze(self.market, data),
            self._safe_analyze(self.risk, data),
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        opinions = []
        for result in results:
            if isinstance(result, AgentOpinion):
                opinions.append(result)
            elif isinstance(result, Exception):
                logger.warning(f"에이전트 분석 실패: {result}")

        return opinions

    async def _safe_analyze(self, agent: BaseAgent, data: AnalysisData) -> AgentOpinion:
        """Safely analyze with error handling."""
        try:
            return await agent.analyze(data)
        except Exception as e:
            logger.error(f"[{agent.name}] 분석 실패: {e}")
            raise

    def _calculate_consensus(self, opinions: list[AgentOpinion]) -> ConsensusLevel:
        """Calculate consensus level from opinions."""
        if not opinions:
            return ConsensusLevel.DIVIDED

        buy_count = sum(1 for o in opinions if o.opinion == Opinion.BUY)
        sell_count = sum(1 for o in opinions if o.opinion == Opinion.SELL)
        neutral_count = sum(1 for o in opinions if o.opinion == Opinion.NEUTRAL)

        total = len(opinions)
        max_count = max(buy_count, sell_count, neutral_count)

        if max_count >= total * 0.75:
            return ConsensusLevel.STRONG
        elif max_count >= total * 0.5:
            return ConsensusLevel.MODERATE
        elif max_count >= total * 0.4:
            return ConsensusLevel.WEAK
        else:
            return ConsensusLevel.DIVIDED

    def _determine_final_opinion(
        self,
        opinions: list[AgentOpinion],
        moderator_opinion: AgentOpinion,
        consensus: ConsensusLevel,
    ) -> tuple[Opinion, int]:
        """Determine final opinion and confidence."""
        if consensus == ConsensusLevel.STRONG:
            return moderator_opinion.opinion, moderator_opinion.confidence

        if consensus == ConsensusLevel.MODERATE:
            return moderator_opinion.opinion, int(moderator_opinion.confidence * 0.9)

        if not opinions:
            return Opinion.NEUTRAL, 30

        weighted_score = 0.0
        total_weight = 0.0

        opinion_scores = {Opinion.BUY: 1, Opinion.NEUTRAL: 0, Opinion.SELL: -1}

        for opinion in opinions:
            weight = opinion.confidence / 100.0
            score = opinion_scores[opinion.opinion]
            weighted_score += score * weight
            total_weight += weight

        if total_weight == 0:
            return Opinion.NEUTRAL, 30

        avg_score = weighted_score / total_weight

        if avg_score > 0.3:
            final = Opinion.BUY
        elif avg_score < -0.3:
            final = Opinion.SELL
        else:
            final = Opinion.NEUTRAL

        confidence = int(sum(o.confidence for o in opinions) / len(opinions) * 0.7)
        confidence = max(20, min(80, confidence))

        return final, confidence

    def _compile_reasoning(
        self,
        opinions: list[AgentOpinion],
        moderator_opinion: AgentOpinion,
    ) -> list[str]:
        """Compile key reasoning points."""
        reasoning = []

        high_confidence = [o for o in opinions if o.confidence >= 70]
        for opinion in high_confidence:
            if opinion.reasoning:
                reasoning.append(f"[{opinion.agent_name}] {opinion.reasoning[0]}")

        if moderator_opinion and moderator_opinion.reasoning:
            reasoning.append(f"[종합] {moderator_opinion.reasoning[0]}")

        return reasoning[:5]


async def run_debate(
    data: AnalysisData,
    llm_client: LLMClient,
) -> DebateResult:
    """Convenience function to run a debate."""
    engine = DebateEngine(llm_client)
    return await engine.debate(data)
