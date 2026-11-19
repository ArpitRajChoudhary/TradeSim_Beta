import math
from typing import Any
from typing import Any


SUPPORTED_OPERATORS = {
    "AND",
    "OR",
}

SUPPORTED_COMPARISONS = {
    "greater_than",
    "less_than",
    "greater_than_or_equal",
    "less_than_or_equal",
    "equals",
    "crosses_above",
    "crosses_below",
}

SUPPORTED_SOURCES = {
    "indicator",
    "price",
    "constant",
    "volume",
}



def validate_operand(operand: dict[str, Any]) -> None:
    if not isinstance(operand, dict):
        raise ValueError("Condition operand must be an object.")

    source = operand.get("source")

    if not isinstance(source, str) or source not in SUPPORTED_SOURCES:
        raise ValueError(f"Unsupported operand source: {source}")

    if source == "indicator":
        if not isinstance(operand.get("id"), str) or not operand["id"].strip():
            raise ValueError("Indicator operand requires a valid id.")

        if not isinstance(operand.get("output"), str) or not operand["output"].strip():
            raise ValueError("Indicator operand requires a valid output.")

    elif source == "price":
        if operand.get("field") not in {
            "open", "high", "low", "close"
        }:
            raise ValueError("Invalid price field.")

    elif source == "constant":
        value = operand.get("value")

        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
        ):
            raise ValueError(
                "Constant operand requires a finite number."
            )

    elif source == "volume":
        # Volume directly resolves to the candle's volume value.
        # No additional field or parameter is required.
        pass


def validate_condition_group(group: dict[str, Any]) -> None:
    if not isinstance(group, dict):
        raise ValueError("Condition group must be an object.")

    operator = group.get("operator")

    if operator not in SUPPORTED_OPERATORS:
        raise ValueError(f"Unsupported logical operator: {operator}")

    conditions = group.get("conditions")

    if not isinstance(conditions, list) or not conditions:
        raise ValueError("Condition group cannot be empty.")

    for condition in conditions:
        if not isinstance(condition, dict):
            raise ValueError("Invalid condition.")

        validate_operand(condition.get("left"))

        comparison = condition.get("comparison")

        if comparison not in SUPPORTED_COMPARISONS:
            raise ValueError(
                f"Unsupported comparison: {comparison}"
            )

        validate_operand(condition.get("right"))


def validate_strategy_schema(strategy: dict[str, Any]) -> None:
    if not isinstance(strategy, dict):
        raise ValueError("Strategy must be an object.")

    required_fields = {
        "asset",
        "timeframe",
        "indicators",
        "entry",
        "exit",
    }

    missing = required_fields - strategy.keys()

    if missing:
        raise ValueError(
            f"Missing strategy fields: {', '.join(sorted(missing))}"
        )

    if not isinstance(strategy["indicators"], list):
        raise ValueError("Indicators must be a list.")

    indicator_ids = set()

    for indicator in strategy["indicators"]:
        if not isinstance(indicator, dict):
            raise ValueError("Invalid indicator definition.")

        indicator_id = indicator.get("id")

        if not indicator_id or indicator_id in indicator_ids:
            raise ValueError("Missing or duplicate indicator id.")

        if not isinstance(indicator.get("parameters"), dict):
            raise ValueError("Indicator parameters must be an object.")

        indicator_ids.add(indicator_id)

    validate_condition_group(strategy["entry"])
    validate_condition_group(strategy["exit"])

    # Verify that every referenced indicator exists.
    for group_name in ("entry", "exit"):
        group = strategy[group_name]

        for condition in group["conditions"]:
            for side in ("left", "right"):
                operand = condition[side]

                if (
                    operand["source"] == "indicator"
                    and operand["id"] not in indicator_ids
                ):
                    raise ValueError(
                        f"Undefined indicator: {operand['id']}"
                    )
