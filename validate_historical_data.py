
import csv
from decimal import Decimal
from pathlib import Path


DATA_DIR = Path("data/historical")

FILES = {
    "spot": DATA_DIR / "BTCUSDT_spot_1h.csv",
    "futures": DATA_DIR / "BTCUSDT_futures_1h.csv",
}

ONE_HOUR_MS = 60 * 60 * 1000


def load_csv(path):
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {path}")

    with path.open("r", newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def validate_dataset(name, candles):
    print(f"\n--- {name.upper()} DATASET ---")

    if not candles:
        raise ValueError("Dataset is empty.")

    timestamps = [
        int(candle["open_time"])
        for candle in candles
    ]

    if len(timestamps) != len(set(timestamps)):
        raise ValueError("Duplicate candle timestamps found.")

    if timestamps != sorted(timestamps):
        raise ValueError("Candles are not chronologically ordered.")

    missing_candles = []

    for previous, current in zip(timestamps, timestamps[1:]):
        difference = current - previous

        if difference > ONE_HOUR_MS:
            missing_count = difference // ONE_HOUR_MS - 1

            missing_candles.append({
                "after": previous,
                "before": current,
                "count": missing_count,
            })

        elif difference < ONE_HOUR_MS:
            raise ValueError("Unexpected candle interval detected.")

    for candle in candles:
        open_price = Decimal(candle["open"])
        high_price = Decimal(candle["high"])
        low_price = Decimal(candle["low"])
        close_price = Decimal(candle["close"])
        volume = Decimal(candle["volume"])

        if not (
            low_price <= open_price <= high_price
            and low_price <= close_price <= high_price
        ):
            raise ValueError("Invalid OHLC values.")

        if volume < 0:
            raise ValueError("Negative volume detected.")

    print("Total candles:", len(candles))
    print("First timestamp:", candles[0]["open_time_utc"])
    print("Last timestamp:", candles[-1]["open_time_utc"])
    print("Duplicate timestamps: 0")
    print("Chronological ordering: VALID")
    print("OHLC values: VALID")
    print("Volume values: VALID")

    if missing_candles:
        print("Missing hourly intervals:", len(missing_candles))

        for gap in missing_candles[:10]:
            print(
                f"Gap: {gap['count']} candle(s) "
                f"between {gap['after']} and {gap['before']}"
            )

        if len(missing_candles) > 10:
            print("Additional gaps omitted from display.")

    else:
        print("Missing hourly intervals: 0")

    return set(timestamps), missing_candles


def main():
    datasets = {}

    for market, path in FILES.items():
        candles = load_csv(path)

        timestamps, gaps = validate_dataset(
            market,
            candles
        )

        datasets[market] = timestamps

    print("\n--- SPOT VS FUTURES COMPARISON ---")

    spot_times = datasets["spot"]
    futures_times = datasets["futures"]

    common = spot_times & futures_times

    print("Spot candles:", len(spot_times))
    print("Futures candles:", len(futures_times))
    print("Matching timestamps:", len(common))
    print("Spot-only timestamps:", len(spot_times - futures_times))
    print("Futures-only timestamps:", len(futures_times - spot_times))

    if spot_times == futures_times:
        print("Timestamp alignment: PASSED")
    else:
        print("Timestamp alignment: DIFFERENCES FOUND")

    print("\nDATASET VALIDATION COMPLETED.")


if __name__ == "__main__":
    main()
