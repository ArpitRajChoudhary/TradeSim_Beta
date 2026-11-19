
from decimal import Decimal, InvalidOperation, ROUND_DOWN

from liquidation import calculate_isolated_liquidation_price


def to_decimal(value, field_name):
    try:
        number = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError(f"{field_name} must be a valid number.")

    if not number.is_finite():
        raise ValueError(f"{field_name} must be finite.")

    return number


def round_down_to_step(quantity, step):
    return (
        quantity / step
    ).to_integral_value(rounding=ROUND_DOWN) * step


def select_maintenance_bracket(position_value, bracket_data):
    if not bracket_data:
        return None

    brackets = sorted(
        bracket_data.get("brackets", []),
        key=lambda item: to_decimal(
            item["notionalFloor"],
            "Bracket notional floor"
        )
    )

    for index, bracket in enumerate(brackets):
        floor = to_decimal(
            bracket["notionalFloor"],
            "Bracket notional floor"
        )
        cap = to_decimal(
            bracket["notionalCap"],
            "Bracket notional cap"
        )

        if floor <= position_value < cap:
            return bracket

        if index == len(brackets) - 1 and floor <= position_value <= cap:
            return bracket

    raise ValueError(
        "No maintenance-margin bracket covers this position notional."
    )


def calculate_trade_size(
    capital,
    risk_percentage,
    entry_price,
    stop_loss,
    capital_currency,
    rules,
    side="long",
    fee_percentage_per_side="0.1",
    slippage_bps="5",
    leverage="1",
    leverage_brackets=None,
    additional_isolated_margin="0",
):
    """
    Binance Spot and USD-M Futures position sizing.

    Spot:
        Long positions only.

    USD-M Futures:
        Long and short positions.
        Optional additional isolated margin.

    Fee percentage:
        0.1 means 0.1% per side.

    Slippage:
        5 basis points means 0.05% adverse slippage.

    Additional isolated margin:
        Extra quote-asset collateral allocated to a Futures position.

    Liquidation:
        Estimated only when account-specific maintenance brackets
        are available.
    """

    capital = to_decimal(capital, "Capital")
    risk_percentage = to_decimal(risk_percentage, "Risk percentage")
    entry_price = to_decimal(entry_price, "Entry price")
    stop_loss = to_decimal(stop_loss, "Stop loss")
    fee_percentage = to_decimal(
        fee_percentage_per_side,
        "Fee percentage"
    )
    slippage_bps = to_decimal(slippage_bps, "Slippage")
    leverage = to_decimal(leverage, "Leverage")
    additional_margin = to_decimal(
        additional_isolated_margin,
        "Additional isolated margin"
    )

    market_type = rules["market_type"]
    side = side.lower().strip()
    order_type = rules.get("order_type", "MARKET").upper()

    if market_type not in ("spot", "futures"):
        raise ValueError("Unsupported market type.")

    if side not in ("long", "short"):
        raise ValueError("Side must be long or short.")

    if market_type == "spot" and side == "short":
        raise ValueError("Spot short selling is not supported.")

    if capital <= 0:
        raise ValueError("Capital must be greater than zero.")

    if risk_percentage <= 0 or risk_percentage > 100:
        raise ValueError("Risk percentage must be greater than 0 and at most 100.")

    if entry_price <= 0 or stop_loss <= 0:
        raise ValueError("Prices must be greater than zero.")

    if fee_percentage < 0 or slippage_bps < 0:
        raise ValueError("Fees and slippage cannot be negative.")

    if additional_margin < 0:
        raise ValueError("Additional isolated margin cannot be negative.")

    if leverage < 1 or leverage != leverage.to_integral_value():
        raise ValueError("Leverage must be a positive whole number.")

    if market_type == "spot":
        if leverage != 1:
            raise ValueError("Spot calculations do not use leverage.")

        if additional_margin != 0:
            raise ValueError("Additional isolated margin applies only to Futures.")

    if side == "long" and stop_loss >= entry_price:
        raise ValueError("For a long trade, stop loss must be below entry price.")

    if side == "short" and stop_loss <= entry_price:
        raise ValueError("For a short trade, stop loss must be above entry price.")

    quote_asset = rules["quote_asset"]

    if capital_currency.strip().upper() != quote_asset.upper():
        raise ValueError(
            f"This symbol is quoted in {quote_asset}, but your "
            f"capital currency is {capital_currency}. "
            "Currency conversion is not supported yet."
        )

    # Binance quantity filters
    step_size = to_decimal(rules["step_size"], "Quantity step")
    min_qty = to_decimal(rules["min_qty"], "Minimum quantity")
    max_qty = to_decimal(rules["max_qty"], "Maximum quantity")

    min_notional = to_decimal(
        rules.get("min_notional", "0"),
        "Minimum notional"
    )
    max_notional = to_decimal(
        rules.get("max_notional", "0"),
        "Maximum notional"
    )

    if step_size <= 0 or max_qty <= 0:
        raise ValueError("Invalid Binance quantity filters.")

    # Fees and slippage
    slippage_rate = slippage_bps / Decimal("10000")
    fee_rate = fee_percentage / Decimal("100")

    if side == "long":
        entry_fill = entry_price * (1 + slippage_rate)
        stop_fill = stop_loss * (1 - slippage_rate)
    else:
        entry_fill = entry_price * (1 - slippage_rate)
        stop_fill = stop_loss * (1 + slippage_rate)

    if entry_fill <= 0 or stop_fill <= 0:
        raise ValueError("Adjusted execution prices must be positive.")

    price_loss_per_unit = abs(entry_fill - stop_fill)
    entry_fee_per_unit = entry_fill * fee_rate
    exit_fee_per_unit = stop_fill * fee_rate

    total_risk_per_unit = (
        price_loss_per_unit
        + entry_fee_per_unit
        + exit_fee_per_unit
    )

    if total_risk_per_unit <= 0:
        raise ValueError("Risk per unit must be greater than zero.")

    risk_budget = capital * risk_percentage / Decimal("100")
    risk_based_quantity = risk_budget / total_risk_per_unit

    # Capital constraint
    if market_type == "spot":
        capital_per_unit = entry_fill * (1 + fee_rate)
    else:
        capital_per_unit = entry_fill * (
            (Decimal("1") / leverage) + fee_rate
        )

    capital_available_for_position = capital - additional_margin

    if capital_available_for_position <= 0:
        raise ValueError(
            "Additional margin leaves no capital for opening the position."
        )

    capital_based_quantity = (
        capital_available_for_position / capital_per_unit
    )

    raw_quantity = min(
        risk_based_quantity,
        capital_based_quantity,
        max_qty,
    )

    quantity = round_down_to_step(raw_quantity, step_size)

    if quantity <= 0:
        raise ValueError("Calculated quantity is below the permitted quantity step.")

    if quantity < min_qty:
        raise ValueError(
            f"Calculated quantity {quantity} is below Binance "
            f"minimum quantity {min_qty}."
        )

    position_value = entry_fill * quantity

    # Binance notional filter applicability
    min_flag = rules.get("min_notional_applies_to_market")
    max_flag = rules.get("max_notional_applies_to_market")

    if order_type == "MARKET":
        enforce_min_notional = min_flag is not False
        enforce_max_notional = max_flag is True
    else:
        enforce_min_notional = True
        enforce_max_notional = max_notional > 0

    if enforce_min_notional and min_notional > 0:
        if position_value < min_notional:
            raise ValueError(
                f"Estimated order value {position_value} is below "
                f"the minimum notional {min_notional} {quote_asset}."
            )

    if enforce_max_notional and max_notional > 0:
        if position_value > max_notional:
            raise ValueError(
                f"Estimated order value {position_value} exceeds "
                f"the maximum notional {max_notional} {quote_asset}."
            )

    # Estimated loss and fees
    estimated_price_loss = price_loss_per_unit * quantity
    estimated_entry_fee = entry_fee_per_unit * quantity
    estimated_exit_fee = exit_fee_per_unit * quantity
    estimated_fees = estimated_entry_fee + estimated_exit_fee
    estimated_total_loss = estimated_price_loss + estimated_fees

    if market_type == "spot":
        margin_required = position_value
        capital_required = position_value + estimated_entry_fee
        isolated_wallet_balance = None
    else:
        margin_required = position_value / leverage

        # This is a simulation estimate, not a live Binance wallet balance.
        isolated_wallet_balance = margin_required + additional_margin

        capital_required = (
            isolated_wallet_balance + estimated_entry_fee
        )

    # Maintenance margin and liquidation estimates
    maintenance_margin = None
    maintenance_margin_rate = None
    maintenance_margin_cum = None
    bracket_max_leverage = None
    bracket_number = None
    maintenance_status = "not_loaded"

    liquidation_result = None
    liquidation_status = "not_loaded"
    liquidation_error = None

    if market_type == "futures" and leverage_brackets:
        bracket_symbol = leverage_brackets.get("symbol")

        if bracket_symbol != rules["symbol"]:
            raise ValueError(
                "Leverage bracket symbol does not match the trade symbol."
            )

        bracket_list = leverage_brackets.get("brackets", [])

        bracket = select_maintenance_bracket(
            position_value,
            leverage_brackets
        )

        if bracket is None:
            raise ValueError("No matching maintenance-margin bracket was found.")

        bracket_max_leverage = to_decimal(
            bracket["initialLeverage"],
            "Bracket maximum leverage"
        )

        if leverage > bracket_max_leverage:
            raise ValueError(
                f"Requested leverage {leverage}x exceeds the "
                f"maximum {bracket_max_leverage}x for this notional tier."
            )

        maintenance_margin_rate = to_decimal(
            bracket["maintMarginRatio"],
            "Maintenance margin ratio"
        )

        maintenance_margin_cum = to_decimal(
            bracket["cum"],
            "Maintenance margin cumulative amount"
        )

        maintenance_margin = max(
            Decimal("0"),
            position_value * maintenance_margin_rate
            - maintenance_margin_cum
        )

        bracket_number = bracket["bracket"]
        maintenance_status = "estimated_from_account_bracket"

        # Isolated liquidation estimate
        try:
            liquidation_result = calculate_isolated_liquidation_price(
                quantity=quantity,
                entry_price=entry_fill,
                isolated_wallet_balance=isolated_wallet_balance,
                brackets=bracket_list,
                side=side,
            )

            liquidation_status = "estimated_from_account_brackets"

        except ValueError as error:
            liquidation_status = "unavailable"
            liquidation_error = str(error)

    elif market_type == "spot":
        maintenance_status = "not_applicable"
        liquidation_status = "not_applicable"

    # Notional validation explanation
    if order_type != "MARKET":
        notional_basis = "limit_order_reference_fill_estimate"
    elif min_flag is False:
        notional_basis = "minimum_notional_not_applied_to_market"
    elif min_flag is None:
        notional_basis = "conservative_check_flag_unavailable"
    else:
        notional_basis = "market_filter_applies_using_estimated_fill"

    return {
        "status": "success",
        "exchange": "Binance",
        "market_type": market_type,
        "symbol": rules["symbol"],
        "side": side,
        "quote_asset": quote_asset,

        "capital": str(capital),
        "risk_percentage": str(risk_percentage),
        "risk_budget": str(risk_budget),

        "reference_entry_price": str(entry_price),
        "reference_stop_price": str(stop_loss),
        "estimated_entry_fill": str(entry_fill),
        "estimated_stop_fill": str(stop_fill),

        "slippage_bps": str(slippage_bps),
        "fee_percentage_per_side": str(fee_percentage),
        "leverage": str(leverage),

        "quantity_step": str(step_size),
        "minimum_quantity": str(min_qty),
        "maximum_quantity": str(max_qty),
        "minimum_notional": str(min_notional),
        "maximum_notional": str(max_notional),
        "notional_validation_basis": notional_basis,

        "position_quantity": str(quantity),
        "position_value": str(position_value),

        "margin_required_estimate": str(margin_required),
        "additional_isolated_margin": str(additional_margin),
        "isolated_wallet_balance_estimate": (
            str(isolated_wallet_balance)
            if isolated_wallet_balance is not None
            else None
        ),

        "estimated_entry_fee": str(estimated_entry_fee),
        "estimated_exit_fee": str(estimated_exit_fee),
        "estimated_fees": str(estimated_fees),
        "estimated_price_loss": str(estimated_price_loss),
        "estimated_total_loss": str(estimated_total_loss),
        "capital_required_estimate": str(capital_required),

        "risk_budget_respected": estimated_total_loss <= risk_budget,
        "capital_constraint_respected": capital_required <= capital,

        "quantity_filter_respected": (
            quantity >= min_qty
            and quantity <= max_qty
            and quantity % step_size == 0
        ),

        "notional_filter_respected": (
            (not enforce_min_notional or position_value >= min_notional)
            and (
                not enforce_max_notional
                or max_notional <= 0
                or position_value <= max_notional
            )
        ),

        "maintenance_margin_status": maintenance_status,
        "maintenance_margin_estimate": (
            str(maintenance_margin)
            if maintenance_margin is not None
            else None
        ),
        "maintenance_margin_rate": (
            str(maintenance_margin_rate)
            if maintenance_margin_rate is not None
            else None
        ),
        "maintenance_margin_cum": (
            str(maintenance_margin_cum)
            if maintenance_margin_cum is not None
            else None
        ),
        "maintenance_bracket": bracket_number,
        "bracket_max_initial_leverage": (
            str(bracket_max_leverage)
            if bracket_max_leverage is not None
            else None
        ),

        "liquidation_estimation_status": liquidation_status,
        "liquidation_price_estimate": (
            liquidation_result["liquidation_price_estimate"]
            if liquidation_result
            else None
        ),
        "liquidation_bracket": (
            liquidation_result["maintenance_bracket"]
            if liquidation_result
            else None
        ),
        "liquidation_estimation_error": liquidation_error,

        "limitations": [
            "Slippage is a simulation assumption, not a guaranteed fill.",
            "Fees are estimates, not account-specific fee rates.",
            "Market notional validation uses an estimated fill.",
            "Maintenance margin requires account-specific bracket data.",
            "Isolated wallet balance is estimated from initial margin and additional margin.",
            "Liquidation price is an estimate, not Binance's guaranteed liquidation trigger.",
            "Mark-price movements, funding, commissions and liquidation fees can affect actual liquidation.",
            "Cross-margin balances and other positions are not modelled.",
            "No orders are sent to Binance.",
        ],
    }
