
from datetime import datetime, timezone

from backtest_data import load_candles
from strategies import SmaCrossStrategy


from ai_backtest import interpret_strategy

tests = [
    "Create a Bitcoin SMA crossover strategy using SMA 10 and SMA 30.",
    
    "Buy Bitcoin when RSI 14 goes below 25 and exit when RSI goes above 70.",
    
    "Buy when EMA 9 crosses above EMA 21 and MACD is positive. Exit when EMA 9 crosses below EMA 21.",
    
    "Buy when Bitcoin breaks above the highest price of the previous 20 candles, with volume at least twice its 20-period average."
]

for i, prompt in enumerate(tests, 1):
    print(f"\n{'=' * 60}")
    print(f"TEST {i}: {prompt}")
    print("=" * 60)

    try:
        result = interpret_strategy(prompt)
        print(result)
    except Exception as e:
        print("ERROR:", str(e))



def main():

    candles = load_candles(
        "data/historical/BTCUSDT_spot_1h.csv"
    )

    strategy = SmaCrossStrategy(
        fast_period=5,
        slow_period=20,
    )

    print("DATASET:", len(candles), "candles")
    print("STRATEGY: SMA 5/20 crossover")
    print("\nGENERATED SIGNALS:\n")

    signal_count = 0

    for index in range(len(candles)):

        signal = strategy.generate_signal(
            candles,
            index
        )

        if signal != "HOLD":

            candle_time = datetime.fromtimestamp(
                candles[index].open_time / 1000,
                tz=timezone.utc
            )

            print(
                f"{candle_time.isoformat()} | "
                f"Close: {candles[index].close} | "
                f"Signal: {signal}"
            )

            signal_count += 1

    print("\nTOTAL SIGNALS:", signal_count)
    print("STRATEGY TEST COMPLETED.")


if __name__ == "__main__":
    main()
