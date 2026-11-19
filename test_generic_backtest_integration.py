
import pytest

from ai_backtest import validate_strategy, run_ai_backtest


def make_rsi_config():
    return {
        "asset": "BTCUSDT",
        "market_type": "spot",
        "timeframe": "1h",
        "strategy_type": "condition_based",

        "indicators": [
            {
                "id": "rsi14",
                "type": "rsi",
                "parameters": {"period": 14},
            }
        ],

        "entry": {
            "operator": "AND",
            "conditions": [
                {
                    "left": {
                        "source": "indicator",
                        "id": "rsi14",
                        "output": "value",
                    },
                    "comparison": "less_than",
                    "right": {
                        "source": "constant",
                        "value": 30,
                    },
                }
            ],
        },

        "exit": {
            "operator": "AND",
            "conditions": [
                {
                    "left": {
                        "source": "indicator",
                        "id": "rsi14",
                        "output": "value",
                    },
                    "comparison": "greater_than",
                    "right": {
                        "source": "constant",
                        "value": 60,
                    },
                }
            ],
        },

        "initial_capital": 20000,
        "quote_per_trade": 1000,
        "fee_percentage_per_side": 0.1,
        "slippage_bps": 5,
        "stop_loss_percentage": 2,
        "take_profit_percentage": 4,
    }


@pytest.fixture
def backtest_output():
    config = validate_strategy(make_rsi_config())

    return run_ai_backtest(
        config,
        generate_report=False,
    )


def test_generic_backtest_returns_expected_structure(backtest_output):
    assert isinstance(backtest_output, dict)

    assert "results" in backtest_output
    assert "execution_time_seconds" in backtest_output
    assert "candles_processed" in backtest_output
    assert "dataset" in backtest_output

    assert backtest_output["candles_processed"] > 0
    assert backtest_output["execution_time_seconds"] >= 0
    assert backtest_output["dataset"] == "BTCUSDT_spot_1h.csv"


def test_generic_backtest_returns_valid_metrics(backtest_output):
    results = backtest_output["results"]

    assert isinstance(results, dict)

    assert results["initial_capital"] == "20000"
    assert isinstance(results["final_equity"], str)
    assert isinstance(results["total_pnl"], str)

    assert results["closed_trade_count"] >= 0
    assert results["winning_trades"] + results["losing_trades"] == (
        results["closed_trade_count"]
    )

    assert 0 <= float(results["win_rate_percentage"]) <= 100


def test_generic_backtest_trade_records(backtest_output):
    results = backtest_output["results"]

    for trade in results["trades"]:
        assert trade["entry_price"] is not None
        assert trade["exit_price"] is not None
        assert float(trade["entry_price"]) > 0
        assert float(trade["exit_price"]) > 0

        assert trade["exit_reason"] in {
            "stop_loss",
            "take_profit",
            "signal",
        }

        assert "net_pnl" in trade
        assert "gross_pnl" in trade


def test_generic_backtest_equity_curve(backtest_output):
    results = backtest_output["results"]
    equity_curve = results["equity_curve"]

    assert len(equity_curve) == backtest_output["candles_processed"]

    for point in equity_curve:
        assert float(point["equity"]) > 0
