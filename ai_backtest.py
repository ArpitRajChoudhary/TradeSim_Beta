
import os
import json
import math
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types

from backtest_data import load_candles
from strategies import SmaCrossStrategy
from generic_strategy import ConditionBasedStrategy
from backtest_engine import BacktestEngine
from backtest_report import generate_backtest_report
from strategy_schema import validate_strategy_schema


# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent

DATASET_PATH = (
    BASE_DIR / "data" / "historical" / "BTCUSDT_spot_1h.csv"
)

MODEL = "gemini-3.5-flash-lite"

DEFAULT_SETTINGS = {
    "initial_capital": 20000,
    "quote_per_trade": 1000,
    "fee_percentage_per_side": 0.1,
    "slippage_bps": 5,
    "stop_loss_percentage": 2,
    "take_profit_percentage": 4,
}

load_dotenv(BASE_DIR / ".env")

# api_key = os.getenv("GEMINI_API_KEY")

# if not api_key:
#     raise ValueError(
#         "GEMINI_API_KEY was not found. Check your .env file."
#     )

# client = genai.Client(api_key=api_key)


# --------------------------------------------------
# AI INSTRUCTIONS
# --------------------------------------------------


SYSTEM_PROMPT = """
You are TradeSim's strategy interpretation component.

Your job is to extract structured backtesting parameters
from the user's natural-language trading request.

You do NOT calculate profits, losses, prices or indicators.
Python performs all calculations and runs the backtest.

CURRENT EXECUTION LIMITATIONS:

Asset:
- BTCUSDT only

Market:
- Spot only

Timeframe:
- 1h only

Supported strategy types:
1. sma_crossover
2. condition_based

Supported indicators:
- sma
- ema
- rsi

All currently supported indicators use a period parameter
and return an output named "value".

Supported logical operators:
- AND
- OR

Supported comparisons:
- greater_than
- less_than
- greater_than_or_equal
- less_than_or_equal
- equals
- crosses_above
- crosses_below

Supported condition operand sources:
- indicator
- price
- constant
- volume

Price fields:
- open
- high
- low
- close

INTERPRETATION RULES:

1. Extract only information supported by the user's request.
2. Do not invent missing strategy parameters.
3. Use sma_crossover only when the user describes an SMA crossover.
4. Use condition_based for other supported indicator-based strategies.
5. For SMA crossover, extract fast_period and slow_period.
6. For condition_based, define indicators with unique IDs,
   indicator types, and their parameters.
7. Represent entry and exit conditions separately.
8. Use AND or OR to combine conditions.
9. Represent each condition using left, comparison, and right.
10. Indicator operands must reference a defined indicator ID
    and its output.
11. Price operands must specify a valid OHLC field.
12. Constant operands must contain a numerical value.
13. Do not invent indicator calculations or unsupported operations.
14. If the requested strategy uses unsupported functionality,
    identify it explicitly and request clarification or explain
    that it cannot currently be executed.
15. Do not silently omit unsupported strategy conditions.
16. Do not claim a strategy is executable merely because you
    can understand its description.
17. Identify entry, exit, stop-loss, take-profit, and position
    sizing rules separately.
18. Preserve the exact meaning of the user's strategy.
19. Do not calculate profits, losses, performance metrics,
    or backtest results.
20. Python is responsible for all validation and execution.

PORTFOLIO AND EXECUTION PARAMETERS:

- initial_capital (USDT)
- quote_per_trade (USDT)
- fee_percentage_per_side (percentage)
- slippage_bps (basis points)
- stop_loss_percentage
- take_profit_percentage

DEFAULT RULES:

1. If market_type is not specified, return null.
2. If timeframe is not specified, return null.
3. If initial capital is not specified, return null.
4. If trade amount is not specified, return null.
5. If trading fees are not specified, return null.
6. If slippage is not specified, return null.
7. If stop-loss or take-profit is not specified, return null.
8. Do not confuse percentages with basis points.
9. Do not assume missing indicator periods.
10. Return missing_information when essential information
    is unavailable.
11. Set needs_clarification to true when clarification is needed.
12. Explain the interpreted strategy in user_explanation.

STRATEGY OUTPUT RULES:

For sma_crossover:
- Return strategy_type = "sma_crossover".
- Return fast_period and slow_period.
- Return indicators as an empty list.
- Return entry and exit as null.

For condition_based:
- Return strategy_type = "condition_based".
- Return indicators as a list of definitions.
- Return entry and exit as condition groups.
- Return fast_period and slow_period as null.

Never claim that unsupported conditions were executed.
"""


