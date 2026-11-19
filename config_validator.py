
from decimal import Decimal, InvalidOperation


# --------------------------------------------------
# DEFAULT SETTINGS
# --------------------------------------------------

DEFAULT_SETTINGS = {
    "initial_capital": Decimal("20000"),
    "quote_per_trade": Decimal("1000"),
    "fee_percentage_per_side": Decimal("0.1"),
    "slippage_bps": Decimal("5"),
    "stop_loss_percentage": Decimal("2"),
    "take_profit_percentage": Decimal("4"),
}


# These are TradeSim safety limits, not Binance rules.
MAX_FEE_PERCENTAGE = Decimal("10")
MAX_SLIPPAGE_BPS = Decimal("1000")


# --------------------------------------------------
# NUMERIC VALIDATION
# --------------------------------------------------

def to_decimal(value, name):

    if isinstance(value, bool):
        raise ValueError(f"{name} must be a number.")

    try:
        number = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError(f"{name} must be a valid number.")

    if not number.is_finite():
        raise ValueError(f"{name} must be finite.")

    return number


def validate_positive(value, name):
    number = to_decimal(value, name)

    if number <= 0:
        raise ValueError(
            f"{name} must be greater than zero."
        )

    return number


# --------------------------------------------------
# INTEGER VALIDATION
# --------------------------------------------------

def validate_period(value, name):

    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{name} must be an integer.")

    if value <= 0:
        raise ValueError(f"{name} must be positive.")

    return value


# --------------------------------------------------
# MAIN CONFIGURATION VALIDATOR
# --------------------------------------------------

def validate_backtest_config(config):

    if not isinstance(config, dict):
        raise ValueError("Configuration must be a dictionary.")

    # ----------------------------------------------
    # Asset
    # ----------------------------------------------

    asset = config.get("asset")

    if not isinstance(asset, str) or not asset.strip():
        raise ValueError("Please specify a valid asset.")

    asset = asset.strip().upper()

    if asset != "BTCUSDT":
        raise ValueError(
            "Currently, only BTCUSDT is supported."
        )

    # ----------------------------------------------
    # Market
    # ----------------------------------------------

    market_type = config.get("market_type")

    if market_type is None:
        market_type = "spot"

    if not isinstance(market_type, str):
        raise ValueError("Market type must be a string.")

    market_type = market_type.strip().lower()

    if market_type != "spot":
        raise ValueError(
            "Only Spot backtesting is supported."
        )

    # ----------------------------------------------
    # Timeframe
    # ----------------------------------------------

    timeframe = config.get("timeframe")

    if timeframe is None:
        timeframe = "1h"

    if not isinstance(timeframe, str):
        raise ValueError("Timeframe must be a string.")

    timeframe = timeframe.strip().lower()

    if timeframe != "1h":
        raise ValueError(
            "Only the 1-hour timeframe is supported."
        )

    # ----------------------------------------------
    # Strategy
    # ----------------------------------------------

    strategy_type = config.get("strategy_type")

    if strategy_type != "sma_crossover":
        raise ValueError(
            "Only SMA crossover strategy is supported."
        )

    fast_period = validate_period(
        config.get("fast_period"),
        "Fast SMA period",
    )

    slow_period = validate_period(
        config.get("slow_period"),
        "Slow SMA period",
    )

    if fast_period >= slow_period:
        raise ValueError(
            "Fast SMA period must be smaller than slow SMA period."
        )

    # ----------------------------------------------
    # Portfolio settings
    # ----------------------------------------------

    initial_capital = validate_positive(
        config.get(
            "initial_capital",
            DEFAULT_SETTINGS["initial_capital"],
        ) if config.get("initial_capital") is not None
        else DEFAULT_SETTINGS["initial_capital"],
        "Initial capital",
    )

    quote_per_trade = validate_positive(
        config.get("quote_per_trade")
        if config.get("quote_per_trade") is not None
        else DEFAULT_SETTINGS["quote_per_trade"],
        "Quote per trade",
    )

    if quote_per_trade > initial_capital:
        raise ValueError(
            "Quote per trade cannot exceed initial capital."
        )

    # ----------------------------------------------
    # Fee validation
    # ----------------------------------------------

    fee = to_decimal(
        config.get("fee_percentage_per_side")
        if config.get("fee_percentage_per_side") is not None
        else DEFAULT_SETTINGS["fee_percentage_per_side"],
        "Fee per side",
    )

    if fee < 0:
        raise ValueError("Fee cannot be negative.")

    if fee > MAX_FEE_PERCENTAGE:
        raise ValueError(
            f"Fee per side cannot exceed "
            f"{MAX_FEE_PERCENTAGE}%."
        )

    # ----------------------------------------------
    # Slippage validation
    # ----------------------------------------------

    slippage = to_decimal(
        config.get("slippage_bps")
        if config.get("slippage_bps") is not None
        else DEFAULT_SETTINGS["slippage_bps"],
        "Slippage",
    )

    if slippage < 0:
        raise ValueError("Slippage cannot be negative.")

    if slippage > MAX_SLIPPAGE_BPS:
        raise ValueError(
            f"Slippage cannot exceed "
            f"{MAX_SLIPPAGE_BPS} basis points."
        )

    # ----------------------------------------------
    # Stop-loss validation
    # ----------------------------------------------

    stop_loss = validate_positive(
        config.get("stop_loss_percentage")
        if config.get("stop_loss_percentage") is not None
        else DEFAULT_SETTINGS["stop_loss_percentage"],
        "Stop-loss",
    )

    if stop_loss >= 100:
        raise ValueError(
            "Stop-loss must be below 100%."
        )

    # ----------------------------------------------
    # Take-profit validation
    # ----------------------------------------------

    take_profit = validate_positive(
        config.get("take_profit_percentage")
        if config.get("take_profit_percentage") is not None
        else DEFAULT_SETTINGS["take_profit_percentage"],
        "Take-profit",
    )

    # ----------------------------------------------
    # Return normalized configuration
    # ----------------------------------------------

    return {
        "asset": asset,
        "market_type": market_type,
        "timeframe": timeframe,
        "strategy_type": strategy_type,
        "fast_period": fast_period,
        "slow_period": slow_period,
        "initial_capital": initial_capital,
        "quote_per_trade": quote_per_trade,
        "fee_percentage_per_side": fee,
        "slippage_bps": slippage,
        "stop_loss_percentage": stop_loss,
        "take_profit_percentage": take_profit,
    }
