
import csv

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
