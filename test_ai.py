
import os
import json

from dotenv import load_dotenv
from google import genai
from google.genai import types

from calculator import calculate_trade_size
from binance_market import get_symbol_rules
from state_validator import validate_trading_state
from state_manager import load_state, save_state, reset_saved_state

# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError(
        "GEMINI_API_KEY was not found. Check your .env file."
    )

client = genai.Client(api_key=api_key)

MODEL = "gemini-3.5-flash-lite"


# --------------------------------------------------
# TRADING STATE
# --------------------------------------------------

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


trading_state = create_empty_state()


# --------------------------------------------------
# SYSTEM INSTRUCTIONS
# --------------------------------------------------

SYSTEM_PROMPT = """
You are TradeSim, an AI assistant inside a trading simulation
and strategy-testing application.

Your job is to understand the user's trading instructions,
extract information, maintain context, and classify their intent.

You do NOT perform financial calculations.
Python performs all calculations.
You do NOT claim that a backtest has been performed unless
a real backtesting engine has actually run.

INTENT CLASSIFICATION:

Choose exactly one intent:

1. create_strategy
   The user wants to create or define a new trading strategy.

2. update_strategy
   The user changes or corrects an existing parameter or condition.
   Examples:
   - "Change my risk to 1%."
   - "Actually, my capital is 25000."
   - "Move my stop loss to 88000."
   - "Use Ethereum instead."

3. calculate_position_size
   The user explicitly asks for position sizing or asks how much
   they can buy based on their capital, entry price and stop loss.
   Examples:
   - "Calculate my position size."
   - "How much Bitcoin can I buy?"
   - "Calculate the quantity for this trade."

4. backtest
   The user explicitly asks to test a strategy against historical data.

5. explain
   The user asks a question or requests an explanation of existing
   information or trading concepts.

6. other
   General trading conversation that does not fit the categories above.

IMPORTANT INTENT RULES:

- Changing an existing value alone is update_strategy.
- Do NOT classify every parameter update as calculate_position_size.
- If the user explicitly asks for a calculation, use
  calculate_position_size.
- If the user only asks to change their risk percentage,
  use update_strategy.
- A user asking what their current values are should normally
  be classified as explain.
- Do not invent missing values.
- Do not assume currencies.
- Do not assume an asset if it is not clear.
- Use the conversation history and current trading state.
- Return only newly provided or corrected values.
- Return null for values that have not changed.
- Never erase an existing value just because it was not mentioned.
- Do not calculate position size yourself.
- Do not claim that a backtest has been performed.

POSITION-SIZING INFORMATION:

A position-size calculation requires:
- capital
- capital_currency
- risk_percentage
- entry_price
- stop_loss
- price_currency

If the user gives a fixed risk amount instead of a percentage,
extract it as risk_amount. Do not invent a risk percentage.

STRATEGY INFORMATION:

A strategy can be defined without knowing the user's capital
or risk percentage.

For a strategy, extract:
- asset
- strategy_type
- entry_condition
- exit_condition

BACKTESTING:

If the user requests a backtest, extract the requested period
and strategy information. Do not say the backtest is complete.
The actual backtesting engine is a separate Python component.

CLARIFICATION:

If information required for the user's requested task is missing,
list the missing information and ask one clear question.

Do not ask for information that is not required for the current task.

USER EXPLANATION:

Give a short, clear explanation of what you understood.
Do not give guaranteed profit or loss claims.
Do not present a strategy as profitable without evidence.
"""


# --------------------------------------------------
# RESPONSE SCHEMA
# --------------------------------------------------

response_schema = {
    "type": "OBJECT",
    "properties": {
        "intent": {
            "type": "STRING",
            "enum": [
                "create_strategy",
                "update_strategy",
                "calculate_position_size",
                "backtest",
                "explain",
                "other",
            ],
        },
        "asset": {
            "type": "STRING",
            "nullable": True,
        },
        "strategy_type": {
            "type": "STRING",
            "nullable": True,
        },
        "capital": {
            "type": "NUMBER",
            "nullable": True,
        },
        "capital_currency": {
            "type": "STRING",
            "nullable": True,
        },
        "risk_percentage": {
            "type": "NUMBER",
            "nullable": True,
        },
        "risk_amount": {
            "type": "NUMBER",
            "nullable": True,
        },
        "entry_price": {
            "type": "NUMBER",
            "nullable": True,
        },
        "stop_loss": {
            "type": "NUMBER",
            "nullable": True,
        },
        "price_currency": {
            "type": "STRING",
            "nullable": True,
        },
        "backtest_period": {
            "type": "STRING",
            "nullable": True,
        },
        "entry_condition": {
            "type": "STRING",
            "nullable": True,
        },
        "exit_condition": {
            "type": "STRING",
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
        "ready_for_backtest": {
            "type": "BOOLEAN",
        },
        "user_explanation": {
            "type": "STRING",
        },
    },
    "required": [
        "intent",
        "asset",
        "strategy_type",
        "capital",
        "capital_currency",
        "risk_percentage",
        "risk_amount",
        "entry_price",
        "stop_loss",
        "price_currency",
        "backtest_period",
        "entry_condition",
        "exit_condition",
        "missing_information",
        "needs_clarification",
        "clarification_question",
        "ready_for_backtest",
        "user_explanation",
    ],
}


# --------------------------------------------------
# CHAT CREATION
# --------------------------------------------------

def create_chat():
    return client.chats.create(
        model=MODEL,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=0.1,
            response_mime_type="application/json",
            response_schema=response_schema,
        ),
    )


