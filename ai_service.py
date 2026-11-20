import json
import os
import uuid
import re

from decimal import Decimal

from dotenv import load_dotenv
from google import genai
from google.genai import types

from calculator import calculate_trade_size
from binance_market import get_symbol_rules, get_leverage_brackets
from state_validator import validate_trading_state


load_dotenv()

MODEL = "gemini-3.5-flash-lite"

MAX_RISK_PERCENTAGE = Decimal("5")

# Development-only session storage.
# Each session has its own Gemini chat and trading state.
SESSIONS = {}


SYSTEM_PROMPT = """
You are TradeSim, an AI assistant inside a trading simulation application.

Your responsibilities:
1. Understand natural-language trading instructions.
2. Extract trading parameters into the supplied JSON schema.
3. Maintain conversation context.
4. Identify missing information.
5. Explain verified Python calculation results when provided.

IMPORTANT:
- You do not perform financial calculations.
- Python is responsible for all calculations.
- Never invent missing trading values.
- Never assume a currency, asset, market type, or trading side.
- Return only newly provided or corrected values.
- Return null for values that have not changed.
- Never erase an existing value just because it was not mentioned.
- Never claim a calculation or backtest has been performed unless Python confirms it.

INTENTS:
- create_strategy
- update_strategy
- calculate_position_size
- backtest
- explain
- other

POSITION SIZING:
A calculation requires:
- asset
- market_type
- side
- capital
- capital_currency
- risk_percentage
- entry_price
- stop_loss

For Spot:
- Only Long positions are supported.

For USD-M Futures:
- Long and Short positions are supported.
- Extract leverage when supplied.
- Do not invent leverage.

RISK POLICY:
- TradeSim currently permits a maximum risk of 5%.
- Do not silently change a user's requested risk.
- Python will validate the risk.

CLARIFICATION:
- If required information is missing, list it.
- Ask one clear question.
- Do not calculate with incomplete information.

BACKTESTING:
- Extract strategy and requested period.
- Do not claim a backtest has been run.

USER EXPLANATION:
- Be concise and beginner-friendly.
- Do not recommend buying or selling.
- Do not promise profits or guarantee protection.
"""

CONVERSATIONAL_SYSTEM_PROMPT = """
You are TradeSim, a knowledgeable and helpful AI assistant
inside a trading simulation application.

YOUR ROLE:
- Explain trading concepts clearly.
- Help users understand trading strategies and indicators.
- Explain Spot and Futures trading.
- Explain position sizing, leverage, fees, risk, and stop-loss.
- Answer questions about the TradeSim application.
- Maintain context from previous messages.
- Ask follow-up questions when the user's request is unclear.

RESPONSE STYLE:
- Be conversational, natural, and helpful.
- Give explanations appropriate for a beginner.
- Use headings and bullet points when they improve readability.
- Explain technical terms rather than assuming the user knows them.
- Avoid unnecessarily short or generic answers.
- Give examples when they help explain a concept.
- Answer the actual question instead of repeating generic disclaimers.

TRADING SAFETY:
- Never guarantee profits.
- Never claim a trade has been executed.
- Never invent live market prices or calculation results.
- Never present estimates as verified calculations.
- Do not make unsupported buy or sell recommendations.

IMPORTANT:
- You are responsible for explanations, not financial calculations.
- Python performs all authoritative trading calculations.
- If a user requests a calculation, explain that the required
  trading details must be provided to the calculation workflow.
"""

