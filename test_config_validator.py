
import unittest

from decimal import Decimal

from config_validator import validate_backtest_config


VALID_CONFIG = {
    "asset": "BTCUSDT",
    "market_type": "spot",
    "timeframe": "1h",
    "strategy_type": "sma_crossover",
    "fast_period": 3,
    "slow_period": 10,
    "initial_capital": 5000,
    "quote_per_trade": 500,
    "fee_percentage_per_side": 0.08,
    "slippage_bps": 10,
    "stop_loss_percentage": 1,
    "take_profit_percentage": 2,
}


class TestConfigValidator(unittest.TestCase):

    def test_valid_configuration(self):
        result = validate_backtest_config(VALID_CONFIG)

        self.assertEqual(result["asset"], "BTCUSDT")
        self.assertEqual(result["fast_period"], 3)
        self.assertEqual(result["slow_period"], 10)

    def test_defaults_are_applied(self):
        config = VALID_CONFIG.copy()

        for key in (
            "initial_capital",
            "quote_per_trade",
            "fee_percentage_per_side",
            "slippage_bps",
            "stop_loss_percentage",
            "take_profit_percentage",
        ):
            config[key] = None

        result = validate_backtest_config(config)

        self.assertEqual(
            result["initial_capital"],
            Decimal("20000"),
        )

        self.assertEqual(
            result["quote_per_trade"],
            Decimal("1000"),
        )

        self.assertEqual(
            result["fee_percentage_per_side"],
            Decimal("0.1"),
        )

    def test_trade_amount_exceeds_capital(self):
        config = VALID_CONFIG.copy()
        config["quote_per_trade"] = 6000

        with self.assertRaises(ValueError):
            validate_backtest_config(config)

    def test_zero_capital(self):
        config = VALID_CONFIG.copy()
        config["initial_capital"] = 0

        with self.assertRaises(ValueError):
            validate_backtest_config(config)

    def test_negative_trade_amount(self):
        config = VALID_CONFIG.copy()
        config["quote_per_trade"] = -100

        with self.assertRaises(ValueError):
            validate_backtest_config(config)

    def test_negative_fee(self):
        config = VALID_CONFIG.copy()
        config["fee_percentage_per_side"] = -1

        with self.assertRaises(ValueError):
            validate_backtest_config(config)

    def test_excessive_fee(self):
        config = VALID_CONFIG.copy()
        config["fee_percentage_per_side"] = 150

        with self.assertRaises(ValueError):
            validate_backtest_config(config)

    def test_negative_slippage(self):
        config = VALID_CONFIG.copy()
        config["slippage_bps"] = -10

        with self.assertRaises(ValueError):
            validate_backtest_config(config)

    def test_excessive_slippage(self):
        config = VALID_CONFIG.copy()
        config["slippage_bps"] = 50000

        with self.assertRaises(ValueError):
            validate_backtest_config(config)

    def test_zero_stop_loss(self):
        config = VALID_CONFIG.copy()
        config["stop_loss_percentage"] = 0

        with self.assertRaises(ValueError):
            validate_backtest_config(config)

    def test_stop_loss_100_percent(self):
        config = VALID_CONFIG.copy()
        config["stop_loss_percentage"] = 100

        with self.assertRaises(ValueError):
            validate_backtest_config(config)

    def test_zero_take_profit(self):
        config = VALID_CONFIG.copy()
        config["take_profit_percentage"] = 0

        with self.assertRaises(ValueError):
            validate_backtest_config(config)

    def test_fast_period_greater_than_slow(self):
        config = VALID_CONFIG.copy()
        config["fast_period"] = 20
        config["slow_period"] = 10

        with self.assertRaises(ValueError):
            validate_backtest_config(config)

    def test_non_integer_sma_period(self):
        config = VALID_CONFIG.copy()
        config["fast_period"] = 3.5

        with self.assertRaises(ValueError):
            validate_backtest_config(config)

    def test_boolean_is_not_a_number(self):
        config = VALID_CONFIG.copy()
        config["initial_capital"] = True

        with self.assertRaises(ValueError):
            validate_backtest_config(config)

    def test_infinite_capital(self):
        config = VALID_CONFIG.copy()
        config["initial_capital"] = float("inf")

        with self.assertRaises(ValueError):
            validate_backtest_config(config)

    def test_nan_fee(self):
        config = VALID_CONFIG.copy()
        config["fee_percentage_per_side"] = float("nan")

        with self.assertRaises(ValueError):
            validate_backtest_config(config)

    def test_unsupported_asset(self):
        config = VALID_CONFIG.copy()
        config["asset"] = "ETHUSDT"

        with self.assertRaises(ValueError):
            validate_backtest_config(config)


if __name__ == "__main__":
    unittest.main(verbosity=2)