def reset_chat_with_current_state():
    """Reset Gemini conversation using Python's authoritative state."""

    global chat

    chat = create_chat()

    chat.send_message(
        f"""
The following is the authoritative current trading state
maintained by the Python application.

CURRENT TRADING STATE:

{json.dumps(trading_state, indent=2)}

IMPORTANT RULES:

1. Treat this state as the source of truth.
2. Previous rejected updates must not be treated as successful.
3. Never assume a value changed unless Python confirms it.
4. Do not invent missing trading information.
5. Continue understanding the user's next instruction
   using this current state.
"""
    )


chat = create_chat()


# --------------------------------------------------
# STATE MANAGEMENT
# --------------------------------------------------

def normalize_currency(currency):
    """Convert common currency names and symbols to standard codes."""

    if currency is None:
        return None

    value = currency.strip().upper()

    aliases = {
        "RUPEE": "INR",
        "RUPEES": "INR",
        "RS": "INR",
        "RS.": "INR",
        "₹": "INR",
        "INDIAN RUPEE": "INR",
        "INDIAN RUPEES": "INR",
        "DOLLAR": "USD",
        "DOLLARS": "USD",
        "$": "USD",
    }

    return aliases.get(value, value)




def update_state(result):
    """Validate, save and then commit proposed trading-state updates."""

    global trading_state

    proposed_state = trading_state.copy()

    # Apply proposed values to a temporary copy.
    for key in proposed_state.keys():
        new_value = result.get(key)

        if new_value is not None:
            if key in ("capital_currency", "price_currency"):
                new_value = normalize_currency(new_value)

            proposed_state[key] = new_value

    # Validate before saving or changing the current state.
    valid, message = validate_trading_state(
        proposed_state,
        require_complete=False
    )

    if not valid:
        print("\n--- STATE UPDATE REJECTED ---")
        print(f"Reason: {message}")
        print("Previous trading state has been preserved.")
        print("-----------------------------\n")
        return False

    # Avoid unnecessary disk writes if nothing changed.
    if proposed_state == trading_state:
        return True

    # Save first. Commit in-memory state only if saving succeeds.
    try:
        save_state(proposed_state)

    except Exception as error:
        print("\n--- STATE SAVE FAILED ---")
        print(f"Reason: {error}")
        print("Previous trading state has been preserved.")
        print("-------------------------\n")
        return False

    trading_state = proposed_state

    return True

def display_state():
    print("\n--- CURRENT TRADING STATE ---")

    for key, value in trading_state.items():
        print(f"{key}: {value}")

    print("-----------------------------\n")


# --------------------------------------------------
# POSITION-SIZING VALIDATION
# --------------------------------------------------


def validate_position_inputs(state):
    """Validate that all required calculation inputs are available."""

    return validate_trading_state(
        state,
        require_complete=True
    )

# --------------------------------------------------
# PYTHON CALCULATION ENGINE
# --------------------------------------------------
def resolve_binance_symbol(asset):
    if not asset:
        raise ValueError("Trading asset has not been specified.")

    asset = asset.strip().upper()

    supported_assets = {
        "BITCOIN": "BTCUSDT",
        "BTC": "BTCUSDT",
        "BTCUSDT": "BTCUSDT",
    }

    if asset not in supported_assets:
        raise ValueError(
            f"Asset '{asset}' is not supported yet. "
            "Currently, only Bitcoin (BTCUSDT) is supported."
        )

    return supported_assets[asset]

