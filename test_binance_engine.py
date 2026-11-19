
import os

from dotenv import load_dotenv

from binance_market import (
    get_symbol_rules,
    get_leverage_brackets,
)

from calculator import calculate_trade_size


load_dotenv()


def run_test(
    market_type,
    side,
    entry_price,
    stop_loss,
    leverage=1,
    additional_isolated_margin="0",
):
    print("\n" + "=" * 60)
    print(f"TEST: BINANCE {market_type.upper()} — {side.upper()}")
    print("=" * 60)

    rules = get_symbol_rules(
        symbol="BTCUSDT",
        market_type=market_type,
        order_type="MARKET",
    )

    print("\nLIVE BINANCE RULES:")

    for key, value in rules.items():
        print(f"{key}: {value}")

    brackets = None

    if market_type == "futures":
        if (
            os.getenv("BINANCE_API_KEY")
            and os.getenv("BINANCE_API_SECRET")
        ):
            try:
                brackets = get_leverage_brackets("BTCUSDT")
                print("\nAccount-specific Futures brackets retrieved.")
            except Exception as error:
                print(
                    "\nCould not retrieve Futures brackets. "
                    f"Continuing without them: {error}"
                )
        else:
            print(
                "\nNo Binance API credentials configured. "
                "Liquidation estimation will be unavailable."
            )

    result = calculate_trade_size(
        capital=20000,
        risk_percentage=1,
        entry_price=entry_price,
        stop_loss=stop_loss,
        capital_currency="USDT",
        rules=rules,
        side=side,
        fee_percentage_per_side="0.1",
        slippage_bps="5",
        leverage=leverage,
        leverage_brackets=brackets,
        additional_isolated_margin=additional_isolated_margin,
    )

    print("\nCALCULATION RESULTS:")

    for key, value in result.items():
        print(f"{key}: {value}")


if __name__ == "__main__":

    run_test(
        market_type="spot",
        side="long",
        entry_price=90000,
        stop_loss=88200,
    )

    run_test(
        market_type="futures",
        side="long",
        entry_price=90000,
        stop_loss=88200,
        leverage=5,
        additional_isolated_margin="200",
    )

    run_test(
        market_type="futures",
        side="short",
        entry_price=90000,
        stop_loss=91800,
        leverage=5,
    )
