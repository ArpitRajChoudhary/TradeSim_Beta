
import unittest

from calculator import calculate_trade_size


SYNTHETIC_RULES = {
    "exchange": "Binance",
    "market_type": "spot",
    "symbol": "BTCUSDT",
    "status": "TRADING",
    "base_asset": "BTC",
    "quote_asset": "USDT",
    "order_type": "MARKET",
    "step_size": "0.00001000",
    "min_qty": "0.00001000",
    "max_qty": "9000",
    "min_notional": "5",
    "max_notional": "9000000",
    "min_notional_applies_to_market": True,
    "max_notional_applies_to_market": False,
    "tick_size": "0.01",
}


class TestCurrencyValidation(unittest.TestCase):

    def calculate(self, capital_currency):
        return calculate_trade_size(
            capital=20000,
            risk_percentage=2,
            entry_price=90000,
            stop_loss=88200,
            capital_currency=capital_currency,
            rules=SYNTHETIC_RULES,
            side="long",
            fee_percentage_per_side="0.1",
            slippage_bps="5",
        )

    def test_matching_currency_is_accepted(self):
        result = self.calculate("USDT")

        self.assertEqual(result["status"], "success")

    def test_mismatched_currency_is_rejected(self):
        with self.assertRaises(ValueError):
            self.calculate("INR")

    def test_usd_is_not_silently_treated_as_usdt(self):
        with self.assertRaises(ValueError):
            self.calculate("USD")


if __name__ == "__main__":
    unittest.main()