# --------------------------------------------------
# GEMINI RESPONSE SCHEMA
# --------------------------------------------------


operand_schema = {
    "type": "OBJECT",
    "properties": {
        "source": {
            "type": "STRING",
            "enum": ["indicator", "price", "constant", "volume"],
        },
        "id": {
            "type": "STRING",
            "nullable": True,
        },
        "output": {
            "type": "STRING",
            "nullable": True,
        },
        "field": {
            "type": "STRING",
            "enum": ["open", "high", "low", "close"],
            "nullable": True,
        },
        "value": {
            "type": "NUMBER",
            "nullable": True,
        },
    },
    "required": ["source", "id", "output", "field", "value"],
}


condition_schema = {
    "type": "OBJECT",
    "properties": {
        "left": operand_schema,
        "comparison": {
            "type": "STRING",
            "enum": [
                "greater_than",
                "less_than",
                "greater_than_or_equal",
                "less_than_or_equal",
                "equals",
                "crosses_above",
                "crosses_below",
            ],
        },
        "right": operand_schema,
    },
    "required": ["left", "comparison", "right"],
}


condition_group_schema = {
    "type": "OBJECT",
    "properties": {
        "operator": {
            "type": "STRING",
            "enum": ["AND", "OR"],
        },
        "conditions": {
            "type": "ARRAY",
            "items": condition_schema,
        },
    },
    "required": ["operator", "conditions"],
}


indicator_schema = {
    "type": "OBJECT",
    "properties": {
        "id": {
            "type": "STRING",
        },
        "type": {
            "type": "STRING",
            "enum": ["sma", "ema", "rsi"],
        },
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "period": {
                    "type": "INTEGER",
                    "nullable": True,
                },
            },
            "required": ["period"],
        },
    },
    "required": ["id", "type", "parameters"],
}


response_schema = {
    "type": "OBJECT",
    "properties": {
        "asset": {
            "type": "STRING",
            "nullable": True,
        },
        "market_type": {
            "type": "STRING",
            "nullable": True,
        },
        "timeframe": {
            "type": "STRING",
            "nullable": True,
        },
        "strategy_type": {
            "type": "STRING",
            "enum": ["sma_crossover", "condition_based"],
        },
        "fast_period": {
            "type": "INTEGER",
            "nullable": True,
        },
        "slow_period": {
            "type": "INTEGER",
            "nullable": True,
        },
        "indicators": {
            "type": "ARRAY",
            "items": indicator_schema,
        },
        "entry": {
            **condition_group_schema,
            "nullable": True,
        },
        "exit": {
            **condition_group_schema,
            "nullable": True,
        },
        "stop_loss_percentage": {
            "type": "NUMBER",
            "nullable": True,
        },
        "take_profit_percentage": {
            "type": "NUMBER",
            "nullable": True,
        },
        "initial_capital": {
            "type": "NUMBER",
            "nullable": True,
        },
        "quote_per_trade": {
            "type": "NUMBER",
            "nullable": True,
        },
        "fee_percentage_per_side": {
            "type": "NUMBER",
            "nullable": True,
        },
        "slippage_bps": {
            "type": "NUMBER",
            "nullable": True,
        },
        "missing_information": {
            "type": "ARRAY",
            "items": {
                "type": "STRING",
            },
        },
        "needs_clarification": {
            "type": "BOOLEAN",
        },
        "clarification_question": {
            "type": "STRING",
            "nullable": True,
        },
        "user_explanation": {
            "type": "STRING",
        },
    },
    "required": [
        "asset",
        "market_type",
        "timeframe",
        "strategy_type",
        "fast_period",
        "slow_period",
        "indicators",
        "entry",
        "exit",
        "stop_loss_percentage",
        "take_profit_percentage",
        "initial_capital",
        "quote_per_trade",
        "fee_percentage_per_side",
        "slippage_bps",
        "missing_information",
        "needs_clarification",
        "clarification_question",
        "user_explanation",
    ],
}


# --------------------------------------------------
# ASK GEMINI TO INTERPRET THE REQUEST
# --------------------------------------------------

