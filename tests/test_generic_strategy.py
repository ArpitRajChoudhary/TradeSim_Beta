
from decimal import Decimal

from backtest_data import Candle
from generic_strategy import ConditionBasedStrategy


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


specification = {
    "asset": "BTCUSDT",
    "timeframe": "1h",

    "indicators": [
        {
            "id": "rsi_14",
            "type": "rsi",
            "parameters": {
                "period": 14
            }
        }
    ],

    "entry": {
        "operator": "AND",
        "conditions": [
            {
                "left": {
                    "source": "indicator",
                    "id": "rsi_14",
                    "output": "value"
                },
                "comparison": "crosses_below",
                "right": {
                    "source": "constant",
                    "value": 30
                }
            }
        ]
    },

    "exit": {
        "operator": "AND",
        "conditions": [
            {
                "left": {
                    "source": "indicator",
                    "id": "rsi_14",
                    "output": "value"
                },
                "comparison": "crosses_above",
                "right": {
                    "source": "constant",
                    "value": 60
                }
            }
        ]
    }
}


strategy = ConditionBasedStrategy(candles, specification)

for index in range(len(candles)):
    signal = strategy.generate_signal(candles, index)

    print(
        f"Index: {index:2} | "
        f"RSI: {strategy.indicators['rsi_14']['value'][index]} | "
        f"Signal: {signal}"
    )

print("\nGeneric strategy adapter test passed.")
