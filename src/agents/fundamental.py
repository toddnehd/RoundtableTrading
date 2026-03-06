"""Fundamental analysis agent for stock trading."""

import re

from loguru import logger

from src.agents.base import (
    AgentOpinion,
    AnalysisData,
    BaseAgent,
    Opinion,
    format_analysis_date,
)
from src.agents.llm.base import LLMClient


class FundamentalAnalysisAgent(BaseAgent):
    """Fundamental analysis agent using financial metrics."""

    SYSTEM_PROMPT = """당신은 한국 주식시장 전문 펀더멘털 분석가입니다.

## 역할
기업의 재무제표, 밸류에이션, 성장성을 분석하여 중장기(3개월~1년) 투자 의견을 제시합니다.

## 분석 지표

### 밸류에이션
- PER (주가수익비율): 업종 평균 대비 고평가/저평가 판단
  - 10 이하: 저평가 가능성
  - 10~20: 적정
  - 20 이상: 고평가 가능성 (단, 성장주는 예외)
- PBR (주가순자산비율): 자산가치 대비 주가 수준
  - 1 이하: 자산가치 대비 저평가
  - 1~3: 적정
  - 3 이상: 프리미엄 반영

### 수익성
- ROE (자기자본이익률): 자본 효율성
  - 15% 이상: 우수
  - 10~15%: 양호
  - 10% 미만: 개선 필요

### 재무 안정성
- 부채비율: 재무 리스크
  - 100% 이하: 안정적
  - 100~200%: 보통
  - 200% 이상: 주의 필요

### 성장성
- 매출/영업이익 증가율: 분기별 성장 추세
- 실적 서프라이즈: 시장 기대치 대비 실적

## 분석 원칙
1. 단일 지표가 아닌 종합적 재무 분석
2. 업종 특성을 고려한 상대 비교
3. 분기별 추세 변화 확인

## 신뢰도 점수 기준
- 80~100: 밸류에이션+수익성+안정성 모두 양호
- 60~79: 2개 영역 양호
- 40~59: 혼조, 일부 우려
- 20~39: 2개 이상 영역에서 우려
- 0~19: 전반적 재무 위험

## 출력 형식 (정확히 준수)
의견: [매수/중립/매도]
신뢰도: [0-100]
근거1: [지표명과 해석]
근거2: [지표명과 해석]
근거3: [지표명과 해석]
"""

    def __init__(self, llm_client: LLMClient) -> None:
        super().__init__(name="펀더멘털분석", llm_client=llm_client)

    def get_system_prompt(self) -> str:
        return self.SYSTEM_PROMPT

    async def prepare_prompt(self, data: AnalysisData) -> str:
        if not data.financials:
            return self._prepare_prompt_without_financials(data)

        latest = data.financials[0]
        prev = data.financials[1] if len(data.financials) > 1 else None

        current_price = data.prices[-1].close_price if data.prices else 0

        prompt = f"""## 분석 기준일
{format_analysis_date(data)}

## 분석 대상
종목: {data.stock_name} ({data.stock_code})
현재가: {current_price:,}원

## 재무 지표 ({latest.quarter})

### 밸류에이션
- PER: {self._format_value(latest.per)}
- PBR: {self._format_value(latest.pbr)}

### 수익성
- ROE: {self._format_pct(latest.roe)}
- 매출액: {self._format_billions(latest.revenue)}
- 영업이익: {self._format_billions(latest.operating_income)}
- 순이익: {self._format_billions(latest.net_income)}

### 재무 안정성
- 부채비율: {self._format_pct(latest.debt_ratio)}

{self._format_quarter_comparison(latest, prev)}

위 데이터를 종합 분석하여 지정된 형식으로 의견을 제시하세요.
"""
        return prompt

    def _prepare_prompt_without_financials(self, data: AnalysisData) -> str:
        current_price = data.prices[-1].close_price if data.prices else 0
        market_cap = data.prices[-1].market_cap if data.prices else None

        prompt = f"""## 분석 기준일
{format_analysis_date(data)}

## 분석 대상
종목: {data.stock_name} ({data.stock_code})
현재가: {current_price:,}원
시가총액: {self._format_billions(market_cap)}

## 재무 데이터
상세 재무제표 데이터가 없습니다.
시가총액과 주가 수준을 기반으로 보수적인 분석을 제공하세요.

위 데이터를 종합 분석하여 지정된 형식으로 의견을 제시하세요.
"""
        return prompt

    def _format_value(self, value: float | None) -> str:
        if value is None:
            return "N/A"
        return f"{value:.2f}"

    def _format_pct(self, value: float | None) -> str:
        if value is None:
            return "N/A"
        return f"{value:.1f}%"

    def _format_billions(self, value: float | None) -> str:
        if value is None:
            return "N/A"
        return f"{value / 1_000_000_000:.1f}억원"

    def _format_quarter_comparison(self, latest, prev) -> str:
        if prev is None:
            return ""

        lines = ["## 전분기 대비 변화"]

        if latest.revenue and prev.revenue:
            change = (latest.revenue - prev.revenue) / prev.revenue * 100
            lines.append(f"- 매출액: {change:+.1f}%")

        if latest.operating_income and prev.operating_income:
            change = (
                (latest.operating_income - prev.operating_income) / abs(prev.operating_income) * 100
            )
            lines.append(f"- 영업이익: {change:+.1f}%")

        if latest.net_income and prev.net_income:
            change = (latest.net_income - prev.net_income) / abs(prev.net_income) * 100
            lines.append(f"- 순이익: {change:+.1f}%")

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