def interpret_strategy(user_prompt):
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not configured.")

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=MODEL,
        contents=f"""
{SYSTEM_PROMPT}

USER REQUEST:

{user_prompt}

Extract the strategy configuration.
Return only the structured JSON response.
""",
        config=types.GenerateContentConfig(
            temperature=0.1,
            response_mime_type="application/json",
            response_schema=response_schema,
        ),
    )

    if not response.text:
        raise ValueError("Gemini returned an empty response.")

    return json.loads(response.text)


# --------------------------------------------------
# NUMERIC VALIDATION HELPER
# --------------------------------------------------

def validate_number(value, name, default, minimum, maximum=None):

    if value is None:
        value = default

    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
    ):
        raise ValueError(f"{name} must be a valid number.")

    if value < minimum:
        raise ValueError(
            f"{name} must be at least {minimum}."
        )

    if maximum is not None and value > maximum:
        raise ValueError(
            f"{name} must not exceed {maximum}."
        )

    return value


# --------------------------------------------------
# PYTHON VALIDATION
# --------------------------------------------------


def validate_strategy(config):

    if not isinstance(config, dict):
        raise ValueError("Strategy configuration must be an object.")

    # --------------------------------------------------
    # 1. ASSET VALIDATION
    # --------------------------------------------------

    asset = config.get("asset")

    if not isinstance(asset, str) or not asset.strip():
        raise ValueError("Please specify the asset.")

    asset = asset.strip().upper()

    if asset != "BTCUSDT":
        raise ValueError(
            "This integration currently supports BTCUSDT only."
        )

    # --------------------------------------------------
    # 2. MARKET VALIDATION
    # --------------------------------------------------

    market_type = config.get("market_type")

    if market_type is None:
        market_type = "spot"

    if not isinstance(market_type, str):
        raise ValueError("Market type must be a string.")

    market_type = market_type.strip().lower()

    if market_type != "spot":
        raise ValueError(
            "Only Spot backtesting is currently supported."
        )

    # --------------------------------------------------
    # 3. TIMEFRAME VALIDATION
    # --------------------------------------------------

    timeframe = config.get("timeframe")

    if timeframe is None:
        timeframe = "1h"

    if not isinstance(timeframe, str):
        raise ValueError("Timeframe must be a string.")

    timeframe = timeframe.strip().lower()

    if timeframe != "1h":
        raise ValueError(
            "Only the 1-hour timeframe is currently supported."
        )

    # --------------------------------------------------
    # 4. STRATEGY TYPE VALIDATION
    # --------------------------------------------------

    strategy_type = config.get("strategy_type")

    if strategy_type not in {
        "sma_crossover",
        "condition_based",
    }:
        raise ValueError(
            f"Unsupported strategy type: {strategy_type}"
        )

    fast_period = None
    slow_period = None
    indicators = []
    entry = None
    exit = None

    # --------------------------------------------------
    # 5. SMA CROSSOVER VALIDATION
    # --------------------------------------------------

    if strategy_type == "sma_crossover":

        fast_period = config.get("fast_period")
        slow_period = config.get("slow_period")

        if fast_period is None or slow_period is None:
            raise ValueError(
                "Both fast and slow SMA periods are required."
            )

        if (
            isinstance(fast_period, bool)
            or not isinstance(fast_period, int)
            or isinstance(slow_period, bool)
            or not isinstance(slow_period, int)
        ):
            raise ValueError("SMA periods must be integers.")

        if fast_period <= 0 or slow_period <= 0:
            raise ValueError("SMA periods must be positive.")

        if fast_period >= slow_period:
            raise ValueError(
                "Fast SMA period must be smaller than slow SMA period."
            )

    # --------------------------------------------------
    # 6. GENERIC CONDITION-BASED STRATEGY VALIDATION
    # --------------------------------------------------

    elif strategy_type == "condition_based":

        # Validate the generic strategy structure.
        validate_strategy_schema(config)

        indicators = config["indicators"]
        entry = config["entry"]
        exit = config["exit"]

        if not indicators:
            raise ValueError(
                "At least one indicator is required."
            )

        if entry is None or exit is None:
            raise ValueError(
                "Both entry and exit conditions are required."
            )

        supported_indicators = {"sma", "ema", "rsi"}

        for indicator in indicators:

            indicator_type = indicator.get("type")

            if indicator_type not in supported_indicators:
                raise ValueError(
                    f"Unsupported indicator: {indicator_type}"
                )

            parameters = indicator["parameters"]

            if set(parameters.keys()) != {"period"}:
                raise ValueError(
                    f"Unsupported parameters for {indicator_type}. "
                    "Only period is currently supported."
                )

            period = parameters.get("period")

            if (
                isinstance(period, bool)
                or not isinstance(period, int)
                or period <= 0
            ):
                raise ValueError(
                    f"{indicator_type} period must be a "
                    "positive integer."
                )

        # Currently every registered indicator returns "value".
        # Reject unknown outputs instead of silently ignoring them.
        for group in (entry, exit):

            for condition in group["conditions"]:

                for side in ("left", "right"):

                    operand = condition[side]

                    if operand["source"] == "indicator":

                        if operand["output"] != "value":
                            raise ValueError(
                                "Unsupported indicator output: "
                                f"{operand['output']}"
                            )

    # --------------------------------------------------
    # 7. STOP-LOSS AND TAKE-PROFIT VALIDATION
    # --------------------------------------------------

    stop_loss = validate_number(
        config.get("stop_loss_percentage"),
        "Stop-loss",
        DEFAULT_SETTINGS["stop_loss_percentage"],
        0.000001,
        99.999999,
    )

    take_profit = validate_number(
        config.get("take_profit_percentage"),
        "Take-profit",
        DEFAULT_SETTINGS["take_profit_percentage"],
        0.000001,
    )

    # --------------------------------------------------
    # 8. PORTFOLIO SETTINGS
    # --------------------------------------------------

    initial_capital = validate_number(
        config.get("initial_capital"),
        "Initial capital",
        DEFAULT_SETTINGS["initial_capital"],
        0.000001,
    )

    quote_per_trade = validate_number(
        config.get("quote_per_trade"),
        "Quote per trade",
        DEFAULT_SETTINGS["quote_per_trade"],
        0.000001,
    )

    if quote_per_trade > initial_capital:
        raise ValueError(
            "Quote per trade cannot exceed initial capital."
        )

    # --------------------------------------------------
    # 9. EXECUTION SETTINGS
    # --------------------------------------------------

    fee_percentage_per_side = validate_number(
        config.get("fee_percentage_per_side"),
        "Fee per side",
        DEFAULT_SETTINGS["fee_percentage_per_side"],
        0,
        99.999999,
    )

    slippage_bps = validate_number(
        config.get("slippage_bps"),
        "Slippage",
        DEFAULT_SETTINGS["slippage_bps"],
        0,
    )

    # --------------------------------------------------
    # 10. RETURN VALIDATED CONFIGURATION
    # --------------------------------------------------

    return {
        "asset": asset,
        "market_type": market_type,
        "timeframe": timeframe,
        "strategy_type": strategy_type,

        "fast_period": fast_period,
        "slow_period": slow_period,

        "indicators": indicators,
        "entry": entry,
        "exit": exit,

        "stop_loss_percentage": stop_loss,
        "take_profit_percentage": take_profit,

        "initial_capital": initial_capital,
        "quote_per_trade": quote_per_trade,
        "fee_percentage_per_side": fee_percentage_per_side,
        "slippage_bps": slippage_bps,
    }

