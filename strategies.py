
from decimal import Decimal


class SmaCrossStrategy:

    def __init__(self, fast_period=5, slow_period=20):

        if fast_period <= 0 or slow_period <= 0:
            raise ValueError("SMA periods must be positive.")

        if fast_period >= slow_period:
            raise ValueError(
                "Fast SMA period must be smaller than slow SMA period."
            )

        self.fast_period = fast_period
        self.slow_period = slow_period

    def calculate_sma(self, candles, end_index, period):

        start_index = end_index - period + 1

        if start_index < 0:
            return None

        prices = [
            candles[i].close
            for i in range(start_index, end_index + 1)
        ]

        return sum(prices, Decimal("0")) / Decimal(period)

    def generate_signal(self, candles, index):

        if index < self.slow_period:
            return "HOLD"

        previous_fast = self.calculate_sma(
            candles,
            index - 1,
            self.fast_period
        )

        previous_slow = self.calculate_sma(
            candles,
            index - 1,
            self.slow_period
        )

        current_fast = self.calculate_sma(
            candles,
            index,
            self.fast_period
        )

        current_slow = self.calculate_sma(
            candles,
            index,
            self.slow_period
        )

        if (
            previous_fast <= previous_slow
            and current_fast > current_slow
        ):
            return "BUY"

        if (
            previous_fast >= previous_slow
            and current_fast < current_slow
        ):
            return "SELL"

        return "HOLD"
