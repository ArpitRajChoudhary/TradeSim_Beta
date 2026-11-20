
from decimal import Decimal

from backtest_data import Candle
from indicators import calculate_indicators
from condition_engine import evaluate_condition_group


prices = [
    10, 11, 12, 13, 14, 15, 14, 13,
    12, 11, 10, 11, 12, 13, 14, 15
]

candles = [
    Candle(
        open_time=i,
        open=Decimal(str(price)),
        high=Decimal(str(price + 1)),
        low=Decimal(str(price - 1)),
        close=Decimal(str(price)),
        volume=Decimal("100")
    )
    for i, price in enumerate(prices)
]

indicators = calculate_indicators(
    candles,
    [
        {
            "id": "rsi_14",
            "type": "rsi",
            "parameters": {"period": 14}
        }
    ]
)


entry_condition = {
    "operator": "AND",
    "conditions": [
        {
            "left": {
                "source": "indicator",
                "id": "rsi_14",
                "output": "value"
            },
            "comparison": "less_than",
            "right": {
                "source": "constant",
                "value": 30
            }
        }
    ]
}


exit_condition = {
    "operator": "AND",
    "conditions": [
        {
            "left": {
                "source": "indicator",
                "id": "rsi_14",
                "output": "value"
            },
            "comparison": "greater_than",
            "right": {
                "source": "constant",
                "value": 60
            }
        }
    ]
}


entry_result = evaluate_condition_group(
    entry_condition, candles, indicators, 14
)

exit_result = evaluate_condition_group(
    exit_condition, candles, indicators, 14
)

print("RSI at index 14:", indicators["rsi_14"]["value"][14])
print("Entry condition:", entry_result)
print("Exit condition:", exit_result)

assert entry_result is False
assert exit_result is True

print("\nCondition engine tests passed.")
