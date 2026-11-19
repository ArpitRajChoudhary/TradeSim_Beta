# TradeSim --- AI-Powered Trading Strategy Backtesting Platform

TradeSim is an AI-powered trading strategy interpretation and
backtesting platform. It allows users to describe trading strategies in
natural language and converts those descriptions into structured
strategy configurations that can be validated and executed by a Python
backtesting engine.

The platform combines Generative AI with rule-based validation and
historical market data to help users understand and evaluate trading
strategies without manually writing strategy code.

> **Note:** TradeSim is a research and backtesting platform. It does not
> execute live trades or place orders on an exchange.

## Features

-   **Natural Language Strategy Input:** Describe trading strategies
    using ordinary language.
-   **AI-Powered Strategy Interpretation:** Uses Google's Gemini API to
    convert descriptions into structured JSON configurations.
-   **Python-Based Validation:** Validates strategy parameters,
    indicators, conditions, and supported capabilities before execution.
-   **Technical Indicators:** Supports Simple Moving Average (SMA),
    Exponential Moving Average (EMA), and Relative Strength Index (RSI).
-   **Generic Strategy Conditions:** Supports condition-based strategies
    with AND/OR logic and comparison operators.
-   **Historical Backtesting:** Evaluates strategies against historical
    market candle data.
-   **Risk Management:** Supports stop-loss, take-profit, position
    sizing, fees, and slippage according to configured backtesting
    rules.
-   **Performance Metrics:** Calculates net P&L, percentage return, win
    rate, profit factor, and maximum drawdown.

## How It Works

1.  **User Input:** The user describes a trading strategy in natural
    language.
2.  **AI Interpretation:** Gemini converts the description into a
    structured JSON strategy configuration.
3.  **Backend Validation:** The Python backend checks strategy validity
    and verifies supported indicators, parameters, and conditions.
4.  **Indicator Calculation:** The backend calculates the required
    technical indicators from historical candle data.
5.  **Signal Generation:** The strategy engine evaluates entry and exit
    conditions.
6.  **Backtesting:** The backtesting engine simulates trades using
    historical data and configured execution rules.
7.  **Results:** The platform returns performance metrics and
    backtesting results.

## Technology Stack

  Component             Technology
  --------------------- -------------------------------------
  Frontend              React.js, Vite
  Backend               Python, FastAPI
  AI Integration        Google Gemini API
  Data Processing       Python
  Market Data           Historical BTCUSDT Spot candle data
  Strategy Indicators   SMA, EMA, RSI
  Testing               pytest

## Supported Strategy Capabilities

### Strategy Types

-   SMA Crossover Strategy
-   Generic Condition-Based Strategy

### Technical Indicators

-   Simple Moving Average (SMA)
-   Exponential Moving Average (EMA)
-   Relative Strength Index (RSI)

### Condition Evaluation

-   AND and OR logical operators
-   Comparison operators
-   Indicator-based conditions
-   Price-based conditions
-   Constant values
-   Volume-based conditions

### Current Backtesting Scope

-   Trading pair: BTCUSDT
-   Market: Spot
-   Timeframe: 1 hour
-   Historical data: Local CSV dataset
-   Position direction: Long-only

The supported market, timeframe, and strategy capabilities depend on the
current backend implementation.

## Project Structure

The following is an illustrative structure. Adjust it to match the
actual repository.

``` text
TradeSim/
├── backend/
│   ├── main.py
│   ├── ai_backtest.py
│   ├── indicators.py
│   ├── strategy_schema.py
│   ├── condition_engine.py
│   ├── generic_strategy.py
│   ├── backtest_engine.py
│   ├── backtest_data.py
│   ├── backtest_report.py
│   ├── strategies.py
│   ├── data/
│   │   └── historical/
│   ├── requirements.txt
│   └── .env
└── frontend/
    ├── src/
    ├── public/
    ├── package.json
    └── ...
```

## Installation and Setup

### Prerequisites

