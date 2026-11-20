
from decimal import Decimal


# --------------------------------------------------
# Indicator calculation functions
# --------------------------------------------------

def calculate_sma(candles, period):
    """Calculate Simple Moving Average."""

    if not isinstance(period, int) or isinstance(period, bool) or period <= 0:
        raise ValueError("SMA period must be a positive integer.")

    values = [None] * len(candles)

    for index in range(period - 1, len(candles)):
        total = sum(
            (candles[i].close for i in range(index - period + 1, index + 1)),
            Decimal("0")
        )

        values[index] = total / Decimal(period)

    return {"value": values}


def calculate_ema(candles, period):
    """Calculate Exponential Moving Average."""

    if not isinstance(period, int) or isinstance(period, bool) or period <= 0:
        raise ValueError("EMA period must be a positive integer.")

    values = [None] * len(candles)

    if len(candles) < period:
        return {"value": values}

    # Seed EMA with the first SMA.
    initial_average = sum(
        (candles[i].close for i in range(period)),
        Decimal("0")
    ) / Decimal(period)

    values[period - 1] = initial_average

    multiplier = Decimal("2") / Decimal(period + 1)

    for index in range(period, len(candles)):
        previous_ema = values[index - 1]

        values[index] = (
            (candles[index].close - previous_ema) * multiplier
            + previous_ema
        )

    return {"value": values}


def calculate_rsi(candles, period):
    """Calculate RSI using Wilder's smoothing method."""

    if not isinstance(period, int) or isinstance(period, bool) or period <= 0:
        raise ValueError("RSI period must be a positive integer.")

    values = [None] * len(candles)

    if len(candles) <= period:
        return {"value": values}

    gains = []
    losses = []

    # Calculate initial average gain and loss.
    for index in range(1, period + 1):
        change = candles[index].close - candles[index - 1].close

        gains.append(max(change, Decimal("0")))
        losses.append(max(-change, Decimal("0")))

    average_gain = sum(gains, Decimal("0")) / Decimal(period)
    average_loss = sum(losses, Decimal("0")) / Decimal(period)

    def get_rsi(avg_gain, avg_loss):
        if avg_loss == 0:
            if avg_gain == 0:
                return Decimal("50")
            return Decimal("100")

        relative_strength = avg_gain / avg_loss

        return Decimal("100") - (
            Decimal("100") / (Decimal("1") + relative_strength)
        )

    values[period] = get_rsi(average_gain, average_loss)

    # Wilder's smoothing.
    for index in range(period + 1, len(candles)):
        change = candles[index].close - candles[index - 1].close

        gain = max(change, Decimal("0"))
        loss = max(-change, Decimal("0"))

        average_gain = (
            average_gain * Decimal(period - 1) + gain
        ) / Decimal(period)

        average_loss = (
            average_loss * Decimal(period - 1) + loss
        ) / Decimal(period)

        values[index] = get_rsi(average_gain, average_loss)

    return {"value": values}


# --------------------------------------------------
# Indicator registry
# --------------------------------------------------

INDICATOR_REGISTRY = {
    "sma": {
        "calculate": calculate_sma,
        "parameters": {"period"},
        "outputs": {"value"},
    },
    "ema": {
        "calculate": calculate_ema,
        "parameters": {"period"},
        "outputs": {"value"},
    },
    "rsi": {
        "calculate": calculate_rsi,
        "parameters": {"period"},
        "outputs": {"value"},
    },
}


# --------------------------------------------------
# Indicator validation and execution
# --------------------------------------------------

def validate_indicator_definition(indicator):
    """
    Validate an indicator against the registry capabilities.
    """

    if not isinstance(indicator, dict):
        raise ValueError("Indicator definition must be an object.")

    indicator_type = indicator.get("type")

    if not isinstance(indicator_type, str):
        raise ValueError("Indicator type must be a string.")

    indicator_type = indicator_type.strip().lower()

    if indicator_type not in INDICATOR_REGISTRY:
        raise ValueError(
            f"Unsupported indicator: {indicator_type}"
        )

    definition = INDICATOR_REGISTRY[indicator_type]

    parameters = indicator.get("parameters")

    if not isinstance(parameters, dict):
        raise ValueError("Indicator parameters must be an object.")

    if set(parameters.keys()) != definition["parameters"]:
        raise ValueError(
            f"{indicator_type.upper()} requires exactly these "
            f"parameters: {', '.join(sorted(definition['parameters']))}"
        )

    for parameter_name, parameter_value in parameters.items():
        if parameter_name == "period":
            if (
                isinstance(parameter_value, bool)
                or not isinstance(parameter_value, int)
                or parameter_value <= 0
            ):
                raise ValueError(
                    f"{indicator_type.upper()} period must be "
                    "a positive integer."
                )

    return indicator_type


def validate_indicator_output(indicator_type, output):
    """
    Verify that an indicator supports the requested output.
    """

    if not isinstance(indicator_type, str):
        raise ValueError("Indicator type must be a string.")

    indicator_type = indicator_type.strip().lower()

    if indicator_type not in INDICATOR_REGISTRY:
        raise ValueError(
            f"Unsupported indicator: {indicator_type}"
        )

    supported_outputs = INDICATOR_REGISTRY[indicator_type]["outputs"]

    if output not in supported_outputs:
        raise ValueError(
            f"Unsupported output '{output}' for "
            f"{indicator_type.upper()}. "
            f"Supported outputs: {', '.join(sorted(supported_outputs))}"
        )


def calculate_indicator(candles, indicator_type, parameters):
    indicator_type = validate_indicator_definition({
        "type": indicator_type,
        "parameters": parameters,
    })

    definition = INDICATOR_REGISTRY[indicator_type]

    return definition["calculate"](
        candles,
        **parameters
    )


def calculate_indicators(candles, indicator_definitions):
    """
    Calculate all indicators defined in a strategy.

    Each indicator is stored using its unique strategy ID.
    """

    results = {}

    for definition in indicator_definitions:
        indicator_id = definition["id"]
        indicator_type = definition["type"]
        parameters = definition["parameters"]

        if indicator_id in results:
            raise ValueError(f"Duplicate indicator ID: {indicator_id}")

        results[indicator_id] = calculate_indicator(
            candles,
            indicator_type,
            parameters
        )

    return results