# --------------------------------------------------
# RUN BACKTEST
# --------------------------------------------------



def run_ai_backtest(config, generate_report=True):
    """
    Execute the validated backtest.

    Execution duration measures only BacktestEngine.run(),
    not AI interpretation or report generation.
    """
    import time

    if not DATASET_PATH.exists():
        raise FileNotFoundError(
            f"Historical dataset not found: {DATASET_PATH}"
        )

    candles = load_candles(DATASET_PATH)

    # Select the strategy and validate its required history.
    if config["strategy_type"] == "sma_crossover":

        required_period = config["slow_period"]

        if len(candles) <= required_period + 1:
            raise ValueError(
                "Not enough historical candles for the selected "
                "slow SMA period."
            )

        strategy = SmaCrossStrategy(
            fast_period=config["fast_period"],
            slow_period=config["slow_period"],
        )

    elif config["strategy_type"] == "condition_based":

        indicators = config["indicators"]

        required_period = max(
            indicator["parameters"]["period"]
            for indicator in indicators
        )

        if len(candles) <= required_period:
            raise ValueError(
                "Not enough historical candles for the selected "
                "indicator periods."
            )

        strategy = ConditionBasedStrategy(
            candles=candles,
            specification=config,
        )

    else:
        raise ValueError(
            f"Unsupported strategy type: {config['strategy_type']}"
        )

    # Create the existing backtest engine.
    engine = BacktestEngine(
        initial_capital=str(config["initial_capital"]),
        quote_per_trade=str(config["quote_per_trade"]),
        fee_percentage_per_side=str(
            config["fee_percentage_per_side"]
        ),
        slippage_bps=str(config["slippage_bps"]),
        stop_loss_percentage=str(
            config["stop_loss_percentage"]
        ),
        take_profit_percentage=str(
            config["take_profit_percentage"]
        ),
    )

    # Measure actual Python backtest engine execution.
    start_time = time.perf_counter()

    results = engine.run(
        candles=candles,
        strategy=strategy,
    )

    execution_time = time.perf_counter() - start_time

    if generate_report:
        generate_backtest_report(results)

    return {
        "results": results,
        "execution_time_seconds": round(execution_time, 6),
        "candles_processed": len(candles),
        "dataset": DATASET_PATH.name,
    }

