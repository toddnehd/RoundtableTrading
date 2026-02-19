"""Screening result models and protocols.

This module defines data structures for stock screening results
and protocols for screener implementations.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Literal, Protocol

from src.data.models import DailyPrice


class ScreeningReason(str, Enum):
    """Reason for stock screening selection."""

    VOLUME_SURGE = "거래량 급증"
    PRICE_BREAKOUT = "가격 돌파"
    MOMENTUM = "모멘텀 강세"
    OVERSOLD = "과매도 반등"
    GOLDEN_CROSS = "골든크로스"
    DEATH_CROSS = "데드크로스"
    NEW_HIGH = "신고가"
    NEW_LOW = "신저가"
    VOLATILITY = "변동성 확대"
    CUSTOM = "사용자 정의"


@dataclass
class ScreeningResult:
    """Result of stock screening.

    Represents a stock that passed screening criteria.

    Attributes:
        stock_code: 6-digit KRX stock code.
        stock_name: Stock name in Korean.
        market: Market type (KOSPI or KOSDAQ).
        reasons: List of screening reasons.
        score: Screening score (higher = better match).
        metrics: Dictionary of calculated metrics.
        screened_at: Timestamp when screening was performed.
        latest_price: Most recent daily price data.
    """

    stock_code: str
    stock_name: str
    market: str
    reasons: list[ScreeningReason] = field(default_factory=list)
    score: float = 0.0
    metrics: dict[str, float] = field(default_factory=dict)
    screened_at: datetime = field(default_factory=datetime.now)
    latest_price: DailyPrice | None = None


@dataclass
class ScreeningCriteria:
    """Criteria for stock screening.

    Defines the filter conditions for the screener.

    Attributes:
        min_volume: Minimum average volume (e.g., 100000).
        min_volume_surge_ratio: Volume surge ratio vs 20-day avg (e.g., 2.0 = 2x).
        min_price: Minimum stock price (filters penny stocks).
        max_price: Maximum stock price.
        min_market_cap: Minimum market cap in billions KRW.
        markets: List of markets to screen (KOSPI, KOSDAQ).
        lookback_days: Number of days for calculating metrics.
        min_price_change_pct: Minimum price change percentage.
        max_price_change_pct: Maximum price change percentage.
        exclude_sectors: Sectors to exclude from screening.
    """

    min_volume: int = 100_000
    min_volume_surge_ratio: float = 1.5
    min_price: int = 1_000
    max_price: int | None = None
    min_market_cap: int | None = None  # In billions KRW
    markets: list[str] = field(default_factory=lambda: ["KOSPI", "KOSDAQ"])
    lookback_days: int = 20
    min_price_change_pct: float | None = None
    max_price_change_pct: float | None = None
    exclude_sectors: list[str] = field(default_factory=list)


class ScreenerProtocol(Protocol):
    """Protocol for screener implementations.

    All screener implementations must follow this protocol.
    This allows easy swapping between rule-based, ML-based,
    or hybrid screeners in Phase 2.
    """

    async def screen(
        self,
        criteria: ScreeningCriteria,
        limit: int = 20,
    ) -> list[ScreeningResult]:
        """Screen stocks based on criteria.

        Args:
            criteria: Screening criteria to apply.
            limit: Maximum number of results to return.

        Returns:
            List of ScreeningResult sorted by score (descending).
        """
        ...


@dataclass
class TradingSignal:
    """Trading signal for Phase 2 algorithm execution layer.

    This is a placeholder for the Two-Tier Architecture:
    - LLM Layer generates ScreeningResult + AgentOpinion
    - Execution Layer receives TradingSignal for order management

    Attributes:
        stock_code: Stock code to trade.
        action: Trade action (buy/sell/hold).
        strength: Signal strength (0.0 to 1.0).
        suggested_price: Suggested entry price.
        stop_loss_pct: Stop loss percentage.
        take_profit_pct: Take profit percentage.
        ttl_minutes: Signal time-to-live in minutes.
        generated_at: Signal generation timestamp.
        source: Signal source (e.g., "roundtable_consensus").
    """

    stock_code: str
    action: Literal["buy", "sell", "hold"]
    strength: float  # 0.0 ~ 1.0
    suggested_price: int | None = None
    stop_loss_pct: float | None = None
    take_profit_pct: float | None = None
    ttl_minutes: int = 60
    generated_at: datetime = field(default_factory=datetime.now)
    source: str = "roundtable_consensus"
