
from decimal import Decimal


def get_operand_value(operand, candles, indicators, index):
    """Resolve an operand into its value at a candle index."""

    if index < 0 or index >= len(candles):
        return None

    source = operand["source"]

    if source == "constant":
        return Decimal(str(operand["value"]))

    if source == "price":
        field = operand["field"]
        return getattr(candles[index], field)

    if source == "volume":
        return candles[index].volume

    if source == "indicator":
        indicator_id = operand["id"]
        output = operand["output"]

        if indicator_id not in indicators:
            raise ValueError(f"Unknown indicator: {indicator_id}")

        if output not in indicators[indicator_id]:
            raise ValueError(
                f"Unknown output '{output}' for indicator '{indicator_id}'"
            )

        return indicators[indicator_id][output][index]

    raise ValueError(f"Unsupported operand source: {source}")


def evaluate_comparison(
    comparison,
    left_current,
    right_current,
    left_previous=None,
    right_previous=None
):
    """Evaluate a comparison between two values."""

    if left_current is None or right_current is None:
        return False

    if comparison == "greater_than":
        return left_current > right_current

    if comparison == "less_than":
        return left_current < right_current

    if comparison == "greater_than_or_equal":
        return left_current >= right_current

    if comparison == "less_than_or_equal":
        return left_current <= right_current

    if comparison == "equals":
        return left_current == right_current

    if comparison == "crosses_above":
        if left_previous is None or right_previous is None:
            return False

        return (
            left_previous <= right_previous
            and left_current > right_current
        )

    if comparison == "crosses_below":
        if left_previous is None or right_previous is None:
            return False

        return (
            left_previous >= right_previous
            and left_current < right_current
        )

    raise ValueError(f"Unsupported comparison: {comparison}")


def evaluate_condition(condition, candles, indicators, index):
    """Evaluate one condition at the given candle index."""

    left = condition["left"]
    right = condition["right"]

    left_current = get_operand_value(
        left, candles, indicators, index
    )

    right_current = get_operand_value(
        right, candles, indicators, index
    )

    comparison = condition["comparison"]

    if comparison in {"crosses_above", "crosses_below"}:
        left_previous = get_operand_value(
            left, candles, indicators, index - 1
        )

        right_previous = get_operand_value(
            right, candles, indicators, index - 1
        )
    else:
        left_previous = None
        right_previous = None

    return evaluate_comparison(
        comparison,
        left_current,
        right_current,
        left_previous,
        right_previous
    )


def evaluate_condition_group(group, candles, indicators, index):
    """Evaluate an AND/OR group of conditions."""

    results = [
        evaluate_condition(condition, candles, indicators, index)
        for condition in group["conditions"]
    ]

    if group["operator"] == "AND":
        return all(results)

    if group["operator"] == "OR":
        return any(results)

    raise ValueError(
        f"Unsupported logical operator: {group['operator']}"
    )
