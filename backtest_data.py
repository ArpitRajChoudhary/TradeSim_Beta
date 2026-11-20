
import csv
import json

from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path


@dataclass
class Candle:
    open_time: int
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal


def load_candles(file_path):
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {path}")

    candles = []

    with path.open("r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        required_columns = {
            "open_time",
            "open",
            "high",
            "low",
            "close",
            "volume",
        }

        if not required_columns.issubset(reader.fieldnames or []):
            raise ValueError("CSV is missing required OHLCV columns.")

        for row in reader:
            candle = Candle(
                open_time=int(row["open_time"]),
                open=Decimal(row["open"]),
                high=Decimal(row["high"]),
                low=Decimal(row["low"]),
                close=Decimal(row["close"]),
                volume=Decimal(row["volume"]),
            )

            if candle.low > candle.high:
                raise ValueError("Invalid candle: low exceeds high.")

            if not (
                candle.low <= candle.open <= candle.high
                and candle.low <= candle.close <= candle.high
            ):
                raise ValueError("Invalid candle OHLC values.")

            if candle.volume < 0:
                raise ValueError("Negative candle volume.")

            if candles and candle.open_time <= candles[-1].open_time:
                raise ValueError("Candles are not chronologically ordered.")

            candles.append(candle)

    if not candles:
        raise ValueError("No candles found in the dataset.")

    return candles


def download_binance_candles(
    start_date,
    end_date,
    output_path,
    symbol="BTCUSDT",
    interval="1h",
):
    """
    Download historical Binance Spot candles and save them as CSV.

    Dates use YYYY-MM-DD format.
    Both start_date and end_date are inclusive.
    All dates are interpreted as UTC.
    """

    if interval != "1h":
        raise ValueError("Only the 1h timeframe is currently supported.")

    symbol = symbol.strip().upper()

    if not symbol:
        raise ValueError("A trading symbol is required.")

    try:
        start = datetime.strptime(
            start_date, "%Y-%m-%d"
        ).replace(tzinfo=timezone.utc)

        end = datetime.strptime(
            end_date, "%Y-%m-%d"
        ).replace(tzinfo=timezone.utc)

    except (ValueError, TypeError):
        raise ValueError(
            "Dates must use YYYY-MM-DD format."
        )

    if start > end:
        raise ValueError("Start date cannot be after end date.")

    # Binance timestamps are in milliseconds.
    start_ms = int(start.timestamp() * 1000)

    # Include the entire end date.
    end_exclusive = end + timedelta(days=1)
    end_ms = int(end_exclusive.timestamp() * 1000) - 1

    base_url = "https://api.binance.com/api/v3/klines"

    candles = []
    current_start = start_ms

    while current_start <= end_ms:

        params = {
            "symbol": symbol,
            "interval": interval,
            "startTime": current_start,
            "endTime": end_ms,
            "limit": 1000,
        }

        url = f"{base_url}?{urlencode(params)}"

        request = Request(
            url,
            headers={"User-Agent": "TradeSim/1.0"},
        )

        try:
            with urlopen(request, timeout=30) as response:
                batch = json.loads(
                    response.read().decode("utf-8")
                )

        except HTTPError as error:
            details = error.read().decode(
                "utf-8", errors="replace"
            )
            raise RuntimeError(
                f"Binance HTTP {error.code}: {details}"
            ) from error

        except URLError as error:
            raise RuntimeError(
                f"Could not connect to Binance: {error.reason}"
            ) from error

        except TimeoutError as error:
            raise RuntimeError(
                "Binance historical data request timed out."
            ) from error

        if isinstance(batch, dict):
            raise RuntimeError(
                f"Binance API error: {batch}"
            )

        if not batch:
            break

        candles.extend(batch)

        # Move beyond the last downloaded candle.
        current_start = int(batch[-1][0]) + 1

    # Remove duplicates and keep only candles in the requested range.
    unique_candles = {
        int(row[0]): row
        for row in candles
        if start_ms <= int(row[0]) <= end_ms
    }

    sorted_candles = [
        unique_candles[timestamp]
        for timestamp in sorted(unique_candles)
    ]

    if not sorted_candles:
        raise ValueError(
            "Binance returned no historical candles for this date range."
        )

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open(
        "w", newline="", encoding="utf-8"
    ) as file:

        writer = csv.writer(file)

        writer.writerow([
            "open_time",
            "open",
            "high",
            "low",
            "close",
            "volume",
        ])

        for row in sorted_candles:
            writer.writerow([
                row[0],
                row[1],
                row[2],
                row[3],
                row[4],
                row[5],
            ])

    print(
        f"Downloaded {len(sorted_candles)} candles "
        f"for {symbol} ({interval})."
    )

    print(f"Saved dataset: {output_path.resolve()}")

    return output_path







if __name__ == "__main__":
    download_binance_candles(
        start_date="2025-01-01",
        end_date="2025-01-07",
        output_path="data/historical/test_download.csv",
    )

    candles = load_candles(
        "data/historical/test_download.csv"
    )

    print("Verified candle count:", len(candles))
    print("First candle:", candles[0])
    print("Last candle:", candles[-1])