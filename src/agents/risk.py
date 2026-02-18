"""Risk assessment agent for stock trading."""

import re

from loguru import logger

from src.agents.base import (
    AgentOpinion,
    AnalysisData,
    BaseAgent,
    Opinion,
)
from src.agents.llm.base import LLMClient


class RiskAssessmentAgent(BaseAgent):
    """Risk assessment agent evaluating downside risks."""

    SYSTEM_PROMPT = """당신은 한국 주식시장 전문 리스크 분석가입니다.

## 역할
투자의 하방 리스크와 위험 요소를 분석하여 리스크 관점의 의견을 제시합니다.
다른 분석가들이 놓칠 수 있는 위험 요소를 발굴하는 것이 핵심 역할입니다.

## 리스크 분석 영역

### 변동성 리스크
- 일일 변동폭 (고가-저가)
- 최근 변동성 대비 과거 평균
- 급등/급락 패턴

### 유동성 리스크
- 거래량 감소 추세
- 호가 스프레드 (유추)
- 대량 매도 시 충격

### 가격 리스크
- 고점 대비 하락폭
- 지지선 이탈 가능성
- 손절 라인 근접도

### 구조적 리스크
- 재무 건전성 (부채비율)
- 실적 변동성
- 업종 사이클 위치

## 분석 원칙
1. 낙관론보다 보수적 관점 유지
2. 최악의 시나리오 고려
3. 리스크 대비 수익률 평가

## 신뢰도 점수 기준 (리스크 낮음 = 높은 점수)
- 80~100: 리스크 낮음, 안정적
- 60~79: 리스크 보통, 관리 가능
- 40~59: 리스크 주의, 헷지 필요
- 20~39: 고위험, 신중
- 0~19: 매우 고위험, 회피 권장

## 출력 형식 (정확히 준수)
의견: [매수/중립/매도]
신뢰도: [0-100]
근거1: [리스크 요인]
근거2: [리스크 요인]
근거3: [리스크 요인]
"""

    def __init__(self, llm_client: LLMClient) -> None:
        super().__init__(name="리스크분석", llm_client=llm_client)

    def get_system_prompt(self) -> str:
        return self.SYSTEM_PROMPT

    async def prepare_prompt(self, data: AnalysisData) -> str:
        if not data.prices or len(data.prices) < 5:
            return self._prepare_minimal_prompt(data)

        current_price = data.prices[-1].close_price
        risk_metrics = self._calculate_risk_metrics(data.prices)

        prompt = f"""## 분석 대상
종목: {data.stock_name} ({data.stock_code})
현재가: {current_price:,}원

## 리스크 지표

### 변동성
- 20일 일평균 변동폭: {risk_metrics["avg_daily_range"]:.1f}%
- 최근 5일 변동폭: {risk_metrics["recent_volatility"]:.1f}%
- 변동성 비율 (최근/평균): {risk_metrics["volatility_ratio"]:.2f}배

### 가격 위치
- 20일 고점 대비: {risk_metrics["from_high_20d"]:.1f}%
- 20일 저점 대비: {risk_metrics["from_low_20d"]:.1f}%
- 최근 5일 수익률: {risk_metrics["return_5d"]:.1f}%

### 거래량
- 거래량 추세: {risk_metrics["volume_trend"]}
- 거래량 변동: {risk_metrics["volume_change"]:.1f}%

{self._format_financial_risks(data)}

위 리스크 요소들을 분석하여 지정된 형식으로 의견을 제시하세요.
"""
        return prompt

    def _prepare_minimal_prompt(self, data: AnalysisData) -> str:
        current_price = data.prices[-1].close_price if data.prices else 0

        prompt = f"""## 분석 대상
종목: {data.stock_name} ({data.stock_code})
현재가: {current_price:,}원

## 리스크 지표
충분한 가격 데이터가 없어 제한적 분석만 가능합니다.
보수적 관점에서 리스크를 평가하세요.

위 정보를 기반으로 지정된 형식으로 의견을 제시하세요.
"""
        return prompt

    def _calculate_risk_metrics(self, prices: list) -> dict[str, float | str]:
        closes = [p.close_price for p in prices]
        highs = [p.high_price for p in prices]
        lows = [p.low_price for p in prices]
        volumes = [p.volume for p in prices]

        daily_ranges = []
        for i, p in enumerate(prices):
            if p.close_price > 0:
                range_pct = (p.high_price - p.low_price) / p.close_price * 100
                daily_ranges.append(range_pct)

        avg_range_20d = sum(daily_ranges[-20:]) / min(20, len(daily_ranges)) if daily_ranges else 0
        recent_volatility = (
            sum(daily_ranges[-5:]) / min(5, len(daily_ranges)) if daily_ranges else 0
        )
        volatility_ratio = recent_volatility / avg_range_20d if avg_range_20d > 0 else 1.0

        high_20d = max(highs[-20:]) if len(highs) >= 20 else max(highs)
        low_20d = min(lows[-20:]) if len(lows) >= 20 else min(lows)
        current = closes[-1]

        from_high = (current - high_20d) / high_20d * 100
        from_low = (current - low_20d) / low_20d * 100 if low_20d > 0 else 0

        return_5d = 0.0
        if len(closes) >= 5:
            return_5d = (closes[-1] - closes[-5]) / closes[-5] * 100

        volume_20d = sum(volumes[-20:]) / min(20, len(volumes)) if volumes else 0
        volume_5d = sum(volumes[-5:]) / min(5, len(volumes)) if volumes else 0
        volume_change = (volume_5d - volume_20d) / volume_20d * 100 if volume_20d > 0 else 0

        if volume_change > 50:
            volume_trend = "급증"
        elif volume_change > 0:
            volume_trend = "증가"
        elif volume_change > -30:
            volume_trend = "보합"
        else:
            volume_trend = "감소"

        return {
            "avg_daily_range": avg_range_20d,
            "recent_volatility": recent_volatility,
            "volatility_ratio": volatility_ratio,
            "from_high_20d": from_high,
            "from_low_20d": from_low,
            "return_5d": return_5d,
            "volume_trend": volume_trend,
            "volume_change": volume_change,
        }

    def _format_financial_risks(self, data: AnalysisData) -> str:
        if not data.financials:
            return ""

        latest = data.financials[0]
        lines = ["### 재무 리스크"]

        if latest.debt_ratio is not None:
            if latest.debt_ratio > 200:
                lines.append(f"- 부채비율: {latest.debt_ratio:.1f}% (고위험)")
            elif latest.debt_ratio > 100:
                lines.append(f"- 부채비율: {latest.debt_ratio:.1f}% (주의)")
            else:
                lines.append(f"- 부채비율: {latest.debt_ratio:.1f}% (안정)")

        if latest.roe is not None:
            if latest.roe < 0:
                lines.append(f"- ROE: {latest.roe:.1f}% (적자)")
            elif latest.roe < 5:
                lines.append(f"- ROE: {latest.roe:.1f}% (저조)")

        return "\n".join(lines) if len(lines) > 1 else ""

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
