
from decimal import Decimal, InvalidOperation
from pathlib import Path
from datetime import datetime, timezone
import csv


def to_decimal(value):
    """Safely convert a value to Decimal."""
    if value is None or value == "":
        return Decimal("0")

    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return Decimal("0")


def format_number(value, places=4):
    """Format Decimal values without unnecessary trailing zeros."""
    number = to_decimal(value)
    return f"{number:,.{places}f}".rstrip("0").rstrip(".")


def format_timestamp(value):
    """
    Support ISO timestamps and Unix timestamps in seconds or milliseconds.
    Return a readable UTC timestamp.
    """
    if value is None or value == "":
        return "N/A"

    try:
        if isinstance(value, (int, float)) or str(value).replace(".", "", 1).isdigit():
            timestamp = float(value)

            # Current Unix timestamps in milliseconds are 13 digits.
            if timestamp > 100_000_000_000:
                timestamp /= 1000

            return datetime.fromtimestamp(
                timestamp, tz=timezone.utc
            ).strftime("%Y-%m-%d %H:%M:%S UTC")

        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))

        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)

        return parsed.astimezone(timezone.utc).strftime(
            "%Y-%m-%d %H:%M:%S UTC"
        )

    except (ValueError, TypeError, OverflowError, OSError):
        return str(value)


def calculate_trade_statistics(trades):
    """Calculate statistics using closed trades only."""
    profits = [
        to_decimal(trade.get("net_pnl"))
        for trade in trades
    ]

    winners = [p for p in profits if p > 0]
    losers = [p for p in profits if p < 0]

    average_win = (
        sum(winners) / len(winners)
        if winners else Decimal("0")
    )

    average_loss = (
        sum(losers) / len(losers)
        if losers else Decimal("0")
    )

    largest_win = max(winners) if winners else Decimal("0")
    largest_loss = min(losers) if losers else Decimal("0")

    risk_reward = (
        average_win / abs(average_loss)
        if average_win > 0 and average_loss < 0
        else None
    )

    return {
        "total_closed_trades": len(trades),
        "winning_trades": len(winners),
        "losing_trades": len(losers),
        "breakeven_trades": len(trades) - len(winners) - len(losers),
        "closed_trade_net_pnl": sum(profits),
        "average_win": average_win,
        "average_loss": average_loss,
        "largest_win": largest_win,
        "largest_loss": largest_loss,
        "average_risk_reward": risk_reward,
    }


def get_equity_points(equity_curve):
    """Extract valid timestamps and equity values from the equity curve."""
    points = []

    for item in equity_curve:
        if not isinstance(item, dict):
            continue

        timestamp = item.get("time", item.get("timestamp"))
        equity = item.get("equity")

        if timestamp is None or equity is None:
            continue

        points.append({
            "time": format_timestamp(timestamp),
            "equity": to_decimal(equity),
            "raw_time": timestamp,
        })

    return points


def calculate_drawdown(equity_points):
    """Calculate peak-to-trough drawdown from the equity curve."""
    peak = None
    drawdowns = []

    for point in equity_points:
        equity = point["equity"]

        if peak is None or equity > peak:
            peak = equity

        drawdown = peak - equity

        drawdown_percentage = (
            (drawdown / peak) * Decimal("100")
            if peak and peak > 0
            else Decimal("0")
        )

        drawdowns.append({
            "time": point["time"],
            "drawdown": drawdown,
            "drawdown_percentage": drawdown_percentage,
        })

    return drawdowns


