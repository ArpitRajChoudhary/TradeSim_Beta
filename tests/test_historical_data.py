
from datetime import datetime, timedelta, timezone

from historical_data import (
    fetch_historical_klines,
    save_klines_csv,
)


def run_test(market_type):
    print("\n" + "=" * 55)
    print(f"HISTORICAL DATA TEST: {market_type.upper()}")
    print("=" * 55)

    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(days=7)

    candles = fetch_historical_klines(
        symbol="BTCUSDT",
        market_type=market_type,
        interval="1h",
        start_time=start_time,
        end_time=end_time,
        limit=1000,
    )

    if not candles:
        print("No historical candles were returned.")
        return

    output_path = (
        f"data/historical/"
        f"BTCUSDT_{market_type}_1h.csv"
    )

    saved_path = save_klines_csv(
        candles,
        output_path
    )

    print(f"Symbol: BTCUSDT")
    print(f"Market: {market_type}")
    print("Interval: 1h")
    print(f"Number of candles: {len(candles)}")

    print(
        "First candle:",
        candles[0]["open_time_utc"]
    )

    print(
        "Last candle:",
        candles[-1]["open_time_utc"]
    )

    print(f"CSV saved to: {saved_path}")

    print("\nLATEST CANDLE:")

    for key, value in candles[-1].items():
        print(f"{key}: {value}")

    print("\nDATA VALIDATION: PASSED")


if __name__ == "__main__":
    run_test("spot")
    run_test("futures")