RESPONSE_SCHEMA = {
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
        "asset": {"type": "STRING", "nullable": True},
        "strategy_type": {"type": "STRING", "nullable": True},
        "market_type": {
            "type": "STRING",
            "enum": ["spot", "futures"],
            "nullable": True,
        },
        "side": {
            "type": "STRING",
            "enum": ["long", "short"],
            "nullable": True,
        },
        "order_type": {
            "type": "STRING",
            "enum": ["MARKET", "LIMIT"],
            "nullable": True,
        },
        "capital": {"type": "NUMBER", "nullable": True},
        "capital_currency": {"type": "STRING", "nullable": True},
        "risk_percentage": {"type": "NUMBER", "nullable": True},
        "risk_amount": {"type": "NUMBER", "nullable": True},
        "entry_price": {"type": "NUMBER", "nullable": True},
        "stop_loss": {"type": "NUMBER", "nullable": True},
        "price_currency": {"type": "STRING", "nullable": True},
        "leverage": {"type": "NUMBER", "nullable": True},
        "fee_percentage_per_side": {"type": "NUMBER", "nullable": True},
        "slippage_bps": {"type": "NUMBER", "nullable": True},
        "additional_isolated_margin": {"type": "NUMBER", "nullable": True},
        "backtest_period": {"type": "STRING", "nullable": True},
        "entry_condition": {"type": "STRING", "nullable": True},
        "exit_condition": {"type": "STRING", "nullable": True},
        "missing_information": {
            "type": "ARRAY",
            "items": {"type": "STRING"},
        },
        "needs_clarification": {"type": "BOOLEAN"},
        "clarification_question": {"type": "STRING", "nullable": True},
        "ready_for_backtest": {"type": "BOOLEAN"},
        "user_explanation": {"type": "STRING"},
    },
    "required": [
        "intent",
        "asset",
        "strategy_type",
        "market_type",
        "side",
        "order_type",
        "capital",
        "capital_currency",
        "risk_percentage",
        "risk_amount",
        "entry_price",
        "stop_loss",
        "price_currency",
        "leverage",
        "fee_percentage_per_side",
        "slippage_bps",
        "additional_isolated_margin",
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


def create_empty_state():
    return {
        "asset": None,
        "strategy_type": None,
        "market_type": None,
        "side": None,
        "order_type": None,
        "capital": None,
        "capital_currency": None,
        "risk_percentage": None,
        "risk_amount": None,
        "entry_price": None,
        "stop_loss": None,
        "price_currency": None,
        "leverage": None,
        "fee_percentage_per_side": None,
        "slippage_bps": None,
        "additional_isolated_margin": None,
        "backtest_period": None,
        "entry_condition": None,
        "exit_condition": None,
    }


def get_gemini_client():
    """Create the Gemini client without exposing the API key."""

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is missing. Check your local .env file."
        )

    return genai.Client(api_key=api_key)



def create_session(user_id):
    """Create an AI conversation owned by one authenticated user."""

    client = get_gemini_client()

    trading_chat = client.chats.create(
        model=MODEL,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=0.1,
            response_mime_type="application/json",
            response_schema=RESPONSE_SCHEMA,
        ),
    )

    assistant_chat = client.chats.create(
        model=MODEL,
        config=types.GenerateContentConfig(
            system_instruction=CONVERSATIONAL_SYSTEM_PROMPT,
            temperature=0.6,
        ),
    )

    session_id = str(uuid.uuid4())

    SESSIONS[session_id] = {
        "user_id": user_id,
        "client": client,
        "trading_chat": trading_chat,
        "assistant_chat": assistant_chat,
        "state": create_empty_state(),
    }

    return session_id


def get_session(session_id=None, user_id=None):
    """Retrieve a conversation only if it belongs to the user."""

    if not user_id:
        raise ValueError("Authenticated user ID is required.")

    if session_id and session_id in SESSIONS:
        session = SESSIONS[session_id]

        if session.get("user_id") != user_id:
            raise PermissionError("AI session not found.")

        return session_id, session

    new_session_id = create_session(user_id)

    return new_session_id, SESSIONS[new_session_id]


def reset_session(session_id, user_id):
    """Delete a conversation only if it belongs to the user."""

    session = SESSIONS.get(session_id)

    if session is None or session.get("user_id") != user_id:
        return False

    SESSIONS.pop(session_id, None)

    return True


def normalize_currency(currency):
    if currency is None:
        return None

    value = str(currency).strip().upper()

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


def update_session_state(state, proposed):
    """Validate proposed updates before changing the session state."""

    updated = state.copy()

    for key in updated:
        value = proposed.get(key)

        if value is not None:
            if key in ("capital_currency", "price_currency"):
                value = normalize_currency(value)

            if key in ("market_type", "side"):
                value = str(value).lower()

            if key == "order_type":
                value = str(value).upper()

            updated[key] = value

    # Validate trading state.
    valid, message = validate_trading_state(
        updated,
        require_complete=False,
    )

    if not valid:
        return False, state, message

    # Validate additional fields.
    if updated["market_type"] not in (None, "spot", "futures"):
        return False, state, "Market type must be Spot or Futures."

    if updated["side"] not in (None, "long", "short"):
        return False, state, "Side must be Long or Short."

    if updated["order_type"] not in (None, "MARKET", "LIMIT"):
        return False, state, "Order type must be MARKET or LIMIT."

    if updated["market_type"] == "spot" and updated["side"] == "short":
        return False, state, "Short positions are not supported in Spot."

    if updated["leverage"] is not None:
        try:
            leverage = Decimal(str(updated["leverage"]))

            if not leverage.is_finite() or leverage < 1:
                return False, state, "Leverage must be at least 1x."

        except Exception:
            return False, state, "Leverage must be a valid number."

    return True, updated, "Trading state updated successfully."