# --------------------------------------------------
# MAIN APPLICATION
# --------------------------------------------------

def main():

    print("\n========================================")
    print("          TRADESIM AI BACKTEST")
    print("========================================")

    print("Describe a strategy you want to backtest.")
    print("Type /exit to quit.")
    print("========================================\n")

    while True:

        user_prompt = input("\nYou: ").strip()

        if not user_prompt:
            continue

        if user_prompt.lower() == "/exit":
            print("\nExiting TradeSim.")
            break

        try:

            # Step 1: AI interpretation
            print("\nGemini is understanding your strategy...")

            ai_result = interpret_strategy(user_prompt)

            print("\n--- GEMINI INTERPRETATION ---")
            print(ai_result.get("user_explanation", ""))

            if ai_result.get("needs_clarification"):
                print("\nClarification required:")

                question = ai_result.get(
                    "clarification_question"
                )

                if question:
                    print(question)

                continue

            if ai_result.get("missing_information"):
                print("\nMissing information:")

                for item in ai_result["missing_information"]:
                    print(f"- {item}")

                continue

            # Step 2: Track which defaults are being applied
            used_defaults = {
                key: ai_result.get(key) is None
                for key in DEFAULT_SETTINGS
            }

            # Step 3: Python validation
            print("\nValidating strategy parameters...")

            config = validate_strategy(ai_result)

            # Step 4: Show validated strategy
            print("\n--- VALIDATED STRATEGY CONFIGURATION ---")

            for key in (
                "asset",
                "market_type",
                "timeframe",
                "strategy_type",
                "fast_period",
                "slow_period",
                "stop_loss_percentage",
                "take_profit_percentage",
            ):
                print(f"{key}: {config[key]}")

            # Step 5: Show portfolio and execution settings
            print("\nBACKTEST SETTINGS")

            print(
                f"Initial capital: "
                f"{config['initial_capital']} USDT"
            )

            print(
                f"Quote per trade: "
                f"{config['quote_per_trade']} USDT"
            )

            print(
                f"Fee per side: "
                f"{config['fee_percentage_per_side']}%"
            )

            print(
                f"Slippage: "
                f"{config['slippage_bps']} bps"
            )

            print(
                "Dataset: Full available BTCUSDT Spot 1h history"
            )

            # Step 6: Explain defaults only when applied
            default_labels = {
                "initial_capital": "Initial capital",
                "quote_per_trade": "Quote per trade",
                "fee_percentage_per_side": "Fee per side",
                "slippage_bps": "Slippage",
                "stop_loss_percentage": "Stop-loss",
                "take_profit_percentage": "Take-profit",
            }

            applied_defaults = [
                f"{default_labels[key]}: {DEFAULT_SETTINGS[key]}"
                for key, was_defaulted in used_defaults.items()
                if was_defaulted
            ]

            if applied_defaults:
                print("\nDefault values applied:")

                for item in applied_defaults:
                    print(f"- {item}")

            # Step 7: Confirmation
            confirmation = input(
                "\nRun this backtest? (yes/no): "
            ).strip().lower()

            if confirmation not in ("yes", "y"):
                print("\nBacktest cancelled.")
                continue

            # Step 8: Execute Python backtest
            run_ai_backtest(config)

        except Exception as error:
            print(f"\nTradeSim error: {error}")

            print(
                "\nNo backtest was reported as successful "
                "unless the Python engine completed it."
            )


if __name__ == "__main__":
    main()
