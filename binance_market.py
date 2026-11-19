
import hashlib
import hmac
import json
import os
import time

from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from dotenv import load_dotenv


load_dotenv()

SPOT_BASE_URL = "https://api.binance.com"
FUTURES_BASE_URL = "https://fapi.binance.com"


def _get_json(url, headers=None):
    request = Request(
        url,
        headers=headers or {"User-Agent": "TradeSim/1.0"},
    )

    try:
        with urlopen(request, timeout=15) as response:
            return json.loads(response.read().decode("utf-8"))

    except HTTPError as error:
        details = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"Binance returned HTTP {error.code}: {details}"
        ) from error

    except URLError as error:
        raise RuntimeError(
            f"Could not connect to Binance: {error.reason}"
        ) from error

    except TimeoutError as error:
        raise RuntimeError("Binance request timed out.") from error


def get_symbol_rules(symbol, market_type="spot", order_type="MARKET"):
    """
    Fetch public Binance trading rules for a symbol.

    market_type: spot or futures
    order_type: MARKET or LIMIT
    """

    symbol = symbol.strip().upper()
    market_type = market_type.strip().lower()
    order_type = order_type.strip().upper()

    if not symbol:
        raise ValueError("A Binance symbol is required.")

    if market_type not in ("spot", "futures"):
        raise ValueError("market_type must be spot or futures.")

    if order_type not in ("MARKET", "LIMIT"):
        raise ValueError("order_type must be MARKET or LIMIT.")

    if market_type == "spot":
        url = f"{SPOT_BASE_URL}/api/v3/exchangeInfo?symbol={symbol}"
    else:
        url = f"{FUTURES_BASE_URL}/fapi/v1/exchangeInfo?symbol={symbol}"

    data = _get_json(url)
    symbols = data.get("symbols", [])

    if not symbols:
        raise ValueError(
            f"{symbol} was not found on Binance {market_type}."
        )

    symbol_data = symbols[0]

    status = symbol_data.get(
        "status",
        symbol_data.get("contractStatus"),
    )

    if status != "TRADING":
        raise ValueError(
            f"{symbol} is not currently trading. Status: {status}"
        )

    filters = {
        item["filterType"]: item
        for item in symbol_data.get("filters", [])
    }

    # Select quantity rules for the requested order type.
    if order_type == "MARKET":
        lot_filter = filters.get("MARKET_LOT_SIZE")
    else:
        lot_filter = filters.get("LOT_SIZE")

    # A zero step size means that this filter is not active.
    if (
        not lot_filter
        or float(lot_filter.get("stepSize", "0")) <= 0
    ):
        lot_filter = filters.get("LOT_SIZE")

    if not lot_filter:
        raise ValueError("Binance did not return quantity rules.")

    step_size = lot_filter.get("stepSize", "0")

    if float(step_size) <= 0:
        raise ValueError("Binance returned an invalid quantity step.")

    # Preserve the filter's actual market applicability flags.
    notional_filter = (
        filters.get("NOTIONAL")
        or filters.get("MIN_NOTIONAL")
    )

    min_notional = "0"
    max_notional = "0"
    min_applies_to_market = None
    max_applies_to_market = None
    avg_price_mins = None

    if notional_filter:
        min_notional = notional_filter.get(
            "minNotional",
            notional_filter.get("notional", "0"),
        )

        max_notional = notional_filter.get(
            "maxNotional",
            "0",
        )

        avg_price_mins = notional_filter.get("avgPriceMins")

        if notional_filter["filterType"] == "MIN_NOTIONAL":
            min_applies_to_market = notional_filter.get(
                "applyToMarket"
            )

        elif notional_filter["filterType"] == "NOTIONAL":
            min_applies_to_market = notional_filter.get(
                "applyMinToMarket"
            )
            max_applies_to_market = notional_filter.get(
                "applyMaxToMarket"
            )

    price_filter = filters.get("PRICE_FILTER", {})

    return {
        "exchange": "Binance",
        "market_type": market_type,
        "symbol": symbol_data["symbol"],
        "status": status,
        "base_asset": symbol_data.get("baseAsset"),
        "quote_asset": symbol_data.get("quoteAsset"),
        "order_type": order_type,
        "step_size": step_size,
        "min_qty": lot_filter.get("minQty", "0"),
        "max_qty": lot_filter.get("maxQty", "0"),
        "min_notional": min_notional,
        "max_notional": max_notional,
        "min_notional_applies_to_market": min_applies_to_market,
        "max_notional_applies_to_market": max_applies_to_market,
        "notional_avg_price_minutes": avg_price_mins,
        "tick_size": price_filter.get("tickSize", "0"),
    }


def get_leverage_brackets(symbol):
    """
    Fetch account-specific USD-M Futures leverage brackets.

    Requires a Binance API key and secret in the local .env file.
    This endpoint is signed USER_DATA access. It does not place orders.
    """

    api_key = os.getenv("BINANCE_API_KEY")
    api_secret = os.getenv("BINANCE_API_SECRET")

    if not api_key or not api_secret:
        raise RuntimeError(
            "Futures leverage brackets require BINANCE_API_KEY "
            "and BINANCE_API_SECRET in your local .env file."
        )

    symbol = symbol.strip().upper()

    params = {
        "symbol": symbol,
        "timestamp": int(time.time() * 1000),
        "recvWindow": 5000,
    }

    query_string = urlencode(params)

    signature = hmac.new(
        api_secret.encode("utf-8"),
        query_string.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    url = (
        f"{FUTURES_BASE_URL}/fapi/v1/leverageBracket?"
        f"{query_string}&signature={signature}"
    )

    headers = {
        "X-MBX-APIKEY": api_key,
        "User-Agent": "TradeSim/1.0",
    }

    data = _get_json(url, headers=headers)

    # Binance may return a list or a single symbol object.
    if isinstance(data, list):
        matching = [
            item for item in data
            if item.get("symbol") == symbol
        ]

        if not matching:
            raise ValueError(
                f"No leverage brackets returned for {symbol}."
            )

        data = matching[0]

    if data.get("symbol") != symbol:
        raise ValueError(
            f"Unexpected leverage bracket response for {symbol}."
        )

    brackets = data.get("brackets", [])

    if not brackets:
        raise ValueError(
            f"No maintenance-margin brackets returned for {symbol}."
        )

    return {
        "symbol": symbol,
        "notional_coefficient": data.get("notionalCoef", "1"),
        "brackets": brackets,
    }


if __name__ == "__main__":
    rules = get_symbol_rules(
        symbol="BTCUSDT",
        market_type="spot",
        order_type="MARKET",
    )

    print("\nBINANCE MARKET RULES")

    for key, value in rules.items():
        print(f"{key}: {value}")
