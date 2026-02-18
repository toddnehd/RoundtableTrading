from datetime import date

from src.data.models import DailyPrice
from src.screener.models import (
    ScreeningCriteria,
    ScreeningReason,
    ScreeningResult,
    TradingSignal,
)
from src.screener.rule_based import RuleBasedScreener


def test_screening_result_creation():
    result = ScreeningResult(
        stock_code="005930",
        stock_name="삼성전자",
        market="KOSPI",
        reasons=[ScreeningReason.VOLUME_SURGE, ScreeningReason.MOMENTUM],
        score=75.5,
        metrics={"volume_ratio": 2.5, "price_change_5d_pct": 8.3},
    )

    assert result.stock_code == "005930"
    assert result.stock_name == "삼성전자"
    assert result.market == "KOSPI"
    assert len(result.reasons) == 2
    assert ScreeningReason.VOLUME_SURGE in result.reasons
    assert result.score == 75.5
    assert result.metrics["volume_ratio"] == 2.5


def test_screening_result_with_latest_price():
    price = DailyPrice(
        stock_code="005930",
        date=date(2024, 1, 15),
        open_price=75000,
        high_price=77000,
        low_price=74500,
        close_price=76500,
        volume=15000000,
    )

    result = ScreeningResult(
        stock_code="005930",
        stock_name="삼성전자",
        market="KOSPI",
        latest_price=price,
    )

    assert result.latest_price is not None
    assert result.latest_price.close_price == 76500


def test_screening_criteria_defaults():
    criteria = ScreeningCriteria()

    assert criteria.min_volume == 100_000
    assert criteria.min_volume_surge_ratio == 1.5
    assert criteria.min_price == 1_000
    assert criteria.max_price is None
    assert "KOSPI" in criteria.markets
    assert "KOSDAQ" in criteria.markets
    assert criteria.lookback_days == 20


def test_screening_criteria_custom():
    criteria = ScreeningCriteria(
        min_volume=500_000,
        min_volume_surge_ratio=2.0,
        min_price=5_000,
        max_price=100_000,
        markets=["KOSPI"],
        lookback_days=60,
    )

    assert criteria.min_volume == 500_000
    assert criteria.min_volume_surge_ratio == 2.0
    assert criteria.min_price == 5_000
    assert criteria.max_price == 100_000
    assert criteria.markets == ["KOSPI"]
    assert criteria.lookback_days == 60


def test_screening_reason_values():
    assert ScreeningReason.VOLUME_SURGE.value == "거래량 급증"
    assert ScreeningReason.PRICE_BREAKOUT.value == "가격 돌파"
    assert ScreeningReason.MOMENTUM.value == "모멘텀 강세"
    assert ScreeningReason.GOLDEN_CROSS.value == "골든크로스"
    assert ScreeningReason.DEATH_CROSS.value == "데드크로스"


def test_trading_signal_creation():
    signal = TradingSignal(
        stock_code="005930",
        action="buy",
        strength=0.85,
        suggested_price=76000,
        stop_loss_pct=3.0,
        take_profit_pct=10.0,
        ttl_minutes=120,
    )

    assert signal.stock_code == "005930"
    assert signal.action == "buy"
    assert signal.strength == 0.85
    assert signal.suggested_price == 76000
    assert signal.stop_loss_pct == 3.0
    assert signal.take_profit_pct == 10.0
    assert signal.ttl_minutes == 120
    assert signal.source == "roundtable_consensus"


def test_trading_signal_defaults():
    signal = TradingSignal(
        stock_code="005930",
        action="hold",
        strength=0.5,
    )

    assert signal.suggested_price is None
    assert signal.stop_loss_pct is None
    assert signal.take_profit_pct is None
    assert signal.ttl_minutes == 60
    assert signal.source == "roundtable_consensus"


def test_rule_based_screener_instantiation():
    screener = RuleBasedScreener()

    assert screener._pool is None
    assert screener._own_pool is False


def test_rule_based_screener_with_pool():
    screener = RuleBasedScreener(pool=None)

    assert screener._pool is None


def test_compute_technical_metrics():
    screener = RuleBasedScreener()

    prices = [
        DailyPrice("005930", date(2024, 1, 20), 75000, 77000, 74000, 76000, 10000000),
        DailyPrice("005930", date(2024, 1, 19), 74000, 76000, 73500, 75000, 9000000),
        DailyPrice("005930", date(2024, 1, 18), 73000, 74500, 72500, 74000, 8500000),
        DailyPrice("005930", date(2024, 1, 17), 72000, 73500, 71500, 73000, 8000000),
        DailyPrice("005930", date(2024, 1, 16), 71000, 72500, 70500, 72000, 7500000),
    ]

    metrics = screener._compute_technical_metrics(prices)

    assert "price_change_1d_pct" in metrics
    assert "price_change_5d_pct" in metrics
    assert "ma5" in metrics


def test_compute_technical_metrics_price_change():
    screener = RuleBasedScreener()

    prices = [
        DailyPrice("005930", date(2024, 1, 20), 75000, 77000, 74000, 110000, 10000000),
        DailyPrice("005930", date(2024, 1, 19), 74000, 76000, 73500, 100000, 9000000),
    ]

    metrics = screener._compute_technical_metrics(prices)

    assert metrics["price_change_1d_pct"] == 10.0


def test_determine_screening_reasons_volume_surge():
    screener = RuleBasedScreener()
    criteria = ScreeningCriteria(min_volume_surge_ratio=1.5)

    candidate = {"volume_surge_ratio": 2.0}
    metrics: dict[str, float] = {}

    reasons = screener._determine_screening_reasons(candidate, metrics, criteria)

    assert ScreeningReason.VOLUME_SURGE in reasons


def test_determine_screening_reasons_momentum():
    screener = RuleBasedScreener()
    criteria = ScreeningCriteria()

    candidate = {"volume_surge_ratio": 1.0}
    metrics = {"price_change_5d_pct": 15.0}

    reasons = screener._determine_screening_reasons(candidate, metrics, criteria)

    assert ScreeningReason.MOMENTUM in reasons


def test_calculate_score():
    screener = RuleBasedScreener()

    candidate = {"volume_surge_ratio": 2.5}
    metrics = {"price_change_5d_pct": 8.0, "pct_from_high": -5.0}
    reasons = [ScreeningReason.VOLUME_SURGE, ScreeningReason.MOMENTUM]

    score = screener._calculate_score(candidate, metrics, reasons)

    assert score > 0
    assert isinstance(score, float)