def resolve_binance_symbol(asset):
    if not asset:
        raise ValueError("Trading asset has not been specified.")

    normalized = str(asset).strip().upper()

    supported_assets = {
        "BTC": "BTCUSDT",
        "BITCOIN": "BTCUSDT",
        "BTCUSDT": "BTCUSDT",
    }

    if normalized not in supported_assets:
        raise ValueError(
            f"Asset '{asset}' is not supported yet. "
            "Currently, BTCUSDT is supported."
        )

    return supported_assets[normalized]


def get_missing_calculation_fields(state):
    required = [
        "asset",
        "market_type",
        "side",
        "capital",
        "capital_currency",
        "risk_percentage",
        "entry_price",
        "stop_loss",
    ]

    missing = [
        field for field in required
        if state.get(field) is None
    ]

    if state.get("market_type") == "futures" and state.get("leverage") is None:
        missing.append("leverage")

    return missing


def run_position_calculation(state):
    """Run the existing deterministic Python calculation engine."""

    missing = get_missing_calculation_fields(state)

    if missing:
        return None, (
            "More information is required: " + ", ".join(missing)
        )

    try:
        symbol = resolve_binance_symbol(state["asset"])

        market_type = state["market_type"]
        side = state["side"]

        if market_type == "spot" and side != "long":
            raise ValueError("Spot supports Long positions only.")

        rules = get_symbol_rules(
            symbol=symbol,
            market_type=market_type,
            order_type=state.get("order_type") or "MARKET",
        )

        leverage_brackets = None
        liquidation_note = None

        if market_type == "futures":
            if os.getenv("BINANCE_API_KEY") and os.getenv("BINANCE_API_SECRET"):
                try:
                    leverage_brackets = get_leverage_brackets(symbol)
                except (RuntimeError, ValueError) as error:
                    liquidation_note = (
                        "Leverage brackets could not be retrieved. "
                        "Position sizing is available without a "
                        "liquidation estimate."
                    )
                    print(f"Leverage bracket warning: {error}")
            else:
                liquidation_note = (
                    "Binance API credentials are not configured. "
                    "Position sizing is available, but account-specific "
                    "liquidation estimation is unavailable."
                )

        result = calculate_trade_size(
            capital=state["capital"],
            risk_percentage=state["risk_percentage"],
            entry_price=state["entry_price"],
            stop_loss=state["stop_loss"],
            capital_currency=state["capital_currency"],
            rules=rules,
            side=side,
            fee_percentage_per_side=(
                state.get("fee_percentage_per_side") or "0.1"
            ),
            slippage_bps=state.get("slippage_bps") or "5",
            leverage=(
                state.get("leverage")
                if market_type == "futures"
                else "1"
            ),
            leverage_brackets=leverage_brackets,
            additional_isolated_margin=(
                state.get("additional_isolated_margin") or "0"
            ),
        )

        result["liquidation_note"] = liquidation_note

        return result, None

    except (ValueError, RuntimeError, KeyError) as error:
        return None, str(error)


def explain_calculation(client, result):
    """Ask Gemini to explain verified Python results without changing them."""

    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=f"""
Explain these verified TradeSim Python calculation results
in simple, beginner-friendly language.

Rules:
- Do not recalculate or change any numbers.
- Do not guarantee profit or loss.
- Describe loss as an estimate if the stop-loss is executed.
- Explain that actual execution can differ due to fees,
  slippage, liquidity and market gaps.
- Never claim an order has been placed.
- Do not recommend buying or selling.
- Be concise.

Verified Python results:
{json.dumps(result, indent=2, default=str)}
""",
        )

        return response.text or "Calculation completed successfully."

    except Exception:
        return (
            "The Python calculation succeeded, but the AI explanation "
            "could not be generated."
        )


def is_explanation_only_request(message):
    """Identify explanation requests that should bypass execution validation."""

    asks_for_explanation = re.search(
        r"\b(explain|describe|what is|what are|how does|how do|"
        r"advantages|disadvantages|pros and cons)\b",
        message,
        re.IGNORECASE,
    )

    requests_execution = re.search(
        r"\b(run|perform|execute|start|launch)\s+(?:a\s+)?"
        r"(backtest|back-testing|historical test|calculation)\b"
        r"|\b(calculate position size|calculate trade size)\b",
        message,
        re.IGNORECASE,
    )

    return bool(asks_for_explanation and not requests_execution)

