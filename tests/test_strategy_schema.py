
from strategy_schema import validate_strategy_schema


strategy = {
    "asset": "BTCUSDT",
    "timeframe": "15m",

    "indicators": [
        {
            "id": "rsi_14",
            "type": "RSI",
            "parameters": {"period": 14}
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
        "operator": "OR",
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


validate_strategy_schema(strategy)

print("Strategy schema validation passed.")