def run_calculation(state):
    valid, message = validate_position_inputs(state)

    if not valid:
        print(f"\nCannot calculate position size: {message}\n")
        return

    try:
        symbol = resolve_binance_symbol(state["asset"])

        # Fetch actual Binance trading rules.
        rules = get_symbol_rules(
            symbol=symbol,
            market_type="spot",
            order_type="MARKET",
        )

        # Perform deterministic Python calculation.
        result = calculate_trade_size(
            capital=state["capital"],
            risk_percentage=state["risk_percentage"],
            entry_price=state["entry_price"],
            stop_loss=state["stop_loss"],
            capital_currency=state["capital_currency"],
            rules=rules,
            side="long",
            fee_percentage_per_side="0.1",
            slippage_bps="5",
        )

    except (ValueError, RuntimeError, KeyError) as error:
        print(f"\nCalculation error: {error}\n")
        return

    print("\n========== PYTHON CALCULATION ==========")

    for key, value in result.items():
        print(f"{key}: {value}")

    print("========================================\n")

    # Ask Gemini to explain verified Python results.
    try:
        explanation = client.models.generate_content(
            model=MODEL,
            contents=f"""
You are explaining verified calculations performed by
the TradeSim Python calculation engine.

Explain the results in simple, beginner-friendly language.

STRICT RULES:

1. Do not modify, estimate or recalculate any numbers.
2. Never guarantee a particular profit or loss.
3. Describe the loss as an estimate if the position is
   closed at the specified stop-loss price.
4. Explain that actual execution may differ because of
   slippage, liquidity, fees and market gaps.
5. Never claim that a stop-loss guarantees protection.
6. Never claim that the application has placed an order.
7. Explain position quantity, position value and estimated loss.
8. Mention the currency shown in the calculation.
9. Be concise.
10. Do not recommend buying or selling the asset.

Verified Python calculation results:

{json.dumps(result, indent=2)}
""",
        )

        print("--- AI EXPLANATION ---")
        print(explanation.text)
        print("----------------------\n")

    except Exception as error:
        print(
            "\nThe calculation succeeded, but the AI explanation "
            f"could not be generated: {error}\n"
        )

# --------------------------------------------------
# MAIN APPLICATION LOOP
# --------------------------------------------------

def main():

    global trading_state, chat

    # Restore previously saved trading state.
    trading_state, state_message = load_state(create_empty_state())

    print(f"\n{state_message}")

    # Give Gemini the restored state as authoritative context.
    reset_chat_with_current_state()

    print("\n======================================")
    print("       TRADESIM AI TEST ENVIRONMENT")
    print("======================================")
    print("Describe your trading idea in normal language.")
    print("Commands:")
    print("  /state     - View current trading information")
    print("  /calculate - Calculate position size")
    print("  /reset     - Clear current trading information")
    print("  /exit      - Exit TradeSim")
    print("======================================\n")

    while True:

        user_input = input("You: ").strip()

        if not user_input:
            continue

        # Exit
        if user_input.lower() == "/exit":
            print("\nExiting TradeSim. Goodbye!")
            break

        # View current state
        if user_input.lower() == "/state":
            display_state()
            continue

        # Reset state and conversation
                # Reset state, saved file and conversation
        if user_input.lower() == "/reset":

            try:
                reset_saved_state()

            except RuntimeError as error:
                print(f"\nReset failed: {error}")
                print("Your existing trading state was preserved.\n")
                continue

            trading_state = create_empty_state()
            chat = create_chat()

            print("\nTrading state, saved data and conversation reset.\n")
            continue

        # Manually request calculation
        if user_input.lower() == "/calculate":
            run_calculation(trading_state)
            continue

        # Send current state and user message to Gemini
        context = f"""
CURRENT TRADING STATE:

{json.dumps(trading_state, indent=2)}

USER MESSAGE:

{user_input}

Understand the user's message using the current state.
Return only the required structured JSON response.
"""

        try:
            response = chat.send_message(context)
            result = json.loads(response.text)

        except Exception as error:
            print(f"\nAI error: {error}\n")
            continue

        # Update Python state
        update_success = update_state(result)

        # Correct the AI response if Python rejects the update
        if not update_success:

            reset_chat_with_current_state()

            result["user_explanation"] = (
                "Your requested update was rejected because "
                "it violates the trading configuration rules. "
                "Your previous trading state has been preserved."
            )

        # Display AI response
        print("\n--- TRADESIM RESPONSE ---")
        print(f"Intent: {result['intent']}")

        if result.get("user_explanation"):
            print(f"\n{result['user_explanation']}")

        if result.get("missing_information"):
            print("\nMissing information:")

            for item in result["missing_information"]:
                print(f"- {item}")

        if result.get("needs_clarification"):
            question = result.get("clarification_question")

            if question:
                print(f"\nQuestion: {question}")

        print("-------------------------")

        # Show updated state
        display_state()

        # Calculate only when explicitly requested
        if result["intent"] == "calculate_position_size":
            run_calculation(trading_state)


if __name__ == "__main__":
    main()
