"""Replay a log of flagged edges (produced by `scripts/watch_markets.py`)
and simulate what following them would have earned.

This is a simple bookkeeping exercise, not a market-microstructure
simulator: it assumes you could always execute at the logged price, sized
at a fixed position, minus an `assumed_cost` fee/slippage buffer per trade
(in the same probability-point units as `edge`). If the edge doesn't clear
that cost, the trade is treated as skipped rather than a loss -- real
arbitrage strategies don't take negative-EV trades on purpose.
"""

import csv
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class BacktestTrade:
    timestamp: datetime
    group: str
    kind: str
    gross_edge: float
    net_edge: float
    profit: float
    executed: bool


def load_edge_log(path: str) -> list:
    rows = []
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            rows.append(
                {
                    "timestamp": datetime.fromisoformat(row["timestamp"]),
                    "kind": row["kind"],
                    "group": row["group"],
                    "detail": row["detail"],
                    "edge": float(row["edge"]),
                }
            )
    return rows


def simulate(rows: list, position_size: float = 100.0, assumed_cost: float = 0.01):
    """Walk the log in timestamp order, "trading" each opportunity whose
    edge clears `assumed_cost`, sized at `position_size` (in dollars per
    $1-notional contract). Returns (summary_dict, trades, equity_curve)."""
    trades = []
    equity_curve = []
    cumulative = 0.0

    for row in sorted(rows, key=lambda r: r["timestamp"]):
        gross_edge = row["edge"]
        net_edge = gross_edge - assumed_cost
        executed = net_edge > 0
        profit = net_edge * position_size if executed else 0.0
        cumulative += profit

        trades.append(
            BacktestTrade(
                timestamp=row["timestamp"],
                group=row["group"],
                kind=row["kind"],
                gross_edge=gross_edge,
                net_edge=net_edge,
                profit=profit,
                executed=executed,
            )
        )
        equity_curve.append(cumulative)

    executed_trades = [t for t in trades if t.executed]
    summary = {
        "n_opportunities": len(trades),
        "n_executed": len(executed_trades),
        "win_rate": (len(executed_trades) / len(trades)) if trades else 0.0,
        "gross_edge_sum": sum(t.gross_edge for t in trades),
        "avg_net_edge": (
            sum(t.net_edge for t in executed_trades) / len(executed_trades) if executed_trades else 0.0
        ),
        "starting_balance": 0.0,
        "final_balance": cumulative,
    }
    return summary, trades, equity_curve
