from datetime import date

from src.agents import Opinion
from src.backtest import (
    BacktestResult,
    SignalRecord,
    SimpleBacktester,
    Trade,
    TradeAction,
    run_simple_backtest,
)
from src.data.models import DailyPrice


def test_trade_creation():
    trade = Trade(
        stock_code="005930",
        action=TradeAction.BUY,
        entry_date=date(2024, 1, 1),
        entry_price=75000,
        shares=10,
    )

    assert trade.stock_code == "005930"
    assert trade.action == TradeAction.BUY
    assert trade.entry_price == 75000
    assert trade.shares == 10
    assert trade.exit_date is None


def test_trade_with_exit():
    trade = Trade(
        stock_code="005930",
        action=TradeAction.SELL,
        entry_date=date(2024, 1, 1),
        entry_price=75000,
        exit_date=date(2024, 1, 10),
        exit_price=80000,
        shares=10,
        pnl=50000,
        pnl_pct=6.67,
    )

    assert trade.exit_date == date(2024, 1, 10)
    assert trade.exit_price == 80000
    assert trade.pnl == 50000


def test_backtest_result_creation():
    result = BacktestResult(
        stock_code="005930",
        stock_name="삼성전자",
        start_date=date(2024, 1, 1),
        end_date=date(2024, 12, 31),
        initial_capital=10_000_000,
        final_capital=11_500_000,
        total_return_pct=15.0,
        trades=[],
        win_rate=60.0,
        avg_win_pct=8.0,
        avg_loss_pct=-3.0,
        max_drawdown_pct=5.0,
    )

    assert result.total_return_pct == 15.0
    assert result.win_rate == 60.0


def test_signal_record_creation():
    signal = SignalRecord(
        date=date(2024, 1, 5),
        opinion=Opinion.BUY,
        confidence=80,
    )

    assert signal.date == date(2024, 1, 5)
    assert signal.opinion == Opinion.BUY
    assert signal.confidence == 80


def test_simple_backtester_instantiation():
    backtester = SimpleBacktester(
        initial_capital=5_000_000,
        stop_loss_pct=3.0,
        take_profit_pct=8.0,
    )

    assert backtester.initial_capital == 5_000_000
    assert backtester.stop_loss_pct == 3.0
    assert backtester.take_profit_pct == 8.0


def test_backtest_empty_signals():
    prices = [
        DailyPrice("005930", date(2024, 1, i), 75000, 76000, 74000, 75500, 10000000)
        for i in range(1, 31)
    ]

    backtester = SimpleBacktester()
    result = backtester.backtest(prices, [], "삼성전자")

    assert result.total_return_pct == 0.0
    assert len(result.trades) == 0


def test_backtest_empty_prices():
    signals = [
        SignalRecord(date(2024, 1, 5), Opinion.BUY, 80),
    ]

    backtester = SimpleBacktester()
    result = backtester.backtest([], signals, "삼성전자")

    assert result.total_return_pct == 0.0


def test_backtest_single_buy_signal():
    prices = [
        DailyPrice("005930", date(2024, 1, i), 75000, 76000, 74000, 75000 + i * 100, 10000000)
        for i in range(1, 21)
    ]

    signals = [
        SignalRecord(date(2024, 1, 5), Opinion.BUY, 80),
    ]

    backtester = SimpleBacktester(holding_days=10)
    result = backtester.backtest(prices, signals, "삼성전자")

    assert len(result.trades) >= 1


def test_backtest_buy_and_sell():
    prices = [
        DailyPrice("005930", date(2024, 1, i), 75000, 76000, 74000, 75000 + i * 100, 10000000)
        for i in range(1, 21)
    ]

    signals = [
        SignalRecord(date(2024, 1, 3), Opinion.BUY, 80),
        SignalRecord(date(2024, 1, 10), Opinion.SELL, 70),
    ]

    backtester = SimpleBacktester(holding_days=30)
    result = backtester.backtest(prices, signals, "삼성전자")

    assert len(result.trades) >= 1


def test_max_drawdown_calculation():
    backtester = SimpleBacktester()

    capital_history = [100, 110, 105, 95, 100, 90, 95]
    max_dd = backtester._calculate_max_drawdown(capital_history)

    assert max_dd > 0


def test_run_simple_backtest_convenience():
    prices = [
        DailyPrice("005930", date(2024, 1, i), 75000, 76000, 74000, 75500, 10000000)
        for i in range(1, 11)
    ]

    signals = [
        SignalRecord(date(2024, 1, 3), Opinion.BUY, 80),
    ]

    result = run_simple_backtest(prices, signals, "삼성전자", 5_000_000)

    assert result.initial_capital == 5_000_000
    assert result.stock_name == "삼성전자"