def print_backtest_report(results):
    """Print a readable summary and complete closed-trade report."""
    trades = results.get("trades", [])
    open_position = results.get("open_position")
    stats = calculate_trade_statistics(trades)

    initial_capital = to_decimal(results.get("initial_capital"))
    final_equity = to_decimal(results.get("final_equity"))
    total_pnl = to_decimal(results.get("total_pnl"))

    open_unrealized_pnl = Decimal("0")

    if isinstance(open_position, dict):
        open_unrealized_pnl = to_decimal(
            open_position.get("unrealized_pnl")
        )

    print("\n" + "=" * 65)
    print("TRADESIM - DETAILED BACKTEST REPORT")
    print("=" * 65)

    print("\nPORTFOLIO SUMMARY")
    print("-" * 65)
    print(f"Initial capital:          {format_number(initial_capital)}")
    print(f"Final equity:             {format_number(final_equity)}")
    print(f"Total P&L:                {format_number(total_pnl)}")
    print(
        "Total return:             "
        f"{format_number(results.get('total_return_percentage'))}%"
    )

    print("\nTRADE STATISTICS")
    print("-" * 65)
    print(f"Closed trades:            {stats['total_closed_trades']}")
    print(f"Winning trades:           {stats['winning_trades']}")
    print(f"Losing trades:            {stats['losing_trades']}")
    print(f"Breakeven trades:         {stats['breakeven_trades']}")
    print(
        "Win rate:                 "
        f"{format_number(results.get('win_rate_percentage'))}%"
    )
    print(f"Average win:              {format_number(stats['average_win'])}")
    print(f"Average loss:             {format_number(stats['average_loss'])}")
    print(f"Largest win:              {format_number(stats['largest_win'])}")
    print(f"Largest loss:             {format_number(stats['largest_loss'])}")

    if stats["average_risk_reward"] is not None:
        print(
            "Average win/loss ratio:   "
            f"{format_number(stats['average_risk_reward'])}:1"
        )
    else:
        print("Average win/loss ratio:   N/A")

    print(
        "Profit factor:            "
        f"{format_number(results.get('profit_factor'))}"
    )
    print(
        "Maximum drawdown:         "
        f"{format_number(results.get('max_drawdown'))}"
    )
    print(
        "Maximum drawdown (%):     "
        f"{format_number(results.get('max_drawdown_percentage'))}%"
    )

    print("\nP&L BREAKDOWN")
    print("-" * 65)
    print(
        "Closed-trade net P&L:     "
        f"{format_number(stats['closed_trade_net_pnl'])}"
    )
    print(
        "Open-position P&L:       "
        f"{format_number(open_unrealized_pnl)}"
    )

    if isinstance(open_position, dict):
        print("\nOPEN POSITION")
        print("-" * 65)
        print(
            f"Entry time:               "
            f"{format_timestamp(open_position.get('entry_time'))}"
        )
        print(
            f"Entry price:              "
            f"{format_number(open_position.get('entry_price'))}"
        )
        print(
            f"Quantity:                 "
            f"{format_number(open_position.get('quantity'), 8)}"
        )
        print(
            f"Unrealized P&L:           "
            f"{format_number(open_unrealized_pnl)}"
        )
    else:
        print("\nNo open position.")

    print("\nCLOSED TRADE DETAILS")
    print("-" * 65)

    if not trades:
        print("No closed trades.")
    else:
        for index, trade in enumerate(trades, start=1):
            print(f"\nTrade {index}")
            print(
                f"  Entry time:    "
                f"{format_timestamp(trade.get('entry_time'))}"
            )
            print(
                f"  Exit time:     "
                f"{format_timestamp(trade.get('exit_time'))}"
            )
            print(
                f"  Entry price:   "
                f"{format_number(trade.get('entry_price'))}"
            )
            print(
                f"  Exit price:    "
                f"{format_number(trade.get('exit_price'))}"
            )
            print(
                f"  Quantity:      "
                f"{format_number(trade.get('quantity'), 8)}"
            )
            print(
                f"  Gross P&L:     "
                f"{format_number(trade.get('gross_pnl'))}"
            )
            print(
                f"  Entry fee:     "
                f"{format_number(trade.get('entry_fee'))}"
            )
            print(
                f"  Exit fee:      "
                f"{format_number(trade.get('exit_fee'))}"
            )
            print(
                f"  Net P&L:       "
                f"{format_number(trade.get('net_pnl'))}"
            )
            print(
                f"  Return:        "
                f"{format_number(trade.get('return_percentage'))}%"
            )
            print(
                f"  Exit reason:   "
                f"{trade.get('exit_reason', 'N/A')}"
            )

    ignored_signals = results.get("ignored_signals", [])

    print("\nIGNORED SIGNALS")
    print("-" * 65)

    if not ignored_signals:
        print("None.")
    else:
        for signal in ignored_signals:
            print(
                f"{format_timestamp(signal.get('time'))} | "
                f"{signal.get('signal')} | "
                f"{signal.get('reason')}"
            )

    print("\n" + "=" * 65)
    print("END OF REPORT")
    print("=" * 65)


