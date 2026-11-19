
from decimal import Decimal

from backtest_data import Candle
from indicators import calculate_indicators


candles = [
    Candle(
        open_time=i,
        open=Decimal(str(price)),
        high=Decimal(str(price + 1)),
        low=Decimal(str(price - 1)),
        close=Decimal(str(price)),
        volume=Decimal("100")
    )
    for i, price in enumerate(
        [10, 11, 12, 13, 14, 15, 14, 13, 12, 11, 10, 11, 12, 13, 14, 15]
    )
]


definitions = [
    {
        "id": "rsi_14",
        "type": "rsi",
        "parameters": {"period": 14}
    },
    {
        "id": "sma_5",
        "type": "sma",
        "parameters": {"period": 5}
    },
    {
        "id": "ema_5",
        "type": "ema",
        "parameters": {"period": 5}
    }
]


results = calculate_indicators(candles, definitions)

for indicator_id, outputs in results.items():
    print(f"\n{indicator_id}")

    for output_name, values in outputs.items():
        print(f"{output_name}: {values}")


assert len(results["rsi_14"]["value"]) == len(candles)
assert len(results["sma_5"]["value"]) == len(candles)
assert len(results["ema_5"]["value"]) == len(candles)

assert results["rsi_14"]["value"][13] is None
assert results["rsi_14"]["value"][14] is not None

assert isinstance(
    results["rsi_14"]["value"][14],
    Decimal
)

print("\nIndicator tests passed.")
