
import pytest

from indicators import (
    validate_indicator_definition,
    validate_indicator_output,
)


@pytest.mark.parametrize("indicator_type", ["sma", "ema", "rsi"])
def test_supported_indicators(indicator_type):
    result = validate_indicator_definition({
        "type": indicator_type,
        "parameters": {"period": 14},
    })

    assert result == indicator_type


def test_unsupported_indicator():
    with pytest.raises(ValueError):
        validate_indicator_definition({
            "type": "macd",
            "parameters": {"period": 14},
        })


def test_missing_parameter():
    with pytest.raises(ValueError):
        validate_indicator_definition({
            "type": "rsi",
            "parameters": {},
        })


def test_extra_parameter():
    with pytest.raises(ValueError):
        validate_indicator_definition({
            "type": "rsi",
            "parameters": {
                "period": 14,
                "smoothing": 5,
            },
        })


@pytest.mark.parametrize("period", [0, -1, True, 14.5])
def test_invalid_period(period):
    with pytest.raises(ValueError):
        validate_indicator_definition({
            "type": "rsi",
            "parameters": {"period": period},
        })


def test_supported_output():
    validate_indicator_output("rsi", "value")


def test_unsupported_output():
    with pytest.raises(ValueError):
        validate_indicator_output("rsi", "signal")


def test_unsupported_output_for_unknown_indicator():
    with pytest.raises(ValueError):
        validate_indicator_output("macd", "value")
