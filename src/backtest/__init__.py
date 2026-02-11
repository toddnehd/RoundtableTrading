"""Backtesting module for strategy evaluation."""

from src.backtest.simple import (
    BacktestResult,
    SignalRecord,
    SimpleBacktester,
    Trade,
    TradeAction,
    run_simple_backtest,
)

__all__ = [
    "BacktestResult",
    "SignalRecord",
    "SimpleBacktester",
    "Trade",
    "TradeAction",
    "run_simple_backtest",
]
