
from decimal import Decimal, InvalidOperation


def _d(value, name):
    try:
        result = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError(f"{name} must be a valid number.")

    if not result.is_finite():
        raise ValueError(f"{name} must be finite.")

    return result


class BacktestEngine:
    """
    Spot, long-only backtesting engine.

    Signals are calculated from the previous candle's close
    and executed at the current candle's open.

    If stop-loss and take-profit are both touched in one candle,
    stop-loss is assumed to happen first.

    Stop-loss exits use adverse slippage.
    Take-profit exits use limit-style fills.
    """

    def __init__(
        self,
        initial_capital="20000",
        quote_per_trade="1000",
        fee_percentage_per_side="0.1",
        slippage_bps="5",
        stop_loss_percentage="2",
        take_profit_percentage="4",
    ):
        self.initial_capital = _d(
            initial_capital, "Initial capital"
        )
        self.quote_per_trade = _d(
            quote_per_trade, "Quote per trade"
        )

        self.fee_rate = (
            _d(fee_percentage_per_side, "Fee percentage")
            / Decimal("100")
        )

        self.slippage_rate = (
            _d(slippage_bps, "Slippage")
            / Decimal("10000")
        )

        self.stop_loss_rate = (
            _d(stop_loss_percentage, "Stop-loss percentage")
            / Decimal("100")
        )

        self.take_profit_rate = (
            _d(take_profit_percentage, "Take-profit percentage")
            / Decimal("100")
        )

        if self.initial_capital <= 0:
            raise ValueError(
                "Initial capital must be greater than zero."
            )

        if self.quote_per_trade <= 0:
            raise ValueError(
                "Quote per trade must be greater than zero."
            )

        if self.fee_rate < 0 or self.slippage_rate < 0:
            raise ValueError(
                "Fees and slippage cannot be negative."
            )

        if not (
            Decimal("0") < self.stop_loss_rate < Decimal("1")
        ):
            raise ValueError(
                "Stop-loss percentage must be greater than 0 "
                "and below 100."
            )

        if self.take_profit_rate <= 0:
            raise ValueError(
                "Take-profit percentage must be greater than zero."
            )

    def run(self, candles, strategy, start_index=None):
        if len(candles) < 2:
            raise ValueError(
                "At least two candles are required."
            )
                # Preserve existing behavior unless a backtest start index is supplied.
        if start_index is None:
            baseline_index = 0
            first_loop_index = 1

        else:
            if (
                not isinstance(start_index, int)
                or start_index < 1
                or start_index >= len(candles) - 1
            ):
                raise ValueError(
                    "Invalid backtest start index or insufficient candles."
                )

            baseline_index = start_index
            first_loop_index = start_index

        cash = self.initial_capital
        position = None

        trades = []
        ignored_signals = []

        equity_curve = [{
            "time": candles[baseline_index].open_time,
            "equity": str(self.initial_capital),
        }]
        peak_equity = self.initial_capital
        max_drawdown = Decimal("0")

        def market_sell_fill(reference_price):
            return (
                reference_price
                * (Decimal("1") - self.slippage_rate)
            )

        def close_position(
            candle,
            reference_price,
            exit_reason,
            apply_slippage,
        ):
            nonlocal cash, position

            if position is None:
                return

            if apply_slippage:
                exit_price = market_sell_fill(reference_price)
            else:
                # Take-profit is modelled as a limit order.
                # A gap above target receives price improvement.
                exit_price = reference_price

            qty = position["quantity"]

            exit_notional = qty * exit_price
            exit_fee = exit_notional * self.fee_rate

            cash += exit_notional - exit_fee

            gross_pnl = (
                exit_price - position["entry_price"]
            ) * qty

            net_pnl = (
                gross_pnl
                - position["entry_fee"]
                - exit_fee
            )

            entry_cost = (
                position["entry_price"] * qty
                + position["entry_fee"]
            )

            trades.append({
                "entry_time": position["entry_time"],
                "exit_time": candle.open_time,
                "entry_price": str(position["entry_price"]),
                "exit_price": str(exit_price),
                "quantity": str(qty),
                "entry_fee": str(position["entry_fee"]),
                "exit_fee": str(exit_fee),
                "gross_pnl": str(gross_pnl),
                "net_pnl": str(net_pnl),
                "return_percentage": str(
                    net_pnl / entry_cost * Decimal("100")
                    if entry_cost
                    else Decimal("0")
                ),
                "exit_reason": exit_reason,
            })

            position = None

        def intrabar_exit(candle):
            """
            Check the candle's high/low against stop and target.

            If both are touched, stop-loss wins.
            """

            if position is None:
                return

            low = _d(candle.low, "Candle low")
            high = _d(candle.high, "Candle high")

            stop = position["stop_price"]
            target = position["target_price"]

            stop_hit = low <= stop
            target_hit = high >= target

            if stop_hit:
                close_position(
                    candle,
                    stop,
                    "stop_loss",
                    apply_slippage=True,
                )

            elif target_hit:
                close_position(
                    candle,
                    target,
                    "take_profit",
                    apply_slippage=False,
                )

        for index in range(first_loop_index, len(candles)):
            candle = candles[index]

            open_price = _d(
                candle.open, "Candle open"
            )

            # Signal is based on the previous candle.
            signal = strategy.generate_signal(
                candles, index - 1
            )
            signal = str(signal).upper()

            # 1. Handle gaps through existing stop/target.
            if position is not None:

                if open_price <= position["stop_price"]:
                    close_position(
                        candle,
                        open_price,
                        "stop_loss_gap",
                        apply_slippage=True,
                    )

                elif open_price >= position["target_price"]:
                    close_position(
                        candle,
                        open_price,
                        "take_profit_gap",
                        apply_slippage=False,
                    )

            # 2. Apply SELL signal at candle open.
            if position is not None and signal == "SELL":
                close_position(
                    candle,
                    open_price,
                    "signal",
                    apply_slippage=True,
                )

            # 3. Open a new position on BUY.
            elif position is None and signal == "BUY":

                entry_price = (
                    open_price
                    * (Decimal("1") + self.slippage_rate)
                )

                quantity = (
                    self.quote_per_trade / entry_price
                )

                entry_notional = quantity * entry_price
                entry_fee = entry_notional * self.fee_rate

                total_cost = entry_notional + entry_fee

                if total_cost <= cash:
                    cash -= total_cost

                    position = {
                        "entry_time": candle.open_time,
                        "entry_price": entry_price,
                        "quantity": quantity,
                        "entry_fee": entry_fee,

                        "stop_price": (
                            entry_price
                            * (
                                Decimal("1")
                                - self.stop_loss_rate
                            )
                        ),

                        "target_price": (
                            entry_price
                            * (
                                Decimal("1")
                                + self.take_profit_rate
                            )
                        ),
                    }

                else:
                    ignored_signals.append({
                        "time": candle.open_time,
                        "signal": "BUY",
                        "reason": "insufficient_cash",
                    })

            elif position is None and signal == "SELL":
                ignored_signals.append({
                    "time": candle.open_time,
                    "signal": "SELL",
                    "reason": "no_open_position",
                })

            # 4. Check the candle's high/low.
            # This also checks newly opened positions.
            intrabar_exit(candle)

            # 5. Calculate portfolio equity at candle close.
            equity = cash

            if position is not None:
                close_price = _d(
                    candle.close, "Candle close"
                )

                estimated_exit = market_sell_fill(
                    close_price
                )

                estimated_exit_fee = (
                    position["quantity"]
                    * estimated_exit
                    * self.fee_rate
                )

                equity += (
                    position["quantity"] * estimated_exit
                    - estimated_exit_fee
                )

            equity_curve.append({
                "time": candle.open_time,
                "equity": str(equity),
            })

            if equity > peak_equity:
                peak_equity = equity

            drawdown = peak_equity - equity

            if drawdown > max_drawdown:
                max_drawdown = drawdown

        # Final equity includes estimated liquidation value
        # of any position still open.
        final_equity = cash
        open_position_result = None

        if position is not None:
            last_close = _d(
                candles[-1].close, "Final candle close"
            )

            estimated_exit = market_sell_fill(last_close)

            estimated_exit_fee = (
                position["quantity"]
                * estimated_exit
                * self.fee_rate
            )

            unrealized_pnl = (
                (
                    estimated_exit - position["entry_price"]
                ) * position["quantity"]
                - position["entry_fee"]
                - estimated_exit_fee
            )

            final_equity += (
                position["quantity"] * estimated_exit
                - estimated_exit_fee
            )

            open_position_result = {
                "entry_time": position["entry_time"],
                "entry_price": str(position["entry_price"]),
                "quantity": str(position["quantity"]),
                "stop_loss_price": str(position["stop_price"]),
                "take_profit_price": str(position["target_price"]),
                "unrealized_pnl": str(unrealized_pnl),
            }

        total_pnl = final_equity - self.initial_capital

        total_return = (
            total_pnl
            / self.initial_capital
            * Decimal("100")
        )

        winners = [
            trade for trade in trades
            if _d(trade["net_pnl"], "Trade P&L") > 0
        ]

        losers = [
            trade for trade in trades
            if _d(trade["net_pnl"], "Trade P&L") < 0
        ]

        gross_profit = sum(
            (
                _d(trade["net_pnl"], "Trade P&L")
                for trade in winners
            ),
            Decimal("0"),
        )

        gross_loss = abs(
            sum(
                (
                    _d(trade["net_pnl"], "Trade P&L")
                    for trade in losers
                ),
                Decimal("0"),
            )
        )

        profit_factor = (
            gross_profit / gross_loss
            if gross_loss > 0
            else (
                None
                if gross_profit > 0
                else Decimal("0")
            )
        )

        max_drawdown_percentage = (
            max_drawdown / peak_equity * Decimal("100")
            if peak_equity > 0
            else Decimal("0")
        )

        return {
            "initial_capital": str(self.initial_capital),
            "final_equity": str(final_equity),
            "total_pnl": str(total_pnl),
            "total_return_percentage": str(total_return),

            "closed_trade_count": len(trades),
            "winning_trades": len(winners),
            "losing_trades": len(losers),

            "win_rate_percentage": str(
                Decimal(len(winners))
                / Decimal(len(trades))
                * Decimal("100")
                if trades
                else Decimal("0")
            ),

            "profit_factor": (
                str(profit_factor)
                if profit_factor is not None
                else None
            ),

            "max_drawdown": str(max_drawdown),
            "max_drawdown_percentage": str(
                max_drawdown_percentage
            ),

            "stop_loss_percentage": str(
                self.stop_loss_rate * Decimal("100")
            ),

            "take_profit_percentage": str(
                self.take_profit_rate * Decimal("100")
            ),

            "open_position": open_position_result,
            "trades": trades,
            "ignored_signals": ignored_signals,
            "equity_curve": equity_curve,

            "limitations": [
                "Spot long-only execution; Futures and short positions are not implemented.",
                "If stop-loss and take-profit are both touched in one candle, stop-loss is assumed first.",
                "Stop-loss exits use adverse market slippage; take-profit exits are modelled as limit fills.",
                "Hourly OHLC data cannot reveal the exact intrabar price path or queue position.",
                "Funding, taxes, exchange outages, partial fills and spread changes are not modelled.",
                "An open position at the end is marked to market, not force-closed.",
                "This backtest is a software simulation, not financial advice or evidence of future profitability.",
            ],
        }
