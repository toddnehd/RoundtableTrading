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

    SYSTEM_PROMPT = """당신은 한국 주식시장 전문 기술적 분석가입니다.

## 역할
차트 패턴, 기술적 지표, 거래량을 종합 분석하여 단기(1-2주) 매매 의견을 제시합니다.

## 지표 해석 기준

### 이동평균선 배열
- 정배열 (5일 > 20일 > 60일): 상승 추세, 매수 우위
- 역배열 (5일 < 20일 < 60일): 하락 추세, 매도 우위
- 수렴/교차: 추세 전환 가능성

### RSI (14일)
- 70 이상: 과매수 구간, 단기 조정 가능성
- 30 이하: 과매도 구간, 반등 가능성
- 50 근처: 중립, 방향성 불분명

### MACD
- 양수 & 상승: 상승 모멘텀 강화
- 양수 & 하락: 상승 모멘텀 약화
- 음수 & 하락: 하락 모멘텀 강화
- 음수 & 상승: 하락 모멘텀 약화 (반등 신호)

### 거래량
- 1.5배 이상 급증 + 가격 상승: 강한 매수세
- 1.5배 이상 급증 + 가격 하락: 강한 매도세
- 평균 이하: 관망세, 추세 약화

## 분석 원칙
1. 단일 지표가 아닌 3개 이상 지표의 종합 판단
2. 추세 방향과 모멘텀의 일치 여부 확인
3. 거래량으로 추세의 신뢰도 검증

## 신뢰도 점수 기준
- 80~100: 3개 이상 지표가 같은 방향, 거래량 뒷받침
- 60~79: 2개 지표 일치, 일부 불일치
- 40~59: 혼조세, 방향성 불명확
- 20~39: 2개 이상 지표가 반대 방향
- 0~19: 명확한 반대 신호, 고위험

## 출력 형식 (정확히 준수)
의견: [매수/중립/매도]
신뢰도: [0-100]
근거1: [지표명과 해석]
근거2: [지표명과 해석]
근거3: [지표명과 해석]
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
        ma_arrangement = self._get_ma_arrangement(indicators)

        prompt = f"""## 분석 대상
종목: {data.stock_name} ({data.stock_code})
현재가: {current_price:,}원

## 기술적 지표
이동평균선:
- 5일선: {indicators["ma5"]:,}원 (현재가 대비 {self._price_diff_pct(current_price, indicators["ma5"])})
- 20일선: {indicators["ma20"]:,}원 (현재가 대비 {self._price_diff_pct(current_price, indicators["ma20"])})
- 60일선: {indicators["ma60"]:,}원 (현재가 대비 {self._price_diff_pct(current_price, indicators["ma60"])})
- 배열 상태: {ma_arrangement}

모멘텀 지표:
- RSI (14일): {indicators["rsi"]:.1f}
- MACD: {indicators["macd"]:.2f}

거래량:
- 최근 5일 평균 대비: {indicators["volume_ratio"]:.2f}배

## 최근 5일 가격
{recent_prices}

위 데이터를 종합 분석하여 지정된 형식으로 의견을 제시하세요.
"""
        return prompt

    def _price_diff_pct(self, current: int, target: int | float) -> str:
        if target == 0:
            return "N/A"
        diff = ((current - target) / target) * 100
        sign = "+" if diff >= 0 else ""
        return f"{sign}{diff:.1f}%"

    def _get_ma_arrangement(self, indicators: dict[str, float]) -> str:
        ma5, ma20, ma60 = indicators["ma5"], indicators["ma20"], indicators["ma60"]
        if ma5 > ma20 > ma60:
            return "정배열 (상승 추세)"
        elif ma5 < ma20 < ma60:
            return "역배열 (하락 추세)"
        else:
            return "혼조 (추세 전환 가능)"

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