def process_chat_message(message, session_id=None, user_id=None):
    """Main entry point used by the FastAPI chat endpoint."""

    if not isinstance(message, str) or not message.strip():
        raise ValueError("Message cannot be empty.")

    session_id, session = get_session(
        session_id=session_id,
        user_id=user_id,
    )

    trading_chat = session["trading_chat"]
    assistant_chat = session["assistant_chat"]
    current_state = session["state"]

    # Explanation-only requests bypass structured trading validation.
    if is_explanation_only_request(message):
        try:
            assistant_response = assistant_chat.send_message(
                f"""
Current authoritative trading state:
{json.dumps(current_state, indent=2, default=str)}

User message:
{message}

Explain the requested trading concept clearly.
You may explain indicators and strategies even if they
are not supported by the Python backtest engine.

Important:
- Do not perform a backtest.
- Do not perform financial calculations.
- Do not claim that a strategy has been executed.
- Explain any limitations only when relevant.
"""
            )

            explanation = (
                assistant_response.text
                or "I couldn't generate a response. Please try again."
            )

        except Exception as error:
            print(f"Conversational AI error: {error}")
            explanation = (
                "I'm having trouble generating a response right now. "
                "Please try again in a moment."
            )

        return {
            "session_id": session_id,
            "intent": "explain",
            "user_explanation": explanation,
            "needs_clarification": False,
            "clarification_question": None,
            "missing_information": [],
            "state": current_state,
            "state_message": "Explanation only. Trading state unchanged.",
            "calculation": None,
            "calculation_error": None,
            "ai_explanation": None,
        }


    context = f"""
CURRENT AUTHORITATIVE TRADING STATE:
{json.dumps(current_state, indent=2, default=str)}

USER MESSAGE:
{message}

Interpret this message using the current state.
Return only the structured JSON response.
"""

    response = trading_chat.send_message(context)

    try:
        interpretation = json.loads(response.text)
    except (TypeError, json.JSONDecodeError) as error:
        raise RuntimeError(
            "Gemini returned an invalid structured response."
        ) from error

    # Update state only after Python validation.
    success, updated_state, state_message = update_session_state(
        current_state,
        interpretation,
    )

    if success:
        session["state"] = updated_state
    else:
        # Do not retain a rejected Gemini proposal in conversation history.
        # Recreate the chat with the authoritative state.
        session["trading_chat"] = session["client"].chats.create(
            model=MODEL,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.1,
                response_mime_type="application/json",
                response_schema=RESPONSE_SCHEMA,
            ),
        )

        interpretation["user_explanation"] = (
            "I could not apply that update. "
            + state_message
            + " Your previous state has been preserved."
        )

        interpretation["needs_clarification"] = True

    state = session["state"]

    calculation = None
    calculation_error = None
    ai_explanation = None
        # Generate natural-language responses for ordinary conversations.
    if interpretation.get("intent") in ("explain", "other"):
        try:
            assistant_response = assistant_chat.send_message(
                f"""
Current authoritative trading state:
{json.dumps(state, indent=2, default=str)}

User message:
{message}

Respond naturally to the user's message.
Do not modify trading state.
Do not invent calculations or market data.
"""
            )

            interpretation["user_explanation"] = (
                assistant_response.text
                or "I couldn't generate a response. Please try again."
            )

        except Exception as error:
            print(f"Conversational AI error: {error}")

            interpretation["user_explanation"] = (
                "I'm having trouble generating a response right now. "
                "Please try again in a moment."
            )

    # Calculate only when the user explicitly requests position sizing.
    if (
        success
        and interpretation.get("intent") == "calculate_position_size"
    ):
        calculation, calculation_error = run_position_calculation(state)

        if calculation is not None:
            ai_explanation = explain_calculation(
                session["client"],
                calculation,
            )

    return {
        "session_id": session_id,
        "intent": interpretation.get("intent", "other"),
        "user_explanation": interpretation.get("user_explanation"),
        "needs_clarification": interpretation.get(
            "needs_clarification",
            False,
        ),
        "clarification_question": interpretation.get(
            "clarification_question"
        ),
        "missing_information": interpretation.get(
            "missing_information",
            [],
        ),
        "state": state,
        "state_message": state_message,
        "calculation": calculation,
        "calculation_error": calculation_error,
        "ai_explanation": ai_explanation,
    }