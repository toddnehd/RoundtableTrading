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
- PER: 10 이하 저평가 / 10~20 적정 / 20 이상 고평가 (성장주 예외)
- PBR: 1 이하 자산가치 저평가 / 1~3 적정 / 3 이상 프리미엄
- EV/EBITDA: 8 이하 저평가 / 8~15 적정 / 15 이상 고평가

### 수익성
- ROE: 15% 이상 우수 / 10~15% 양호 / 10% 미만 개선 필요
- 영업이익률: 10% 이상 양호 / 5~10% 보통 / 5% 미만 주의
- 순이익률: 5% 이상 양호
- ROA: 5% 이상 양호

### 재무 안정성
- 부채비율: 100% 이하 안정 / 100~200% 보통 / 200% 이상 주의
- 유동비율: 150% 이상 양호 / 100~150% 보통 / 100% 미만 주의
- 이자보상배율: 3 이상 안정 / 1~3 주의 / 1 미만 위험

### 성장성
- 매출/영업이익/순이익 성장률 추세
- EBITDA 절대 규모와 추세

### 배당
- DPS, 배당수익률

## 분석 원칙
1. 단일 지표가 아닌 종합적 재무 분석
2. 업종 비교 데이터가 있으면 반드시 상대 평가 수행
3. 공시·거시 맥락을 재무 해석에 반영

## 신뢰도 점수 기준
- 80~100: 밸류에이션+수익성+안정성 모두 양호
- 60~79: 2개 영역 양호
- 40~59: 혼조, 일부 우려
- 20~39: 2개 이상 영역에서 우려
- 0~19: 전반적 재무 위험

## 출력 형식 (정확히 준수)
Step 1 밸류에이션: [PER/PBR/EV·EBITDA 해석 1줄]
Step 2 수익성: [ROE/영업이익률/ROA 해석 1줄]
Step 3 안정성: [부채비율/유동비율/이자보상배율 해석 1줄]
Step 4 성장성: [매출·이익 성장률 추세 1줄]
Step 5 업종비교: [동종업 대비 위치 1줄, 데이터 없으면 '업종비교 데이터 없음']
Step 6 맥락: [공시·거시경제 영향 1줄, 데이터 없으면 '추가 맥락 없음']
의견: [매수/중립/매도]
신뢰도: [0-100]
근거1: [가장 중요한 판단 근거]
근거2: [두 번째 판단 근거]
근거3: [세 번째 판단 근거]
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
- EV/EBITDA: {self._format_value(latest.ev_ebitda)}

### 수익성
- ROE: {self._format_pct(latest.roe)}
- 영업이익률: {self._format_pct(latest.operating_margin)}
- 순이익률: {self._format_pct(latest.net_margin)}
- ROA: {self._format_pct(latest.roa)}
- 매출액: {self._format_billions(latest.revenue)}
- 영업이익: {self._format_billions(latest.operating_income)}
- EBITDA: {self._format_billions(latest.ebitda)}

### 재무 안정성
- 부채비율: {self._format_pct(latest.debt_ratio)}
- 유동비율: {self._format_pct(latest.current_ratio)}
- 이자보상배율: {self._format_value(latest.interest_coverage)}

### 배당
- DPS: {self._format_value(latest.dps)}원
- 배당수익률: {self._format_pct(latest.dividend_yield)}

{self._format_growth_rates(latest)}

{self._format_quarter_comparison(latest, prev)}

{self._format_sector_comparison(data)}

{self._format_macro_context(data)}

{self._format_disclosures(data)}

위 데이터를 Step 1~6 순서로 분석한 뒤 지정된 형식으로 의견을 제시하세요.
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

    def _format_growth_rates(self, latest) -> str:
        lines = []
        if latest.revenue_growth is not None:
            lines.append(f"- 매출 성장률: {latest.revenue_growth:+.1f}%")
        if latest.operating_income_growth is not None:
            lines.append(f"- 영업이익 성장률: {latest.operating_income_growth:+.1f}%")
        if latest.net_income_growth is not None:
            lines.append(f"- 순이익 성장률: {latest.net_income_growth:+.1f}%")
        if not lines:
            return ""
        return "### 성장률 (전년동기 대비)\n" + "\n".join(lines)

    def _format_sector_comparison(self, data: AnalysisData) -> str:
        sc = {k: v for k, v in data.metadata.items() if k.startswith("sector_")}
        if not sc:
            return ""
        lines = ["## 업종비교"]
        if sc.get("sector_per_avg") not in (None, "None"):
            lines.append(f"- 업종 평균 PER: {float(sc['sector_per_avg']):.1f}")
        if sc.get("sector_pbr_avg") not in (None, "None"):
            lines.append(f"- 업종 평균 PBR: {float(sc['sector_pbr_avg']):.2f}")
        if sc.get("sector_roe_avg") not in (None, "None"):
            lines.append(f"- 업종 평균 ROE: {float(sc['sector_roe_avg']):.1f}%")
        if sc.get("sector_op_margin_avg") not in (None, "None"):
            lines.append(f"- 업종 평균 영업이익률: {float(sc['sector_op_margin_avg']):.1f}%")
        if sc.get("peer_count") not in (None, "None"):
            lines.append(f"- 비교 대상 기업 수: {int(float(sc['peer_count']))}개")
        return "\n".join(lines) if len(lines) > 1 else ""

    def _format_macro_context(self, data: AnalysisData) -> str:
        if data.macro is None:
            return ""
        m = data.macro
        parts = []
        if m.base_rate is not None:
            parts.append(f"기준금리 {m.base_rate:.2f}%")
        if m.usd_krw is not None:
            parts.append(f"원달러 {m.usd_krw:,.0f}원")
        if m.cpi_yoy is not None:
            parts.append(f"CPI 전년비 {m.cpi_yoy:+.1f}%")
        if not parts:
            return ""
        return f"## 거시경제 맥락\n- {', '.join(parts)}"

    def _format_disclosures(self, data: AnalysisData) -> str:
        if not data.disclosures:
            return ""
        lines = ["## 최근 공시 (30일)"]
        for d in data.disclosures[:3]:
            lines.append(f"- {d.rcept_dt}: {d.report_nm}")
        return "\n".join(lines)

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
