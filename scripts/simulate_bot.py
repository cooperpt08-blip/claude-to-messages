#!/usr/bin/env python3
"""Run the scan -> edge-detection -> backtest pipeline against synthetic,
offline market data instead of live APIs.

Useful for demos and development environments that can't reach the real
platforms: it exercises the exact same edge.py / backtest.py code the live
bot uses, just fed a deterministic random-walk of prices instead of real
network responses.

Usage:
    python scripts/simulate_bot.py
    python scripts/simulate_bot.py --steps 200 --seed 42 --min-edge 0.02
"""

import argparse
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from prediction_market_bot import backtest, edge, report
from prediction_market_bot.simulate import generate_synthetic_history


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--steps", type=int, default=100, help="Number of synthetic time steps to generate")
    parser.add_argument("--step-minutes", type=int, default=15, help="Minutes represented by each step")
    parser.add_argument("--min-edge", type=float, default=0.02, help="Minimum edge to flag (probability points)")
    parser.add_argument("--position-size", type=float, default=100.0, help="Dollars notional per trade in the backtest")
    parser.add_argument("--assumed-cost", type=float, default=0.01, help="Assumed fee+slippage per trade")
    parser.add_argument("--seed", type=int, default=None, help="Random seed, for reproducible runs")
    parser.add_argument("--quiet", action="store_true", help="Skip per-step output, print only the final summary")
    args = parser.parse_args()

    history = generate_synthetic_history(n_steps=args.steps, step_minutes=args.step_minutes, seed=args.seed)

    rows = []
    for timestamp, quotes in history:
        cross_edges = edge.find_cross_platform_edges("synthetic-group", quotes, min_edge=args.min_edge)
        complementary_edges = edge.find_complementary_edges("synthetic-group", quotes, min_edge=args.min_edge)

        if not args.quiet and (cross_edges or complementary_edges):
            print(f"\n[{timestamp.isoformat()}]")
            print(report.format_quote_table(quotes))
            print(report.format_cross_platform_edges(cross_edges))
            print(report.format_complementary_edges(complementary_edges))

        for e in cross_edges:
            rows.append({"timestamp": timestamp, "kind": "cross_platform", "group": e.group, "detail": "", "edge": e.edge})
        for e in complementary_edges:
            rows.append({"timestamp": timestamp, "kind": "complementary", "group": e.group, "detail": "", "edge": e.edge})

    print(f"\n{len(rows)} edge(s) found across {args.steps} synthetic steps.\n")

    summary, trades, equity_curve = backtest.simulate(
        rows, position_size=args.position_size, assumed_cost=args.assumed_cost
    )
    print("Backtest of the synthetic run:\n")
    print(report.format_backtest_summary(summary))


if __name__ == "__main__":
    main()
