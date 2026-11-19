
import csv
import json
import time

from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


SPOT_BASE_URL = "https://api.binance.com"
FUTURES_BASE_URL = "https://fapi.binance.com"

MAX_LIMIT = 1000
REQUEST_TIMEOUT = 20

SUPPORTED_INTERVALS = {
    "1m", "3m", "5m", "15m", "30m",
    "1h", "2h", "4h", "6h", "8h", "12h",
    "1d", "3d", "1w", "1M",
}

CSV_FIELDS = [
    "open_time",
    "open_time_utc",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "close_time",
    "close_time_utc",
    "quote_asset_volume",
    "number_of_trades",
    "taker_buy_base_volume",
    "taker_buy_quote_volume",
]


def parse_utc_time(value, field_name):
    """
    Convert an ISO-8601 timestamp into UTC milliseconds.

    Example:
        2026-11-09T00:00:00Z
    """

    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(
                value.strip().replace("Z", "+00:00")
            )
        except ValueError:
            raise ValueError(
                f"{field_name} must be a valid ISO-8601 timestamp."
            )
    else:
        raise ValueError(
            f"{field_name} must be a datetime or ISO-8601 string."
        )

    if parsed.tzinfo is None:
        raise ValueError(
            f"{field_name} must include a timezone. "
            "Use Z for UTC."
        )

    parsed = parsed.astimezone(timezone.utc)

    return int(parsed.timestamp() * 1000)


def milliseconds_to_utc(timestamp):
    return datetime.fromtimestamp(
        timestamp / 1000,
        tz=timezone.utc
    ).isoformat()


def request_klines(
    market_type,
    symbol,
    interval,
    start_time,
    end_time,
    limit=MAX_LIMIT,
):
    """Fetch one page of raw Binance kline data."""

    if market_type == "spot":
        base_url = SPOT_BASE_URL
        endpoint = "/api/v3/klines"

    elif market_type == "futures":
        base_url = FUTURES_BASE_URL
        endpoint = "/fapi/v1/klines"

    else:
        raise ValueError("Market type must be spot or futures.")

    params = {
        "symbol": symbol,
        "interval": interval,
        "startTime": start_time,
        "endTime": end_time,
        "limit": limit,
    }

    url = base_url + endpoint + "?" + urlencode(params)

    request = Request(
        url,
        headers={
            "User-Agent": "TradeSim-Historical-Data/1.0",
        },
    )

    try:
        with urlopen(
            request,
            timeout=REQUEST_TIMEOUT
        ) as response:
            data = json.loads(response.read().decode("utf-8"))

    except HTTPError as error:
        error_body = error.read().decode(
            "utf-8",
            errors="replace"
        )

        raise RuntimeError(
            f"Binance HTTP error {error.code}: {error_body}"
        )

    except URLError as error:
        raise RuntimeError(
            f"Could not connect to Binance: {error.reason}"
        )

    except TimeoutError:
        raise RuntimeError("Binance request timed out.")

    if not isinstance(data, list):
        raise RuntimeError(
            f"Unexpected Binance response: {data}"
        )

    return data


def normalize_candle(raw):
    """
    Convert Binance's 12-element kline array
    into a named dictionary.
    """

    if len(raw) < 12:
        raise ValueError("Incomplete Binance candle received.")

    open_time = int(raw[0])
    close_time = int(raw[6])

    return {
        "open_time": open_time,
        "open_time_utc": milliseconds_to_utc(open_time),

        "open": str(raw[1]),
        "high": str(raw[2]),
        "low": str(raw[3]),
        "close": str(raw[4]),
        "volume": str(raw[5]),

        "close_time": close_time,
        "close_time_utc": milliseconds_to_utc(close_time),

        "quote_asset_volume": str(raw[7]),
        "number_of_trades": int(raw[8]),
        "taker_buy_base_volume": str(raw[9]),
        "taker_buy_quote_volume": str(raw[10]),
    }


def validate_candles(candles):
    """Validate candle values and chronological ordering."""

    previous_open_time = None

    for candle in candles:
        open_price = float(candle["open"])
        high_price = float(candle["high"])
        low_price = float(candle["low"])
        close_price = float(candle["close"])
        volume = float(candle["volume"])

        if min(open_price, high_price, low_price, close_price) <= 0:
            raise ValueError("Candle contains a non-positive price.")

        if low_price > high_price:
            raise ValueError("Candle low is greater than its high.")

        if not (
            low_price <= open_price <= high_price
            and low_price <= close_price <= high_price
        ):
            raise ValueError("Candle OHLC values are inconsistent.")

        if volume < 0:
            raise ValueError("Candle volume cannot be negative.")

        if candle["close_time"] < candle["open_time"]:
            raise ValueError("Candle close time precedes open time.")

        if (
            previous_open_time is not None
            and candle["open_time"] <= previous_open_time
        ):
            raise ValueError(
                "Candles are duplicated or not chronologically ordered."
            )

        previous_open_time = candle["open_time"]

    return True


def fetch_historical_klines(
    symbol,
    market_type,
    interval,
    start_time,
    end_time,
    limit=MAX_LIMIT,
    drop_incomplete=True,
):
    """
    Download historical candles with pagination.

    start_time and end_time must be timezone-aware ISO-8601
    timestamps or timezone-aware datetime objects.

    Returned prices and volumes remain strings to preserve
    Binance's decimal precision.
    """

    symbol = symbol.upper().strip()
    market_type = market_type.lower().strip()

    if not symbol:
        raise ValueError("Symbol cannot be empty.")

    if interval not in SUPPORTED_INTERVALS:
        raise ValueError(
            f"Unsupported interval: {interval}"
        )

    if not 1 <= limit <= MAX_LIMIT:
        raise ValueError(
            f"Limit must be between 1 and {MAX_LIMIT}."
        )

    start_ms = parse_utc_time(start_time, "start_time")
    end_ms = parse_utc_time(end_time, "end_time")

    if start_ms >= end_ms:
        raise ValueError("Start time must be earlier than end time.")

    candles_by_open_time = {}
    next_start = start_ms

    while next_start <= end_ms:
        raw_data = request_klines(
            market_type=market_type,
            symbol=symbol,
            interval=interval,
            start_time=next_start,
            end_time=end_ms,
            limit=limit,
        )

        if not raw_data:
            break

        for raw in raw_data:
            candle = normalize_candle(raw)

            if not (
                start_ms <= candle["open_time"] <= end_ms
            ):
                continue

            if candle["close_time"] > end_ms:
                continue

            if drop_incomplete:
                current_time_ms = int(time.time() * 1000)

                if candle["close_time"] >= current_time_ms:
                    continue

            candles_by_open_time[candle["open_time"]] = candle

        last_close_time = int(raw_data[-1][6])

        next_start = last_close_time + 1

        if len(raw_data) < limit:
            break

        # Avoid hammering the public API.
        time.sleep(0.2)

    candles = sorted(
        candles_by_open_time.values(),
        key=lambda candle: candle["open_time"]
    )

    validate_candles(candles)

    return candles


def save_klines_csv(candles, output_path):
    """Save normalized candles as a CSV file."""

    if not candles:
        raise ValueError("Cannot save an empty candle dataset.")

    output_path = Path(output_path)
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with output_path.open(
        "w",
        newline="",
        encoding="utf-8"
    ) as csv_file:

        writer = csv.DictWriter(
            csv_file,
            fieldnames=CSV_FIELDS
        )

        writer.writeheader()
        writer.writerows(candles)

    return output_path


if __name__ == "__main__":
    print("Historical data module loaded successfully.")
