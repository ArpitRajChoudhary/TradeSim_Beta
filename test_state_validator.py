
import unittest

from state_validator import validate_trading_state


class TestStateValidator(unittest.TestCase):

    def setUp(self):
        self.valid_state = {
            "asset": "Bitcoin",
            "capital": 20000,
            "capital_currency": "USDT",
            "risk_percentage": 2,
            "risk_amount": None,
            "entry_price": 90000,
            "stop_loss": 88200,
            "price_currency": "USDT",
            "strategy_type": None,
            "backtest_period": None,
            "entry_condition": None,
            "exit_condition": None,
        }

    def test_valid_complete_state(self):
        valid, message = validate_trading_state(self.valid_state)
        self.assertTrue(valid)

    def test_valid_partial_state(self):
        state = {"asset": "Bitcoin", "capital": 10000}
        valid, message = validate_trading_state(
            state, require_complete=False
        )
        self.assertTrue(valid)

    def test_negative_capital(self):
        state = self.valid_state.copy()
        state["capital"] = -1000
        valid, message = validate_trading_state(state)
        self.assertFalse(valid)

    def test_zero_capital(self):
        state = self.valid_state.copy()
        state["capital"] = 0
        valid, message = validate_trading_state(state)
        self.assertFalse(valid)

    def test_risk_above_limit(self):
        state = self.valid_state.copy()
        state["risk_percentage"] = 6
        valid, message = validate_trading_state(state)
        self.assertFalse(valid)

    def test_zero_risk(self):
        state = self.valid_state.copy()
        state["risk_percentage"] = 0
        valid, message = validate_trading_state(state)
        self.assertFalse(valid)

    def test_negative_entry_price(self):
        state = self.valid_state.copy()
        state["entry_price"] = -90000
        valid, message = validate_trading_state(state)
        self.assertFalse(valid)

    def test_zero_stop_loss(self):
        state = self.valid_state.copy()
        state["stop_loss"] = 0
        valid, message = validate_trading_state(state)
        self.assertFalse(valid)

    def test_stop_loss_above_entry(self):
        state = self.valid_state.copy()
        state["stop_loss"] = 91000
        valid, message = validate_trading_state(state)
        self.assertFalse(valid)

    def test_missing_required_fields(self):
        state = {"asset": "Bitcoin"}
        valid, message = validate_trading_state(state)
        self.assertFalse(valid)

    def test_boolean_capital(self):
        state = self.valid_state.copy()
        state["capital"] = True
        valid, message = validate_trading_state(state)
        self.assertFalse(valid)

    def test_infinite_capital(self):
        state = self.valid_state.copy()
        state["capital"] = float("inf")
        valid, message = validate_trading_state(state)
        self.assertFalse(valid)


if __name__ == "__main__":
    unittest.main()
