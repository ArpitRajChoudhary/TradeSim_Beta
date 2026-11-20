
from dataclasses import dataclass
from decimal import Decimal

from backtest_engine import BacktestEngine


@dataclass
class Candle:
    open_time: str
    open: str
    high: str
    low: str
    close: str
    volume: str = "1"


class OneBuyStrategy:
    def generate_signal(self, candles, index):
        return "BUY" if index == 0 else "HOLD"


def make_candles(
    second_open,
    second_high,
    second_low,
    second_close,
):
    return [
        Candle("T0", "100", "101", "99", "100"),
        Candle(
            "T1",
            second_open,
            second_high,
            second_low,
            second_close,
        ),
        Candle("T2", "100", "101", "99", "100"),
    ]


def test_stop_loss():
    candles = make_candles(
        "100", "101", "97", "99"
    )

    result = BacktestEngine(
        initial_capital="5000",
        quote_per_trade="1000",
        fee_percentage_per_side="0",
        slippage_bps="0",
        stop_loss_percentage="2",
        take_profit_percentage="4",
    ).run(candles, OneBuyStrategy())

    assert result["closed_trade_count"] == 1
    assert result["trades"][0]["exit_reason"] == "stop_loss"

    assert (
        Decimal(result["trades"][0]["exit_price"])
        == Decimal("98.00")
    )


def test_take_profit():
    candles = make_candles(
        "100", "106", "99", "105"
    )

    result = BacktestEngine(
        initial_capital="5000",
        quote_per_trade="1000",
        fee_percentage_per_side="0",
        slippage_bps="0",
        stop_loss_percentage="2",
        take_profit_percentage="4",
    ).run(candles, OneBuyStrategy())

    assert result["closed_trade_count"] == 1
    assert result["trades"][0]["exit_reason"] == "take_profit"

    assert (
        Decimal(result["trades"][0]["exit_price"])
        == Decimal("104.00")
    )


def test_stop_wins_when_both_touched():
    candles = make_candles(
        "100", "106", "97", "102"
    )

    result = BacktestEngine(
        initial_capital="5000",
        quote_per_trade="1000",
        fee_percentage_per_side="0",
        slippage_bps="0",
        stop_loss_percentage="2",
        take_profit_percentage="4",
    ).run(candles, OneBuyStrategy())

    assert result["closed_trade_count"] == 1
    assert result["trades"][0]["exit_reason"] == "stop_loss"


def test_gap_below_stop():
    candles = [
        Candle("T0", "100", "101", "99", "100"),
        Candle("T1", "100", "101", "99", "100"),
        Candle("T2", "97", "99", "96", "98"),
    ]

    result = BacktestEngine(
        initial_capital="5000",
        quote_per_trade="1000",
        fee_percentage_per_side="0",
        slippage_bps="0",
        stop_loss_percentage="2",
        take_profit_percentage="4",
    ).run(candles, OneBuyStrategy())

    assert result["closed_trade_count"] == 1
    assert result["trades"][0]["exit_reason"] == "stop_loss_gap"

    assert (
        Decimal(result["trades"][0]["exit_price"])
        == Decimal("97")
    )


def test_open_position_has_levels():
    candles = [
        Candle("T0", "100", "101", "99", "100"),
        Candle("T1", "100", "101", "99", "100"),
        Candle("T2", "100", "101", "99", "100"),
    ]

    result = BacktestEngine(
        initial_capital="5000",
        quote_per_trade="1000",
        fee_percentage_per_side="0",
        slippage_bps="0",
        stop_loss_percentage="2",
        take_profit_percentage="4",
    ).run(candles, OneBuyStrategy())

    assert result["open_position"] is not None

    assert (
        Decimal(result["open_position"]["stop_loss_price"])
        == Decimal("98.00")
    )

    assert (
        Decimal(result["open_position"]["take_profit_price"])
        == Decimal("104.00")
    )


if __name__ == "__main__":
    tests = [
        test_stop_loss,
        test_take_profit,
        test_stop_wins_when_both_touched,
        test_gap_below_stop,
        test_open_position_has_levels,
    ]

    for test in tests:
        test()
        print(f"PASS: {test.__name__}")

    print("ALL STOP-LOSS / TAKE-PROFIT TESTS PASSED.")
