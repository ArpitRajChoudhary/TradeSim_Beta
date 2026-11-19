
from strategy_schema import validate_strategy_schema
from indicators import calculate_indicators
from condition_engine import evaluate_condition_group


class ConditionBasedStrategy:
    """
    Generic strategy driven by indicator and condition definitions.

    Compatible with BacktestEngine's generate_signal() interface.
    """

    def __init__(self, candles, specification):
        validate_strategy_schema(specification)

        self.candles = candles
        self.specification = specification

        self.indicators = calculate_indicators(
            candles,
            specification["indicators"]
        )

    def generate_signal(self, candles, index):
        if index < 0 or index >= len(self.candles):
            return "HOLD"

        entry_met = evaluate_condition_group(
            self.specification["entry"],
            self.candles,
            self.indicators,
            index
        )

        exit_met = evaluate_condition_group(
            self.specification["exit"],
            self.candles,
            self.indicators,
            index
        )

        # Exit takes priority if both conditions are true.
        if exit_met:
            return "SELL"

        if entry_met:
            return "BUY"

        return "HOLD"