-   Python 3.10 or later
-   Node.js and npm
-   Git
-   Google Gemini API key

### 1. Clone the Repository

``` bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd TradeSim
```

### 2. Backend Setup

Navigate to the backend directory:

``` bash
cd backend
```

Create a virtual environment:

``` bash
python3 -m venv venv
```

Activate it on Linux/macOS:

``` bash
source venv/bin/activate
```

On Windows PowerShell:

``` powershell
venv\Scripts\Activate.ps1
```

Install dependencies:

``` bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file inside the backend directory:

``` env
GEMINI_API_KEY=your_gemini_api_key
```

Replace the placeholder with your actual Gemini API key.

**Important:** Never commit your `.env` file or expose API keys in the
GitHub repository.

### 4. Run the Backend

From the backend directory:

``` bash
uvicorn main:app --reload
```

The backend should be available at:

-   API: `http://127.0.0.1:8000`
-   Interactive API documentation: `http://127.0.0.1:8000/docs`

If your FastAPI application is defined in a different Python module or
variable, adjust `main:app` accordingly.

### 5. Frontend Setup

Open another terminal and navigate to the frontend directory:

``` bash
cd frontend
```

Install dependencies:

``` bash
npm install
```

Start the Vite development server:

``` bash
npm run dev
```

Open the local URL displayed in the terminal, commonly
`http://localhost:5173`.

## Running the Project

Run the backend and frontend in separate terminals.

**Terminal 1 --- Backend**

``` bash
cd backend
source venv/bin/activate
uvicorn main:app --reload
```

**Terminal 2 --- Frontend**

``` bash
cd frontend
npm run dev
```

Then open the frontend URL displayed by Vite.

## Testing

The project includes tests for strategy validation, indicator
calculations, condition evaluation, and backtesting integration.

Run individual test modules from the backend directory:

``` bash
python -m pytest -q test_strategy_validation.py
python -m pytest -q test_indicator_capabilities.py
python -m pytest -q test_generic_backtest_integration.py
python -m pytest -q test_sma_backtest_integration.py
```

Other isolated test modules can be run as needed:

``` bash
python -m pytest -q test_indicators.py
python -m pytest -q test_condition_engine.py
python -m pytest -q test_generic_strategy.py
```

Some legacy scripts in the repository may make live API or network
calls. Run isolated test modules rather than assuming every root-level
test script is safe for automated collection.

## Backtesting Results

The backtesting engine generates performance information including:

-   Initial capital
-   Final equity
-   Net profit or loss
-   Total return
-   Number of closed trades
-   Winning and losing trades
-   Win rate
-   Profit factor
-   Maximum drawdown
-   Trade exit reasons

These results help users evaluate how a strategy performed over the
available historical dataset.

**Note:** Backtesting results are historical simulations and do not
guarantee future performance.

## Limitations

-   Limited market-data coverage.
-   Currently focused on BTCUSDT Spot with a 1-hour timeframe.
-   No live exchange order execution.
-   No futures or short-selling simulation.
-   Historical results depend on the available dataset.
-   AI-generated configurations must pass backend validation before
    execution.
-   Only indicators and strategy conditions implemented in the backend
    are supported.

## Future Enhancements

-   Support for additional trading pairs and timeframes.
-   More technical indicators and strategy patterns.
-   Improved strategy clarification and unsupported-strategy handling.
-   Interactive equity curves and trade markers.
-   Enhanced backtesting analytics.
-   Additional risk-management configurations.
-   Improved frontend experience and result visualization.

## Security

-   Store API keys in environment variables.
-   Do not commit `.env` files.
-   Do not expose private credentials in source code.
-   Validate AI-generated strategy configurations on the backend before
    execution.

## Disclaimer

TradeSim is an educational and analytical project intended for strategy
research and historical backtesting. It is not financial advice and does
not guarantee trading profits. Users should independently evaluate
strategies before making financial decisions.

## Contributors

Developed as an academic project at Bennett University.
