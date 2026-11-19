
from decimal import Decimal, InvalidOperation


def to_decimal(value, field_name):
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError(f"{field_name} must be a valid number.")

    if not result.is_finite():
        raise ValueError(f"{field_name} must be finite.")

    return result


def find_bracket(notional, brackets):
    ordered = sorted(
        brackets,
        key=lambda item: Decimal(str(item["notionalFloor"]))
    )

    for index, bracket in enumerate(ordered):
        floor = Decimal(str(bracket["notionalFloor"]))
        cap = Decimal(str(bracket["notionalCap"]))

        if floor <= notional < cap:
            return bracket

        if index == len(ordered) - 1 and floor <= notional <= cap:
            return bracket

    raise ValueError("No matching maintenance-margin bracket found.")


def calculate_isolated_liquidation_price(
    quantity,
    entry_price,
    isolated_wallet_balance,
    brackets,
    side="long",
):
    quantity = to_decimal(quantity, "quantity")
    entry_price = to_decimal(entry_price, "entry_price")
    wallet_balance = to_decimal(
        isolated_wallet_balance,
        "isolated_wallet_balance"
    )

    side = side.lower().strip()

    if side not in ("long", "short"):
        raise ValueError("Side must be 'long' or 'short'.")

    if quantity <= 0 or entry_price <= 0:
        raise ValueError("Quantity and entry price must be positive.")

    if wallet_balance <= 0:
        raise ValueError("Isolated wallet balance must be positive.")

    if not brackets:
        raise ValueError("Maintenance-margin brackets are required.")

    entry_notional = quantity * entry_price
    valid_results = []

    for bracket in brackets:
        mmr = to_decimal(
            bracket["maintMarginRatio"],
            "maintMarginRatio"
        )
        cum = to_decimal(bracket["cum"], "cum")

        if mmr < 0 or mmr >= 1:
            raise ValueError("Invalid maintenance-margin ratio.")

        if side == "long":
            liquidation_price = (
                entry_notional - wallet_balance - cum
            ) / (quantity * (Decimal("1") - mmr))
        else:
            liquidation_price = (
                wallet_balance + cum + entry_notional
            ) / (quantity * (Decimal("1") + mmr))

        if liquidation_price <= 0:
            continue

        liquidation_notional = quantity * liquidation_price

        try:
            matching_bracket = find_bracket(
                liquidation_notional,
                brackets
            )
        except ValueError:
            continue

        if matching_bracket == bracket:
            valid_results.append({
                "liquidation_price": liquidation_price,
                "liquidation_notional": liquidation_notional,
                "mmr": mmr,
                "cum": cum,
                "bracket": bracket.get("bracket"),
                "floor": bracket["notionalFloor"],
                "cap": bracket["notionalCap"],
            })

    if len(valid_results) == 0:
        raise ValueError(
            "No consistent liquidation price found for the supplied tiers."
        )

    if len(valid_results) > 1:
        raise ValueError(
            "Multiple tiers matched. Check for overlapping bracket ranges."
        )

    result = valid_results[0]

    return {
        "side": side,
        "quantity": str(quantity),
        "entry_price": str(entry_price),
        "entry_notional": str(entry_notional),
        "isolated_wallet_balance": str(wallet_balance),
        "liquidation_price_estimate": str(
            result["liquidation_price"]
        ),
        "liquidation_notional_estimate": str(
            result["liquidation_notional"]
        ),
        "maintenance_margin_ratio": str(result["mmr"]),
        "maintenance_amount": str(result["cum"]),
        "maintenance_bracket": result["bracket"],
        "bracket_floor": str(result["floor"]),
        "bracket_cap": str(result["cap"]),
        "warning": (
            "Estimated isolated-margin liquidation price. "
            "Actual liquidation depends on mark price, account settings, "
            "fees, funding and exchange rules."
        ),
    }
