
from calculator import calculate_trade_size


SYNTHETIC_RULES = {
    "exchange": "Binance",
    "market_type": "futures",
    "symbol": "BTCUSDT",
    "status": "TRADING",
    "base_asset": "BTC",
    "quote_asset": "USDT",
    "order_type": "MARKET",
    "step_size": "0.001",
    "min_qty": "0.001",
    "max_qty": "120",
    "min_notional": "50",
    "max_notional": "0",
    "min_notional_applies_to_market": None,
    "max_notional_applies_to_market": None,
}


SYNTHETIC_BRACKETS = {
    "symbol": "BTCUSDT",
    "brackets": [
        {
            "bracket": 1,
            "initialLeverage": 125,
            "notionalFloor": "0",
            "notionalCap": "50000",
            "maintMarginRatio": "0.004",
            "cum": "0",
        },
        {
            "bracket": 2,
            "initialLeverage": 100,
            "notionalFloor": "50000",
            "notionalCap": "250000",
            "maintMarginRatio": "0.005",
            "cum": "50",
        },
        {
            "bracket": 3,
            "initialLeverage": 50,
            "notionalFloor": "250000",
            "notionalCap": "1000000",
            "maintMarginRatio": "0.01",
            "cum": "1300",
        },
    ],
}


def run_test(side, additional_margin="0"):
    result = calculate_trade_size(
        capital=20000,
        risk_percentage=1,
        entry_price=90000,
        stop_loss=88200 if side == "long" else 91800,
        capital_currency="USDT",
        rules=SYNTHETIC_RULES,
        side=side,
        fee_percentage_per_side="0.1",
        slippage_bps="5",
        leverage=5,
        leverage_brackets=SYNTHETIC_BRACKETS,
        additional_isolated_margin=additional_margin,
    )

    print(f"\n--- {side.upper()} | Additional margin: {additional_margin} ---")

    for key in (
        "position_quantity",
        "position_value",
        "margin_required_estimate",
        "additional_isolated_margin",
        "isolated_wallet_balance_estimate",
        "capital_required_estimate",
        "estimated_total_loss",
        "risk_budget_respected",
        "capital_constraint_respected",
        "maintenance_margin_status",
        "maintenance_margin_estimate",
        "liquidation_estimation_status",
        "liquidation_price_estimate",
        "liquidation_bracket",
    ):
        print(f"{key}: {result[key]}")

    assert result["status"] == "success"
    assert result["risk_budget_respected"] is True
    assert result["capital_constraint_respected"] is True
    assert result["liquidation_estimation_status"] == (
        "estimated_from_account_brackets"
    )
    assert result["liquidation_price_estimate"] is not None

    return result


if __name__ == "__main__":
    long_normal = run_test("long")
    long_extra = run_test("long", "200")

    short_normal = run_test("short")
    short_extra = run_test("short", "200")

    # More margin should move liquidation farther away.
    assert float(long_extra["liquidation_price_estimate"]) < float(
        long_normal["liquidation_price_estimate"]
    )

    assert float(short_extra["liquidation_price_estimate"]) > float(
        short_normal["liquidation_price_estimate"]
    )

    print("\nALL INTEGRATION TESTS PASSED.")
    print("Synthetic brackets were used; these are not live Binance tiers.")
