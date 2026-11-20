
import math
from typing import Any

from indicators import (
    validate_indicator_definition,
    validate_indicator_output,
)


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
    indicator_types = {}

    # Validate each indicator using the central capability registry.
    for indicator in strategy["indicators"]:
        if not isinstance(indicator, dict):
            raise ValueError("Invalid indicator definition.")

        indicator_id = indicator.get("id")

        if (
            not isinstance(indicator_id, str)
            or not indicator_id.strip()
            or indicator_id in indicator_ids
        ):
            raise ValueError("Missing or duplicate indicator id.")

        validate_indicator_definition(indicator)

        indicator_ids.add(indicator_id)
        indicator_types[indicator_id] = indicator["type"].lower()

    validate_condition_group(strategy["entry"])
    validate_condition_group(strategy["exit"])

    # Verify indicator references and their supported outputs.
    for group_name in ("entry", "exit"):
        group = strategy[group_name]

        for condition in group["conditions"]:
            for side in ("left", "right"):
                operand = condition[side]

                if operand["source"] == "indicator":
                    indicator_id = operand["id"]

                    if indicator_id not in indicator_ids:
                        raise ValueError(
                            f"Undefined indicator: {indicator_id}"
                        )

                    validate_indicator_output(
                        indicator_types[indicator_id],
                        operand["output"],
                    )
