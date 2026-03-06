"""Moderator agent for synthesizing multiple agent opinions."""

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


class ModeratorAgent(BaseAgent):
    """Moderator agent that synthesizes opinions from other agents."""

    SYSTEM_PROMPT = """당신은 한국 주식시장 투자 토론의 사회자입니다.

## 역할
여러 분석가의 의견을 종합하여 최종 투자 결론을 도출합니다.
단순 다수결이 아닌, 각 의견의 논리적 타당성과 신뢰도를 평가합니다.

## 종합 방법

### 의견 가중치 부여
- 신뢰도가 높은 의견에 더 큰 가중치
- 논리적 근거가 명확한 의견 우선
- 상충하는 의견은 양쪽 논거 검토

### 합의 도출 기준
- 3개 이상 의견 일치: 강한 합의
- 2개 의견 일치: 보통 합의
- 의견 분산: 혼조, 보수적 접근

### 리스크 분석가 의견 처리
- 리스크 분석가가 매도 의견일 경우 신중하게 반영
- 다른 분석가들의 낙관론을 견제하는 역할 인정

## 출력 형식 (정확히 준수)
의견: [매수/중립/매도]
신뢰도: [0-100]
근거1: [종합 판단 근거]
근거2: [종합 판단 근거]
근거3: [종합 판단 근거]
종합: [한 문장 요약]
"""

    def __init__(self, llm_client: LLMClient) -> None:
        super().__init__(name="사회자", llm_client=llm_client)
        self._other_opinions: list[AgentOpinion] = []

    def set_opinions(self, opinions: list[AgentOpinion]) -> None:
        """Set opinions from other agents for synthesis."""
        self._other_opinions = opinions

    def get_system_prompt(self) -> str:
        return self.SYSTEM_PROMPT

    async def prepare_prompt(self, data: AnalysisData) -> str:
        current_price = data.prices[-1].close_price if data.prices else 0

        opinions_text = self._format_opinions()

        prompt = f"""## 분석 기준일
{format_analysis_date(data)}

## 분석 대상
종목: {data.stock_name} ({data.stock_code})
현재가: {current_price:,}원

## 분석가 의견

{opinions_text}

## 지시사항
위 분석가들의 의견을 종합하여 최종 투자 결론을 도출하세요.
각 의견의 신뢰도와 근거를 고려하여 가중치를 부여하세요.
의견이 엇갈리는 경우, 리스크 관점을 우선 고려하세요.
"""
        return prompt

    def _format_opinions(self) -> str:
        if not self._other_opinions:
            return "분석가 의견이 없습니다."

        lines = []
        for i, opinion in enumerate(self._other_opinions, 1):
            lines.append(f"### {i}. {opinion.agent_name}")
            lines.append(f"- 의견: {opinion.opinion.value}")
            lines.append(f"- 신뢰도: {opinion.confidence}")
            lines.append("- 근거:")
            for j, reason in enumerate(opinion.reasoning, 1):
                lines.append(f"  {j}. {reason}")
            lines.append("")

        return "\n".join(lines)

    def parse_response(self, content: str) -> AgentOpinion:
        opinion_match = re.search(r"의견:\s*(매수|중립|매도)", content)
        confidence_match = re.search(r"신뢰도:\s*(\d+)", content)
        reasoning_matches = re.findall(r"근거\d+:\s*(.+)", content)
        summary_match = re.search(r"종합:\s*(.+)", content)

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
        if summary_match:
            reasoning.append(f"종합: {summary_match.group(1).strip()}")
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
