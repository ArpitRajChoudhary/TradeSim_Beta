
from decimal import Decimal

from liquidation import calculate_isolated_liquidation_price


TEST_BRACKETS = [
    {
        "bracket": 1,
        "notionalFloor": "0",
        "notionalCap": "50000",
        "maintMarginRatio": "0.004",
        "cum": "0",
    },
    {
        "bracket": 2,
        "notionalFloor": "50000",
        "notionalCap": "250000",
        "maintMarginRatio": "0.005",
        "cum": "50",
    },
    {
        "bracket": 3,
        "notionalFloor": "250000",
        "notionalCap": "1000000",
        "maintMarginRatio": "0.01",
        "cum": "1300",
    },
]


def calculate(side, quantity, entry, margin):
    return calculate_isolated_liquidation_price(
        quantity=quantity,
        entry_price=entry,
        isolated_wallet_balance=margin,
        brackets=TEST_BRACKETS,
        side=side,
    )


def show_result(name, result):
    print(f"\n--- {name} ---")
    print("Entry notional:", result["entry_notional"])
    print("Liquidation price:", result["liquidation_price_estimate"])
    print("Liquidation notional:", result["liquidation_notional_estimate"])
    print("Maintenance bracket:", result["maintenance_bracket"])


def main():
    # Original long and short tests.
    long_result = calculate("long", "0.096", "90000", "1728")
    short_result = calculate("short", "0.096", "90000", "1728")

    show_result("LONG", long_result)
    show_result("SHORT", short_result)

    # Additional margin tests.
    long_extra = calculate("long", "0.096", "90000", "1928")
    short_extra = calculate("short", "0.096", "90000", "1928")

    assert Decimal(long_extra["liquidation_price_estimate"]) < Decimal(
        long_result["liquidation_price_estimate"]
    )

    assert Decimal(short_extra["liquidation_price_estimate"]) > Decimal(
        short_result["liquidation_price_estimate"]
    )

    print("\nPASS: Additional margin moves liquidation farther away.")

    # Long: entry notional is 60,000 (tier 2),
    # but liquidation notional should be in tier 1.
    long_transition = calculate("long", "1", "60000", "15000")

    assert long_transition["maintenance_bracket"] == 1
    show_result("LONG TIER TRANSITION", long_transition)

    # Short: entry notional is 49,000 (tier 1),
    # but liquidation notional should be in tier 2.
    short_transition = calculate("short", "1", "49000", "10000")

    assert short_transition["maintenance_bracket"] == 2
    show_result("SHORT TIER TRANSITION", short_transition)

    print("\nPASS: Both maintenance-tier transition tests passed.")
    print("ALL TESTS PASSED.")


if __name__ == "__main__":
    main()
