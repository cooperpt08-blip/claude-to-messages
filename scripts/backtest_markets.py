#!/usr/bin/env python3
"""Replay a log of flagged edges (from scripts/watch_markets.py) and report
the hypothetical P&L of trading every opportunity that cleared an assumed
fee/slippage cost.

Usage:
    python scripts/backtest_markets.py
    python scripts/backtest_markets.py --log logs/prediction_market_edges_log.csv \\
        --position-size 250 --assumed-cost 0.015
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from prediction_market_bot import backtest, config, report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--log", default=config.EDGES_LOG_PATH, help="Edge log CSV to replay")
    parser.add_argument("--position-size", type=float, default=100.0, help="Dollars notional per trade")
    parser.add_argument(
        "--assumed-cost",
        type=float,
        default=0.01,
        help="Assumed round-trip fee+slippage per trade, in probability points (e.g. 0.01 = 1 cent)",
    )
    args = parser.parse_args()

    if not os.path.exists(args.log):
        print(f"No edge log found at {args.log}. Run scripts/watch_markets.py first to build one.")
        sys.exit(1)

    rows = backtest.load_edge_log(args.log)
    if not rows:
        print(f"{args.log} has no logged edges yet.")
        return

    summary, trades, equity_curve = backtest.simulate(
        rows, position_size=args.position_size, assumed_cost=args.assumed_cost
    )

    print(f"Backtest over {len(rows)} logged edge(s) from {args.log}:\n")
    print(report.format_backtest_summary(summary))


if __name__ == "__main__":
    main()
