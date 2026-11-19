
import pytest

from strategy_schema import validate_operand


def test_valid_volume_operand():
    validate_operand({"source": "volume"})


def test_valid_finite_constant():
    validate_operand({"source": "constant", "value": 30})


@pytest.mark.parametrize(
    "value",
    [
        float("nan"),
        float("inf"),
        float("-inf"),
        True,
        False,
    ],
)
def test_invalid_constant_values(value):
    with pytest.raises(ValueError):
        validate_operand({
            "source": "constant",
            "value": value,
        })


def test_invalid_volume_source():
    with pytest.raises(ValueError):
        validate_operand({"source": "volumes"})


def test_invalid_price_field():
    with pytest.raises(ValueError):
        validate_operand({
            "source": "price",
            "field": "volume",
        })


def test_invalid_indicator_reference():
    with pytest.raises(ValueError):
        validate_operand({
            "source": "indicator",
            "id": "",
            "output": "value",
        })
