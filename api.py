
import os
from decimal import Decimal
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from ai_backtest import (
    DEFAULT_SETTINGS,
    interpret_strategy,
    validate_strategy,
)

from backtest_jobs import (
    start_backtest,
    get_backtest,
)

from ai_service import (
    process_chat_message,
    reset_session,
)

from binance_market import (
    get_symbol_rules,
    get_leverage_brackets,
)

from calculator import calculate_trade_size

from state_validator import MAX_RISK_PERCENTAGE


app = FastAPI(
    title="TradeSim API",
    description="Backend API for the TradeSim trading simulator.",
    version="1.1.0",
)


# Allow the React development server to communicate with this API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class PositionSizeRequest(BaseModel):

    symbol: str = Field(min_length=1, max_length=20)

    market_type: Literal["spot", "futures"] = "spot"

    order_type: Literal["MARKET", "LIMIT"] = "MARKET"

    capital: Decimal = Field(gt=0)

    capital_currency: str = Field(min_length=1, max_length=10)

    risk_percentage: Decimal = Field(
        gt=0,
        le=MAX_RISK_PERCENTAGE,
    )

    entry_price: Decimal = Field(gt=0)

    stop_loss: Decimal = Field(gt=0)

    side: Literal["long", "short"] = "long"

    fee_percentage_per_side: Decimal = Field(
        default=Decimal("0.1"),
        ge=0,
    )

    slippage_bps: Decimal = Field(
        default=Decimal("5"),
        ge=0,
    )

    leverage: Decimal = Field(
        default=Decimal("1"),
        ge=1,
    )

    additional_isolated_margin: Decimal = Field(
        default=Decimal("0"),
        ge=0,
    )
class AIChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=5000)
    session_id: str | None = None
class BacktestPrepareRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=5000)


class BacktestStartRequest(BaseModel):
    config: dict

@app.get("/")
def root():

    return {
        "name": "TradeSim API",
        "status": "running",
        "version": "1.1.0",
    }


@app.get("/api/health")
def health_check():

    return {
        "status": "healthy",
        "service": "TradeSim API",
    }


@app.post("/api/calculator/position-size")
def calculate_position_size(request: PositionSizeRequest):

    try:

        # 1. Fetch current public Binance trading rules.
        rules = get_symbol_rules(
            symbol=request.symbol,
            market_type=request.market_type,
            order_type=request.order_type,
        )

        leverage_brackets = None
        liquidation_note = None

        # 2. Retrieve account-specific Futures brackets if available.
        if request.market_type == "futures":

            api_key = os.getenv("BINANCE_API_KEY")
            api_secret = os.getenv("BINANCE_API_SECRET")

            if api_key and api_secret:

                try:

                    leverage_brackets = get_leverage_brackets(
                        request.symbol
                    )

                except (RuntimeError, ValueError) as error:

                    liquidation_note = (
                        "Leverage brackets could not be retrieved. "
                        "Position sizing will continue without a "
                        "liquidation estimate."
                    )

                    print(f"Leverage bracket warning: {error}")

            else:

                liquidation_note = (
                    "Binance API credentials are not configured. "
                    "Position sizing is available, but liquidation "
                    "estimation requires account-specific brackets."
                )

        # 3. Perform deterministic Python calculation.
        result = calculate_trade_size(
            capital=request.capital,
            risk_percentage=request.risk_percentage,
            entry_price=request.entry_price,
            stop_loss=request.stop_loss,
            capital_currency=request.capital_currency,
            rules=rules,
            side=request.side,
            fee_percentage_per_side=request.fee_percentage_per_side,
            slippage_bps=request.slippage_bps,
            leverage=request.leverage,
            leverage_brackets=leverage_brackets,
            additional_isolated_margin=request.additional_isolated_margin,
        )

        # 4. Add liquidation-estimation information.
        result["liquidation_note"] = liquidation_note

        return result

    except ValueError as error:

        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error

    except RuntimeError as error:

        raise HTTPException(
            status_code=502,
            detail=str(error),
        ) from error

@app.post("/api/ai/chat")
def ai_chat(request: AIChatRequest):

    try:
        return process_chat_message(
            message=request.message,
            session_id=request.session_id,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error

    except RuntimeError as error:
        raise HTTPException(
            status_code=502,
            detail=str(error),
        ) from error


@app.post("/api/ai/reset/{session_id}")
def ai_reset(session_id: str):

    reset_session(session_id)

    return {
        "success": True,
        "message": "AI conversation reset.",
    }


@app.post("/api/backtests/prepare")
def prepare_backtest(request: BacktestPrepareRequest):
    """
    Interpret a natural-language request and validate its
    strategy configuration. This endpoint does NOT run a backtest.
    """
    try:
        interpretation = interpret_strategy(request.prompt)

        if (
            interpretation.get("needs_clarification")
            or interpretation.get("missing_information")
        ):
            return {
                "ready": False,
                "interpretation": interpretation,
                "config": None,
                "defaults_applied": [],
            }

        raw_config = interpretation

        defaults_applied = [
            {
                "field": key,
                "value": DEFAULT_SETTINGS[key],
            }
            for key in DEFAULT_SETTINGS
            if raw_config.get(key) is None
        ]

        validated_config = validate_strategy(raw_config)

        return {
            "ready": True,
            "interpretation": interpretation,
            "config": validated_config,
            "defaults_applied": defaults_applied,
            "message": (
                "Backtest configuration validated. "
                "Review the settings before starting execution."
            ),
        }

    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error

    except RuntimeError as error:
        raise HTTPException(
            status_code=502,
            detail=str(error),
        ) from error


@app.post("/api/backtests/start")
def begin_backtest(request: BacktestStartRequest):
    """
    Start a confirmed backtest in the background.
    """
    try:
        # Always validate again at the execution boundary.
        validated_config = validate_strategy(request.config)

        job = start_backtest(validated_config)

        return {
            "message": "Backtest execution accepted.",
            "job": job,
        }

    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error


@app.get("/api/backtests/{run_id}")
def backtest_status(run_id: str):
    """
    Retrieve execution status or the completed backtest report.
    """
    job = get_backtest(run_id)

    if job is None:
        raise HTTPException(
            status_code=404,
            detail="Backtest run was not found.",
        )

    return job
