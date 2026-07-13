#!/usr/bin/env python3
"""Continuously scan configured prediction-market groups for cross-platform
and complementary (Yes+No) pricing edges, logging every flagged opportunity
to a CSV file.

Usage:
    python scripts/watch_markets.py                    # run forever, every 60s
    python scripts/watch_markets.py --interval 300      # every 5 minutes
    python scripts/watch_markets.py --iterations 5      # run 5 cycles then exit
"""

import argparse
import csv
import os
import sys
import time
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from prediction_market_bot import config
from scan_markets import scan

LOG_FIELDS = ["timestamp", "kind", "group", "detail", "edge"]


def _ensure_log_file(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if not os.path.exists(path):
        with open(path, "w", newline="") as f:
            csv.DictWriter(f, fieldnames=LOG_FIELDS).writeheader()


def _append_log(path, rows):
    with open(path, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=LOG_FIELDS)
        for row in rows:
            writer.writerow(row)


def _rows_for_log(cross_edges, complementary_edges):
    now = datetime.now(timezone.utc).isoformat()
    rows = []
    for e in cross_edges:
        detail = f"sell {e.sell_source}@{e.sell_price:.4f} / buy {e.buy_source}@{e.buy_price:.4f}"
        rows.append({"timestamp": now, "kind": "cross_platform", "group": e.group, "detail": detail, "edge": f"{e.edge:.4f}"})
    for e in complementary_edges:
        detail = f"{e.source} {e.side} yes+no={e.cost:.4f}"
        rows.append({"timestamp": now, "kind": "complementary", "group": e.group, "detail": detail, "edge": f"{e.edge:.4f}"})
    return rows


def run(config_path, min_edge, interval, iterations, log_path):
    _ensure_log_file(log_path)
    print(f"Scanning {config_path} every {interval}s, logging edges to {log_path}")
    print("Press Ctrl+C to stop.\n")

    cycle = 0
    try:
        while iterations is None or cycle < iterations:
            cross_edges, complementary_edges = scan(config_path, min_edge)
            rows = _rows_for_log(cross_edges, complementary_edges)
            if rows:
                _append_log(log_path, rows)
                print(f"\nLogged {len(rows)} edge(s) to {log_path}")

            cycle += 1
            if iterations is None or cycle < iterations:
                time.sleep(interval)
    except KeyboardInterrupt:
        print("\nStopped by user.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=config.DEFAULT_MARKETS_CONFIG, help="Path to markets.yaml")
    parser.add_argument("--min-edge", type=float, default=config.DEFAULT_MIN_EDGE, help="Minimum edge to report/log")
    parser.add_argument("--interval", type=int, default=60, help="Seconds between scans")
    parser.add_argument("--iterations", type=int, default=None, help="Stop after N cycles instead of running forever")
    parser.add_argument("--log", default=config.EDGES_LOG_PATH, help="CSV path to log flagged edges to")
    args = parser.parse_args()

    run(args.config, args.min_edge, args.interval, args.iterations, args.log)


if __name__ == "__main__":
    main()
