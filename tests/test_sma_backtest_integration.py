
from ai_backtest import validate_strategy, run_ai_backtest


def test_sma_backtest_runs_successfully():
    config = {
        "asset": "BTCUSDT",
        "market_type": "spot",
        "timeframe": "1h",
        "strategy_type": "sma_crossover",

        "fast_period": 10,
        "slow_period": 30,

        "initial_capital": 20000,
        "quote_per_trade": 1000,
        "fee_percentage_per_side": 0.1,
        "slippage_bps": 5,
        "stop_loss_percentage": 2,
        "take_profit_percentage": 4,
    }

    validated_config = validate_strategy(config)

    output = run_ai_backtest(
        validated_config,
        generate_report=False,
    )

    assert isinstance(output, dict)
    assert output["dataset"] == "BTCUSDT_spot_1h.csv"
    assert output["candles_processed"] > 0
    assert output["execution_time_seconds"] >= 0

    results = output["results"]

    assert results["initial_capital"] == "20000"
    assert isinstance(results["final_equity"], str)
    assert isinstance(results["total_pnl"], str)

    assert results["closed_trade_count"] >= 0
    assert (
        results["winning_trades"] + results["losing_trades"]
        == results["closed_trade_count"]
    )

    assert len(results["equity_curve"]) == output["candles_processed"]

    for trade in results["trades"]:
        assert float(trade["entry_price"]) > 0
        assert float(trade["exit_price"]) > 0
        assert trade["exit_reason"] in {
            "stop_loss",
            "take_profit",
            "signal",
        }
