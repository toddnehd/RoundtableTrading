"""Technical analysis agent for stock trading.

This module provides a technical analysis agent that analyzes stocks
using technical indicators like moving averages, RSI, and MACD.
"""

import re

from loguru import logger

from src.agents.base import (
    AgentAnalysisError,
    AgentOpinion,
    AnalysisData,
    BaseAgent,
    Opinion,
)
from src.agents.llm.base import LLMClient


class TechnicalAnalysisAgent(BaseAgent):
    """Technical analysis agent using chart patterns and indicators.

    Analyzes stocks using:
    - Moving averages (MA5, MA20, MA60)
    - RSI (Relative Strength Index)
    - MACD (Moving Average Convergence Divergence)
    - Volume analysis
    """

    SYSTEM_PROMPT = """당신은 기술적 분석 전문가입니다.

역할:
- 차트 패턴, 기술적 지표, 거래량 분석
- 단기 가격 움직임 예측

분석 시 고려사항:
1. 여러 지표의 종합 판단 (단일 지표에 의존 금지)
2. 과거 유사 패턴의 성공률
3. 현재 시장 변동성

신뢰도 점수 기준:
- 90~100점: 매우 확실함. 과거 유사 패턴에서 승률 > 80%
- 75~89점: 확신함. 여러 근거가 일치.
- 60~74점: 약한 긍정. 일부 근거만 지지.
- 40~59점: 중립. 불확실함.
- 25~39점: 약한 부정.
- 10~24점: 부정적. 여러 근거가 반대.
- 0~9점: 매우 부정적. 명확한 리스크.

출력 형식 (반드시 준수):
의견: [매수/중립/매도]
신뢰도: [0-100 숫자만]
근거1: [간결한 설명]
근거2: [간결한 설명]
근거3: [간결한 설명]
"""

    def __init__(self, llm_client: LLMClient) -> None:
        super().__init__(name="기술적분석", llm_client=llm_client)

    def get_system_prompt(self) -> str:
        return self.SYSTEM_PROMPT

    async def prepare_prompt(self, data: AnalysisData) -> str:
        if not data.prices:
            raise AgentAnalysisError("No price data available")

        indicators = self._calculate_indicators(data.prices)
        current_price = data.prices[-1].close_price
        recent_prices = self._format_recent_prices(data.prices[-5:])

        prompt = f"""다음 종목의 기술적 분석을 수행하세요.

종목: {data.stock_name} ({data.stock_code})
현재가: {current_price:,}원

기술적 지표:
- 이동평균선:
  - 5일선: {indicators['ma5']:,}원
  - 20일선: {indicators['ma20']:,}원
  - 60일선: {indicators['ma60']:,}원
- RSI (14일): {indicators['rsi']:.1f}
- MACD: {indicators['macd']:.2f}
- 거래량 (최근 5일 평균 대비): {indicators['volume_ratio']:.2f}배

최근 5일 가격 추이:
{recent_prices}

위 데이터를 바탕으로 기술적 분석을 수행하고, 지정된 형식으로 의견을 제시하세요.
"""
        return prompt

    def parse_response(self, content: str) -> AgentOpinion:
        opinion_match = re.search(r"의견:\s*(매수|중립|매도)", content)
        confidence_match = re.search(r"신뢰도:\s*(\d+)", content)
        reasoning_matches = re.findall(r"근거\d+:\s*(.+)", content)

        if not opinion_match:
            logger.warning(f"[{self.name}] 의견 파싱 실패, 기본값 사용")
            opinion_str = "중립"
        else:
            opinion_str = opinion_match.group(1)

        if not confidence_match:
            logger.warning(f"[{self.name}] 신뢰도 파싱 실패, 기본값 사용")
            confidence = 50
        else:
            confidence = min(100, max(0, int(confidence_match.group(1))))

        reasoning = [r.strip() for r in reasoning_matches[:3]]
        if not reasoning:
            reasoning = ["분석 근거를 추출할 수 없음"]

        opinion_map = {"매수": Opinion.BUY, "중립": Opinion.NEUTRAL, "매도": Opinion.SELL}
        opinion = opinion_map.get(opinion_str, Opinion.NEUTRAL)

        return AgentOpinion(
            agent_name="",
            opinion=opinion,
            confidence=confidence,
            reasoning=reasoning,
        )

    def _calculate_indicators(self, prices: list) -> dict[str, float]:
        """Calculate technical indicators from price data."""
        closes = [p.close_price for p in prices]
        volumes = [p.volume for p in prices]

        ma5 = self._moving_average(closes, 5)
        ma20 = self._moving_average(closes, 20)
        ma60 = self._moving_average(closes, 60)
        rsi = self._calculate_rsi(closes, 14)
        macd = self._calculate_macd(closes)
        volume_ratio = self._volume_ratio(volumes)

        return {
            "ma5": ma5,
            "ma20": ma20,
            "ma60": ma60,
            "rsi": rsi,
            "macd": macd,
            "volume_ratio": volume_ratio,
        }

    def _moving_average(self, values: list[int], period: int) -> int:
        if len(values) < period:
            return values[-1] if values else 0
        return int(sum(values[-period:]) / period)

    def _calculate_rsi(self, closes: list[int], period: int = 14) -> float:
        if len(closes) < period + 1:
            return 50.0

        gains = []
        losses = []
        for i in range(1, len(closes)):
            diff = closes[i] - closes[i - 1]
            if diff > 0:
                gains.append(diff)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(diff))

        recent_gains = gains[-period:]
        recent_losses = losses[-period:]

        avg_gain = sum(recent_gains) / period
        avg_loss = sum(recent_losses) / period

        if avg_loss == 0:
            return 100.0
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))

    def _calculate_macd(self, closes: list[int]) -> float:
        if len(closes) < 26:
            return 0.0
        ema12 = self._ema(closes, 12)
        ema26 = self._ema(closes, 26)
        return ema12 - ema26

    def _ema(self, values: list[int], period: int) -> float:
        if len(values) < period:
            return float(values[-1]) if values else 0.0
        multiplier = 2 / (period + 1)
        ema = float(sum(values[:period]) / period)
        for value in values[period:]:
            ema = (value - ema) * multiplier + ema
        return ema

    def _volume_ratio(self, volumes: list[int]) -> float:
        if len(volumes) < 20:
            return 1.0
        recent_avg = sum(volumes[-5:]) / 5
        period_avg = sum(volumes[-20:]) / 20
        if period_avg == 0:
            return 1.0
        return recent_avg / period_avg

    def _format_recent_prices(self, prices: list) -> str:
        lines = []
        for p in prices:
            date_str = p.date.strftime("%Y-%m-%d")
            lines.append(f"  {date_str}: {p.close_price:,}원 (거래량: {p.volume:,})")
        return "\n".join(lines)
