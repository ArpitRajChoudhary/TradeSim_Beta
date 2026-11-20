
import json
import tempfile
import unittest

from pathlib import Path

from state_manager import (
    save_state,
    load_state,
    reset_saved_state,
)


def create_empty_state():
    return {
        "asset": None,
        "strategy_type": None,
        "capital": None,
        "capital_currency": None,
        "risk_percentage": None,
        "risk_amount": None,
        "entry_price": None,
        "stop_loss": None,
        "price_currency": None,
        "backtest_period": None,
        "entry_condition": None,
        "exit_condition": None,
    }


class TestStateManager(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.file_path = Path(self.temp_dir.name) / "trading_state.json"

        self.valid_state = create_empty_state()
        self.valid_state.update({
            "asset": "Bitcoin",
            "capital": 20000,
            "capital_currency": "USDT",
            "risk_percentage": 2,
            "entry_price": 90000,
            "stop_loss": 88200,
            "price_currency": "USDT",
        })

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_save_and_load_state(self):
        save_state(self.valid_state, self.file_path)

        restored, message = load_state(
            create_empty_state(),
            self.file_path
        )

        self.assertEqual(restored, self.valid_state)
        self.assertTrue(self.file_path.exists())

    def test_invalid_state_is_not_saved(self):
        invalid_state = self.valid_state.copy()
        invalid_state["capital"] = -1000

        with self.assertRaises(ValueError):
            save_state(invalid_state, self.file_path)

        self.assertFalse(self.file_path.exists())

    def test_missing_file_returns_empty_state(self):
        restored, message = load_state(
            create_empty_state(),
            self.file_path
        )

        self.assertEqual(restored, create_empty_state())

    def test_corrupt_file_is_not_loaded(self):
        self.file_path.write_text(
            "{ invalid json",
            encoding="utf-8"
        )

        restored, message = load_state(
            create_empty_state(),
            self.file_path
        )

        self.assertEqual(restored, create_empty_state())
        self.assertTrue(self.file_path.exists())

    def test_unsupported_version_is_rejected(self):
        self.file_path.write_text(
            json.dumps({
                "version": 99,
                "state": self.valid_state,
            }),
            encoding="utf-8"
        )

        restored, message = load_state(
            create_empty_state(),
            self.file_path
        )

        self.assertEqual(restored, create_empty_state())

    def test_reset_saved_state(self):
        save_state(self.valid_state, self.file_path)

        reset_saved_state(self.file_path)

        self.assertFalse(self.file_path.exists())

    def test_invalid_saved_state_is_rejected(self):
        invalid_state = self.valid_state.copy()
        invalid_state["risk_percentage"] = 8

        self.file_path.write_text(
            json.dumps({
                "version": 1,
                "state": invalid_state,
            }),
            encoding="utf-8"
        )

        restored, message = load_state(
            create_empty_state(),
            self.file_path
        )

        self.assertEqual(restored, create_empty_state())
        self.assertTrue(self.file_path.exists())


if __name__ == "__main__":
    unittest.main()
