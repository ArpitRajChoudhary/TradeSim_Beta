
from backtest_report import generate_backtest_report
from backtest_data import load_candles
from strategies import SmaCrossStrategy
from backtest_engine import BacktestEngine


def main():

    candles = load_candles(
        "data/historical/BTCUSDT_spot_1h.csv"
    )

    strategy = SmaCrossStrategy(
        fast_period=5,
        slow_period=20,
    )

    engine = BacktestEngine(
        initial_capital="20000",
        quote_per_trade="1000",
        fee_percentage_per_side="0.1",
        slippage_bps="5",
    )

    result = engine.run(
        candles=candles,
        strategy=strategy,
    )

    generate_backtest_report(result)


if __name__ == "__main__":
    main()
