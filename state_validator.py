
from decimal import Decimal, InvalidOperation


# TradeSim application policy
MAX_RISK_PERCENTAGE = Decimal("5")


def to_decimal(value, field_name):
    """Safely convert a value to Decimal."""

    if isinstance(value, bool) or value is None:
        raise ValueError(f"{field_name} must be a valid number.")

    try:
        number = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError(f"{field_name} must be a valid number.")

    if not number.is_finite():
        raise ValueError(f"{field_name} must be finite.")

    return number


def validate_trading_state(state, require_complete=True):
    """
    Validate a TradeSim trading state.

    require_complete=True:
        All required fields must be present.

    require_complete=False:
        Allows incomplete states but validates supplied values.

    Supports both Long and Short positions.
    """

    if not isinstance(state, dict):
        return False, "Trading state must be a dictionary."

    required_fields = [
        "asset",
        "capital",
        "capital_currency",
        "risk_percentage",
        "entry_price",
        "stop_loss",
        "price_currency",
    ]

    if require_complete:
        missing = [
            field
            for field in required_fields
            if state.get(field) is None
            or (
                isinstance(state.get(field), str)
                and not state[field].strip()
            )
        ]

        if missing:
            return False, (
                "Missing information: " + ", ".join(missing)
            )

    # Validate asset.
    asset = state.get("asset")

    if asset is not None:
        if not isinstance(asset, str) or not asset.strip():
            return False, "Asset must be a valid non-empty name."

    # Validate currencies.
    for field in ("capital_currency", "price_currency"):
        value = state.get(field)

        if value is not None:
            if not isinstance(value, str) or not value.strip():
                return False, f"{field} must be a valid currency code."

    # Validate trading side.
    side = state.get("side", "long")

    if side is None:
        side = "long"

    if not isinstance(side, str) or side.lower() not in ("long", "short"):
        return False, "Side must be either 'long' or 'short'."

    side = side.lower()

    # Validate numeric fields.
    numeric_fields = {
        "capital": "Capital",
        "risk_percentage": "Risk percentage",
        "entry_price": "Entry price",
        "stop_loss": "Stop-loss",
    }

    numbers = {}

    for field, label in numeric_fields.items():
        value = state.get(field)

        if value is not None:
            try:
                numbers[field] = to_decimal(value, label)
            except ValueError as error:
                return False, str(error)

    # Capital validation.
    if "capital" in numbers and numbers["capital"] <= 0:
        return False, "Capital must be greater than zero."

    # Risk validation.
    if "risk_percentage" in numbers:
        risk = numbers["risk_percentage"]

        if risk <= 0:
            return False, "Risk percentage must be greater than zero."

        if risk > MAX_RISK_PERCENTAGE:
            return False, (
                f"Risk percentage cannot exceed "
                f"{MAX_RISK_PERCENTAGE}% under current TradeSim policy."
            )

    # Entry validation.
    if "entry_price" in numbers and numbers["entry_price"] <= 0:
        return False, "Entry price must be greater than zero."

    # Stop-loss validation.
    if "stop_loss" in numbers and numbers["stop_loss"] <= 0:
        return False, "Stop-loss must be greater than zero."

    # Validate entry/stop-loss relationship when both are supplied.
    if "entry_price" in numbers and "stop_loss" in numbers:

        entry = numbers["entry_price"]
        stop = numbers["stop_loss"]

        if side == "long" and stop >= entry:
            return False, (
                "For a long position, stop-loss must be below entry price."
            )

        if side == "short" and stop <= entry:
            return False, (
                "For a short position, stop-loss must be above entry price."
            )

    return True, "Trading state is valid."
