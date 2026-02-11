"""Simple backtesting framework for evaluating trading signals."""

from dataclasses import dataclass
from datetime import date
from enum import Enum

from src.agents import Opinion
from src.data.models import DailyPrice


class TradeAction(str, Enum):
    BUY = "매수"
    SELL = "매도"
    HOLD = "보유"


@dataclass
class Trade:
    """Record of a single trade."""

    stock_code: str
    action: TradeAction
    entry_date: date
    entry_price: int
    exit_date: date | None = None
    exit_price: int | None = None
    shares: int = 1
    pnl: float = 0.0
    pnl_pct: float = 0.0


@dataclass
class BacktestResult:
    """Result of backtesting a strategy."""

    stock_code: str
    stock_name: str
    start_date: date
    end_date: date
    initial_capital: float
    final_capital: float
    total_return_pct: float
    trades: list[Trade]
    win_rate: float
    avg_win_pct: float
    avg_loss_pct: float
    max_drawdown_pct: float
    sharpe_ratio: float | None = None


@dataclass
class SignalRecord:
    """Record of a trading signal."""

    date: date
    opinion: Opinion
    confidence: int


class SimpleBacktester:
    """Simple backtester for evaluating trading signals against price data."""

    def __init__(
        self,
        initial_capital: float = 10_000_000,
        position_size_pct: float = 1.0,
        stop_loss_pct: float = 5.0,
        take_profit_pct: float = 10.0,
        holding_days: int = 10,
    ) -> None:
        self.initial_capital = initial_capital
        self.position_size_pct = position_size_pct
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        self.holding_days = holding_days

    def backtest(
        self,
        prices: list[DailyPrice],
        signals: list[SignalRecord],
        stock_name: str = "",
    ) -> BacktestResult:
        """Run backtest with given signals and prices."""
        if not prices or not signals:
            return self._empty_result(prices, stock_name)

        price_map = {p.date: p for p in prices}
        sorted_prices = sorted(prices, key=lambda p: p.date)

        trades: list[Trade] = []
        capital = self.initial_capital
        position: Trade | None = None
        capital_history: list[float] = [capital]

        for signal in sorted(signals, key=lambda s: s.date):
            if signal.date not in price_map:
                continue

            current_price = price_map[signal.date]

            if position:
                position, capital = self._check_exit(
                    position, current_price, capital, price_map, sorted_prices
                )
                if position is None:
                    continue

            if signal.opinion == Opinion.BUY and signal.confidence >= 60:
                if position is None:
                    position = self._open_position(current_price, capital, signal.date)

            elif signal.opinion == Opinion.SELL and position:
                capital = self._close_position(position, current_price, trades)
                position = None

            capital_history.append(
                capital + (self._position_value(position, current_price) if position else 0)
            )

        if position and sorted_prices:
            last_price = sorted_prices[-1]
            capital = self._close_position(position, last_price, trades)

        return self._calculate_result(prices, stock_name, trades, capital, capital_history)

    def _empty_result(self, prices: list[DailyPrice], stock_name: str) -> BacktestResult:
        stock_code = prices[0].stock_code if prices else ""
        start = prices[0].date if prices else date.today()
        end = prices[-1].date if prices else date.today()

        return BacktestResult(
            stock_code=stock_code,
            stock_name=stock_name,
            start_date=start,
            end_date=end,
            initial_capital=self.initial_capital,
            final_capital=self.initial_capital,
            total_return_pct=0.0,
            trades=[],
            win_rate=0.0,
            avg_win_pct=0.0,
            avg_loss_pct=0.0,
            max_drawdown_pct=0.0,
        )

    def _open_position(self, price: DailyPrice, capital: float, signal_date: date) -> Trade:
        position_value = capital * self.position_size_pct
        shares = int(position_value / price.close_price)

        return Trade(
            stock_code=price.stock_code,
            action=TradeAction.BUY,
            entry_date=signal_date,
            entry_price=price.close_price,
            shares=max(1, shares),
        )

    def _check_exit(
        self,
        position: Trade,
        current_price: DailyPrice,
        capital: float,
        price_map: dict[date, DailyPrice],
        sorted_prices: list[DailyPrice],
    ) -> tuple[Trade | None, float]:
        current_pnl_pct = (
            (current_price.close_price - position.entry_price) / position.entry_price * 100
        )

        if current_pnl_pct <= -self.stop_loss_pct:
            capital = self._close_position(position, current_price, [])
            return None, capital

        if current_pnl_pct >= self.take_profit_pct:
            capital = self._close_position(position, current_price, [])
            return None, capital

        entry_idx = next(
            (i for i, p in enumerate(sorted_prices) if p.date == position.entry_date),
            -1,
        )
        if entry_idx >= 0:
            current_idx = next(
                (i for i, p in enumerate(sorted_prices) if p.date == current_price.date),
                -1,
            )
            if current_idx - entry_idx >= self.holding_days:
                capital = self._close_position(position, current_price, [])
                return None, capital

        return position, capital

    def _close_position(self, position: Trade, price: DailyPrice, trades: list[Trade]) -> float:
        position.exit_date = price.date
        position.exit_price = price.close_price
        position.pnl = (price.close_price - position.entry_price) * position.shares
        position.pnl_pct = (price.close_price - position.entry_price) / position.entry_price * 100
        position.action = TradeAction.SELL

        trades.append(position)

        return self.initial_capital + position.pnl

    def _position_value(self, position: Trade, price: DailyPrice) -> float:
        return position.shares * price.close_price

    def _calculate_result(
        self,
        prices: list[DailyPrice],
        stock_name: str,
        trades: list[Trade],
        final_capital: float,
        capital_history: list[float],
    ) -> BacktestResult:
        stock_code = prices[0].stock_code if prices else ""
        sorted_prices = sorted(prices, key=lambda p: p.date)
        start = sorted_prices[0].date if sorted_prices else date.today()
        end = sorted_prices[-1].date if sorted_prices else date.today()

        total_return = (final_capital - self.initial_capital) / self.initial_capital * 100

        wins = [t for t in trades if t.pnl > 0]
        losses = [t for t in trades if t.pnl <= 0]

        win_rate = len(wins) / len(trades) * 100 if trades else 0.0
        avg_win = sum(t.pnl_pct for t in wins) / len(wins) if wins else 0.0
        avg_loss = sum(t.pnl_pct for t in losses) / len(losses) if losses else 0.0

        max_dd = self._calculate_max_drawdown(capital_history)

        return BacktestResult(
            stock_code=stock_code,
            stock_name=stock_name,
            start_date=start,
            end_date=end,
            initial_capital=self.initial_capital,
            final_capital=final_capital,
            total_return_pct=total_return,
            trades=trades,
            win_rate=win_rate,
            avg_win_pct=avg_win,
            avg_loss_pct=avg_loss,
            max_drawdown_pct=max_dd,
        )

    def _calculate_max_drawdown(self, capital_history: list[float]) -> float:
        if len(capital_history) < 2:
            return 0.0

        peak = capital_history[0]
        max_dd = 0.0

        for value in capital_history:
            if value > peak:
                peak = value
            dd = (peak - value) / peak * 100
            if dd > max_dd:
                max_dd = dd

        return max_dd


def run_simple_backtest(
    prices: list[DailyPrice],
    signals: list[SignalRecord],
    stock_name: str = "",
    initial_capital: float = 10_000_000,
) -> BacktestResult:
    """Convenience function to run a simple backtest."""
    backtester = SimpleBacktester(initial_capital=initial_capital)
    return backtester.backtest(prices, signals, stock_name)
