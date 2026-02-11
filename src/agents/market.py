"""Market sentiment analysis agent for stock trading."""

import re

from loguru import logger

from src.agents.base import (
    AgentOpinion,
    AnalysisData,
    BaseAgent,
    Opinion,
)
from src.agents.llm.base import LLMClient


class MarketSentimentAgent(BaseAgent):
    """Market sentiment agent analyzing macro and sector trends."""

    SYSTEM_PROMPT = """당신은 한국 주식시장 전문 시장분석가입니다.

## 역할
시장 전반의 분위기, 섹터 동향, 외부 요인을 분석하여 종목의 시장 환경을 평가합니다.

## 분석 요소

### 시장 지수 동향
- KOSPI/KOSDAQ 추세
- 글로벌 증시 영향 (미국, 중국, 유럽)
- 환율/금리 변동

### 섹터 분석
- 해당 종목 섹터의 강세/약세
- 섹터 내 경쟁사 대비 위치
- 섹터 순환 단계

### 수급 분석
- 외국인/기관 동향
- 공매도 비율
- 거래대금 추이

### 이벤트 요인
- 실적 발표 일정
- 배당/유상증자 등 주요 일정
- 규제/정책 변화

## 분석 원칙
1. 개별 종목보다 시장/섹터 관점 우선
2. 외부 리스크 요인 적극 반영
3. 단기 센티먼트와 중기 트렌드 구분

## 신뢰도 점수 기준
- 80~100: 시장/섹터 강세, 수급 양호
- 60~79: 전반적 양호, 일부 우려
- 40~59: 혼조, 관망 필요
- 20~39: 시장/섹터 약세, 주의
- 0~19: 고위험 환경

## 출력 형식 (정확히 준수)
의견: [매수/중립/매도]
신뢰도: [0-100]
근거1: [분석 내용]
근거2: [분석 내용]
근거3: [분석 내용]
"""

    def __init__(self, llm_client: LLMClient) -> None:
        super().__init__(name="시장분석", llm_client=llm_client)

    def get_system_prompt(self) -> str:
        return self.SYSTEM_PROMPT

    async def prepare_prompt(self, data: AnalysisData) -> str:
        current_price = data.prices[-1].close_price if data.prices else 0
        volume = data.prices[-1].volume if data.prices else 0
        market_cap = data.prices[-1].market_cap if data.prices else None

        sector = data.metadata.get("sector", "N/A")
        market = data.metadata.get("market", "KOSPI")

        price_trend = self._analyze_price_trend(data.prices) if data.prices else "N/A"
        volume_trend = self._analyze_volume_trend(data.prices) if data.prices else "N/A"

        prompt = f"""## 분석 대상
종목: {data.stock_name} ({data.stock_code})
시장: {market}
섹터: {sector}
현재가: {current_price:,}원
시가총액: {self._format_billions(market_cap)}

## 최근 동향
가격 추세 (20일): {price_trend}
거래량 추세: {volume_trend}
최근 거래량: {volume:,}주

## 메타데이터
{self._format_metadata(data.metadata)}

시장 환경과 섹터 동향을 고려하여 지정된 형식으로 의견을 제시하세요.
현재 시장 상황에 대한 가정을 명시하고 분석하세요.
"""
        return prompt

    def _analyze_price_trend(self, prices: list) -> str:
        if len(prices) < 20:
            return "데이터 부족"

        recent = prices[-1].close_price
        days_ago_20 = prices[-20].close_price if len(prices) >= 20 else prices[0].close_price

        change_pct = (recent - days_ago_20) / days_ago_20 * 100

        if change_pct > 10:
            return f"강세 (+{change_pct:.1f}%)"
        elif change_pct > 0:
            return f"약보합 (+{change_pct:.1f}%)"
        elif change_pct > -10:
            return f"약세 ({change_pct:.1f}%)"
        else:
            return f"급락 ({change_pct:.1f}%)"

    def _analyze_volume_trend(self, prices: list) -> str:
        if len(prices) < 10:
            return "데이터 부족"

        recent_5d = sum(p.volume for p in prices[-5:]) / 5
        prev_5d = sum(p.volume for p in prices[-10:-5]) / 5 if len(prices) >= 10 else recent_5d

        if prev_5d == 0:
            return "N/A"

        ratio = recent_5d / prev_5d

        if ratio > 1.5:
            return f"거래량 급증 ({ratio:.1f}배)"
        elif ratio > 1.1:
            return f"거래량 증가 ({ratio:.1f}배)"
        elif ratio > 0.9:
            return "보합"
        else:
            return f"거래량 감소 ({ratio:.1f}배)"

    def _format_billions(self, value: int | None) -> str:
        if value is None:
            return "N/A"
        return f"{value / 1_000_000_000_000:.2f}조원"

    def _format_metadata(self, metadata: dict[str, str]) -> str:
        if not metadata:
            return "추가 정보 없음"

        lines = []
        for key, value in metadata.items():
            if key.startswith("metric_"):
                continue
            lines.append(f"- {key}: {value}")
        return "\n".join(lines) if lines else "추가 정보 없음"

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
