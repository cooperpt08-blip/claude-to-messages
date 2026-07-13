"""Load groups of equivalent markets (same real-world question, different
platforms) from a YAML config, and fetch normalized quotes for each group.

Matching equivalent questions across platforms automatically (via NLP/fuzzy
title matching) is unreliable enough to be dangerous for anything involving
money -- two markets with similar titles can have different resolution
criteria, deadlines, or strike prices. So matching here is explicit and
user-curated: you look up each platform's market identifier (with
`scripts/list_markets.py`) and list them together in markets.yaml.
"""

import sys

import yaml

from . import config
from .sources import SOURCES
from .types import MarketGroup, MarketRef, Quote


def load_groups(path: str = None) -> list:
    path = path or config.DEFAULT_MARKETS_CONFIG
    with open(path) as f:
        raw = yaml.safe_load(f) or {}

    groups = []
    for g in raw.get("groups", []):
        members = [MarketRef(source=m["source"], params=m.get("params", {})) for m in g["members"]]
        groups.append(MarketGroup(name=g["name"], members=members))
    return groups


def fetch_group_quotes(group: MarketGroup, on_error=None) -> list:
    """Fetch a Quote for every member of a group. Failures on one platform
    (e.g. a network hiccup or a resolved/closed market) don't abort the
    whole group -- they're reported via `on_error` and skipped."""
    quotes = []
    for member in group.members:
        fetch_fn = SOURCES.get(member.source)
        if fetch_fn is None:
            raise ValueError(f"unknown source '{member.source}' in group '{group.name}'")
        try:
            quotes.append(fetch_fn(**member.params))
        except Exception as exc:  # noqa: BLE001 - one bad source shouldn't kill the scan
            if on_error:
                on_error(group, member, exc)
            else:
                print(f"warning: {group.name}/{member.source} failed: {exc}", file=sys.stderr)
    return quotes
