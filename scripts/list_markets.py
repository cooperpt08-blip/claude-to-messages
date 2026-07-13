#!/usr/bin/env python3
"""Search one platform for markets matching a keyword, to find the
slug/ticker/market_id you need to populate markets.yaml.

Usage:
    python scripts/list_markets.py polymarket "fed rate"
    python scripts/list_markets.py kalshi "fed rate" --limit 5
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from prediction_market_bot.report import format_quote_table
from prediction_market_bot.sources import SEARCHERS


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", choices=sorted(SEARCHERS), help="Platform to search")
    parser.add_argument("keyword", help="Keyword to match against market questions")
    parser.add_argument("--limit", type=int, default=10, help="Max results")
    args = parser.parse_args()

    quotes = SEARCHERS[args.source](args.keyword, limit=args.limit)
    if not quotes:
        print(f"No markets found on {args.source} matching {args.keyword!r}.")
        return

    print(format_quote_table(quotes))
    print("\nmarket_id values for markets.yaml:")
    for q in quotes:
        print(f"  {q.source}: {q.market_id}")


if __name__ == "__main__":
    main()
