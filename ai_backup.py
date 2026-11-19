
import os
import json
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

# ---------------- CONFIGURATION ----------------

MODEL = "gemini-3.5-flash-lite"

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY not found in .env")

client = genai.Client(api_key=api_key)


# ---------------- TRADING STATE ----------------

def empty_state():
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
        "exit_condition": None
    }


trading_state = empty_state()


# ---------------- AI INSTRUCTIONS ----------------

SYSTEM_PROMPT = """
You are TradeSim's intelligent trading assistant.

Your job is to understand trading instructions in ordinary
human language, including informal, vague and incomplete prompts.

You have access to previous conversation messages and the
current structured trading state.

IMPORTANT RULES:

1. Remember information provided in previous messages.
2. If the user changes a value, update that value.
3. Do not forget previously established information.
4. Extract new information from the latest user message.
5. Never invent missing values.
6. Never assume a currency.
7. Keep capital currency separate from asset price currency.
8. Ask questions when essential information is missing.
9. Never perform financial calculations yourself.
10. Never claim a backtest has been executed.
11. Explain technical concepts in simple language.
12. A strategy can be created before capital and risk are known.
13. A backtest requires sufficiently defined entry and exit rules,
    historical data and execution assumptions.
14. Do not ask for capital or risk unless needed for the
    requested operation.
15. If the user says something like "make it 2% instead",
    identify which existing value they are changing.

STATE UPDATE RULE:

Return only information explicitly provided or corrected
in the latest user message.

For unchanged or unknown fields, return null.
The Python program will preserve existing values.

If the user explicitly corrects an earlier value, return
the corrected value.

Return only valid JSON matching the provided schema.
"""


# ---------------- RESPONSE SCHEMA ----------------

response_schema = {
    "type": "OBJECT",
    "properties": {
        "intent": {
            "type": "STRING",
            "enum": [
                "create_strategy",
                "calculate_position_size",
                "backtest",
                "explain",
                "update_strategy",
                "other"
            ]
        },
        "asset": {
            "type": "STRING",
            "nullable": True
        },
        "strategy_type": {
            "type": "STRING",
            "nullable": True
        },
        "capital": {
            "type": "NUMBER",
            "nullable": True
        },
        "capital_currency": {
            "type": "STRING",
            "nullable": True
        },
        "risk_percentage": {
            "type": "NUMBER",
            "nullable": True
        },
        "risk_amount": {
            "type": "NUMBER",
            "nullable": True
        },
        "entry_price": {
            "type": "NUMBER",
            "nullable": True
        },
        "stop_loss": {
            "type": "NUMBER",
            "nullable": True
        },
        "price_currency": {
            "type": "STRING",
            "nullable": True
        },
        "backtest_period": {
            "type": "STRING",
            "nullable": True
        },
        "entry_condition": {
            "type": "STRING",
            "nullable": True
        },
        "exit_condition": {
            "type": "STRING",
            "nullable": True
        },
        "missing_information": {
            "type": "ARRAY",
            "items": {
                "type": "STRING"
            }
        },
        "needs_clarification": {
            "type": "BOOLEAN"
        },
        "clarification_question": {
            "type": "STRING",
            "nullable": True
        },
        "ready_for_backtest": {
            "type": "BOOLEAN"
        },
        "user_explanation": {
            "type": "STRING"
        }
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
        "user_explanation"
    ]
}


# ---------------- CHAT SESSION ----------------

def create_chat():
    return client.chats.create(
        model=MODEL,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=0.1,
            response_mime_type="application/json",
            response_schema=response_schema
        )
    )


chat = create_chat()


# ---------------- STATE MANAGEMENT ----------------

def update_state(result):
    global trading_state

    for key in trading_state:
        value = result.get(key)

        if value is not None:
            trading_state[key] = value


def show_state():
    print("\n========== CURRENT TRADING STATE ==========")
    print(json.dumps(trading_state, indent=4))
    print("===========================================")


# ---------------- MAIN LOOP ----------------

print("\n========== TRADESIM AI ==========")
print("Commands: /state | /reset | /exit")

while True:

    prompt = input("\nYou: ").strip()

    if not prompt:
        continue

    if prompt.lower() == "/exit":
        break

    if prompt.lower() == "/state":
        show_state()
        continue

    if prompt.lower() == "/reset":
        trading_state = empty_state()
        chat = create_chat()
        print("\nConversation and trading state reset.")
        continue

    # Provide the latest structured state to Gemini.
    context = f"""
CURRENT STRUCTURED TRADING STATE:
{json.dumps(trading_state, indent=2)}

LATEST USER MESSAGE:
{prompt}

Interpret the latest message using the previous conversation
and the current trading state.

Return only newly provided or corrected values.
Return null for unchanged fields.
"""

    try:

        response = chat.send_message(context)

        if not response.text:
            print("\nAI returned an empty response.")
            continue

        result = json.loads(response.text)

        # Update Python's structured state.
        update_state(result)

        print("\n========== TRADESIM AI ==========")

        print("\nIntent:", result["intent"])

        print("\nExplanation:")
        print(result["user_explanation"])

        if result["needs_clarification"]:
            print("\nClarification needed:")
            print(result["clarification_question"])

        print("\n========== UPDATED STATE ==========")
        show_state()

        print("\nReady for backtest:",
              result["ready_for_backtest"])

        print("\n==================================")

    except json.JSONDecodeError:
        print("\nError: Invalid JSON returned by AI.")

    except Exception as e:
        print(f"\nError: {type(e).__name__}: {e}")

print("\nTradeSim AI session ended.")
