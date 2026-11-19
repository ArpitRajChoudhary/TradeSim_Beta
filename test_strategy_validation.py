
import pytest

from ai_backtest import validate_strategy


def base_config():
    return {
        "asset": "BTCUSDT",
        "market_type": "spot",
        "timeframe": "1h",
        "initial_capital": 20000,
        "quote_per_trade": 1000,
        "fee_percentage_per_side": 0.1,
        "slippage_bps": 5,
        "stop_loss_percentage": 2,
        "take_profit_percentage": 4,
    }


def test_valid_sma_crossover():

    config = base_config()

    config.update({
        "strategy_type": "sma_crossover",
        "fast_period": 10,
        "slow_period": 30,
    })

    result = validate_strategy(config)

    assert result["strategy_type"] == "sma_crossover"
    assert result["fast_period"] == 10
    assert result["slow_period"] == 30


def test_valid_rsi_strategy():

    config = base_config()

    config.update({
        "strategy_type": "condition_based",

        "indicators": [
            {
                "id": "rsi14",
                "type": "rsi",
                "parameters": {
                    "period": 14,
                },
            }
        ],

        "entry": {
            "operator": "AND",
            "conditions": [
                {
                    "left": {
                        "source": "indicator",
                        "id": "rsi14",
                        "output": "value",
                    },
                    "comparison": "less_than",
                    "right": {
                        "source": "constant",
                        "value": 30,
                    },
                }
            ],
        },

        "exit": {
            "operator": "AND",
            "conditions": [
                {
                    "left": {
                        "source": "indicator",
                        "id": "rsi14",
                        "output": "value",
                    },
                    "comparison": "greater_than",
                    "right": {
                        "source": "constant",
                        "value": 60,
                    },
                }
            ],
        },
    })

    result = validate_strategy(config)

    assert result["strategy_type"] == "condition_based"
    assert result["indicators"][0]["type"] == "rsi"
    assert result["indicators"][0]["parameters"]["period"] == 14


def test_invalid_sma_periods():

    config = base_config()

    config.update({
        "strategy_type": "sma_crossover",
        "fast_period": 30,
        "slow_period": 10,
    })

    with pytest.raises(ValueError):
        validate_strategy(config)


def test_unsupported_timeframe():

    config = base_config()

    config.update({
        "strategy_type": "sma_crossover",
        "fast_period": 10,
        "slow_period": 30,
        "timeframe": "15m",
    })

    with pytest.raises(ValueError):
        validate_strategy(config)


def test_unsupported_indicator():

    config = base_config()

    config.update({
        "strategy_type": "condition_based",
        "indicators": [
            {
                "id": "test",
                "type": "macd",
                "parameters": {
                    "period": 14,
                },
            }
        ],
        "entry": {
            "operator": "AND",
            "conditions": [
                {
                    "left": {
                        "source": "indicator",
                        "id": "test",
                        "output": "value",
                    },
                    "comparison": "less_than",
                    "right": {
                        "source": "constant",
                        "value": 30,
                    },
                }
            ],
        },
        "exit": {
            "operator": "AND",
            "conditions": [
                {
                    "left": {
                        "source": "indicator",
                        "id": "test",
                        "output": "value",
                    },
                    "comparison": "greater_than",
                    "right": {
                        "source": "constant",
                        "value": 60,
                    },
                }
            ],
        },
    })

    with pytest.raises(ValueError):
        validate_strategy(config)