def save_trade_csv(trades, output_path):
    """Save closed trades to a CSV file."""
    fields = [
        "trade_number",
        "entry_time",
        "exit_time",
        "entry_price",
        "exit_price",
        "quantity",
        "gross_pnl",
        "entry_fee",
        "exit_fee",
        "net_pnl",
        "return_percentage",
        "exit_reason",
    ]

    with open(output_path, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()

        for index, trade in enumerate(trades, start=1):
            row = {
                "trade_number": index,
                **trade,
            }

            row["entry_time"] = format_timestamp(
                trade.get("entry_time")
            )
            row["exit_time"] = format_timestamp(
                trade.get("exit_time")
            )

            writer.writerow({
                field: row.get(field, "")
                for field in fields
            })


def save_equity_and_drawdown_charts(results, output_dir):
    """Generate and save equity and drawdown charts."""
    try:
        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates
    except ImportError:
        print(
            "\nMatplotlib is not installed. "
            "Run: pip install matplotlib"
        )
        return

    equity_points = get_equity_points(
        results.get("equity_curve", [])
    )

    if len(equity_points) < 2:
        print("\nNot enough equity-curve points to generate charts.")
        return

    dates = [
        datetime.strptime(
            point["time"], "%Y-%m-%d %H:%M:%S UTC"
        )
        for point in equity_points
    ]

    equities = [
        float(point["equity"])
        for point in equity_points
    ]

    # Equity curve
    plt.figure(figsize=(12, 5))
    plt.plot(dates, equities, label="Portfolio equity")
    plt.title("TradeSim - Portfolio Equity Curve")
    plt.xlabel("Time (UTC)")
    plt.ylabel("Equity")
    plt.grid(True, alpha=0.3)
    plt.legend()

    axis = plt.gca()
    axis.xaxis.set_major_formatter(
        mdates.DateFormatter("%d %b %H:%M")
    )
    plt.gcf().autofmt_xdate()

    plt.tight_layout()
    equity_path = output_dir / "equity_curve.png"
    plt.savefig(equity_path, dpi=150)
    plt.close()

    # Drawdown curve
    drawdowns = calculate_drawdown(equity_points)

    drawdown_values = [
        float(point["drawdown_percentage"])
        for point in drawdowns
    ]

    plt.figure(figsize=(12, 5))
    plt.plot(dates, drawdown_values, label="Drawdown")
    plt.title("TradeSim - Portfolio Drawdown")
    plt.xlabel("Time (UTC)")
    plt.ylabel("Drawdown (%)")
    plt.grid(True, alpha=0.3)
    plt.legend()

    axis = plt.gca()
    axis.xaxis.set_major_formatter(
        mdates.DateFormatter("%d %b %H:%M")
    )
    plt.gcf().autofmt_xdate()

    plt.tight_layout()
    drawdown_path = output_dir / "drawdown_curve.png"
    plt.savefig(drawdown_path, dpi=150)
    plt.close()

    print(f"\nEquity chart saved:   {equity_path}")
    print(f"Drawdown chart saved: {drawdown_path}")


def generate_backtest_report(results, output_dir="reports"):
    """Generate console report, CSV, and charts."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print_backtest_report(results)

    trades = results.get("trades", [])
    csv_path = output_dir / "trades.csv"

    save_trade_csv(trades, csv_path)
    print(f"\nTrade CSV saved:      {csv_path}")

    save_equity_and_drawdown_charts(results, output_dir)

    print(f"\nAll report files are in: {output_dir.resolve()}")
