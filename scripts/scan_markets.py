#!/usr/bin/env python3
"""One-shot scan of every market group in markets.yaml: fetch current prices
from each configured platform, print a comparison table, and flag any
cross-platform or complementary (Yes+No) pricing edges above --min-edge.

Usage:
    python scripts/scan_markets.py
    python scripts/scan_markets.py --config my_markets.yaml --min-edge 0.03
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from prediction_market_bot import config, edge, markets, report


def scan(config_path: str, min_edge: float):
    groups = markets.load_groups(config_path)
    if not groups:
        print(f"No market groups defined in {config_path}. See markets.yaml for the format.")
        return [], []

    all_cross_edges = []
    all_complementary_edges = []

    for group in groups:
        print(f"\n=== {group.name} ===")
        quotes = markets.fetch_group_quotes(group)
        if not quotes:
            print("  no quotes fetched (all sources failed)")
            continue

        print(report.format_quote_table(quotes))

        cross_edges = edge.find_cross_platform_edges(group.name, quotes, min_edge=min_edge)
        complementary_edges = edge.find_complementary_edges(group.name, quotes, min_edge=min_edge)
        errors = edge.pricing_errors(quotes)

        print("\nCross-platform edges (sell high / buy low):")
        print(report.format_cross_platform_edges(cross_edges))
        print("\nComplementary (Yes+No) mispricing:")
        print(report.format_complementary_edges(complementary_edges))
        print("\nPricing error vs. cross-platform consensus:")
        print(report.format_pricing_errors(errors))

        all_cross_edges.extend(cross_edges)
        all_complementary_edges.extend(complementary_edges)

    return all_cross_edges, all_complementary_edges


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=config.DEFAULT_MARKETS_CONFIG, help="Path to markets.yaml")
    parser.add_argument(
        "--min-edge",
        type=float,
        default=config.DEFAULT_MIN_EDGE,
        help="Minimum edge (probability points) to report, default from PMB_MIN_EDGE or 0.02",
    )
    args = parser.parse_args()

    cross_edges, complementary_edges = scan(args.config, args.min_edge)

    total = len(cross_edges) + len(complementary_edges)
    print(f"\n{total} edge(s) found above {args.min_edge:.4f} threshold.")


if __name__ == "__main__":
    main()
