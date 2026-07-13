"""Edge and pricing-error detection across a group of equivalent markets.

Two independent signals are computed:

1. Cross-platform edge: platform A's Yes bid is higher than platform B's
   Yes ask, meaning you could (in principle) buy Yes on B and sell it on A
   for a guaranteed profit -- or, if you can't actually move capital between
   the two, it's at minimum a sign the platforms disagree on the odds.

2. Complementary mispricing: on a single platform, Yes and No should always
   cost ~$1 together (since exactly one of them pays out $1). If
   yes_ask + no_ask < $1, buying both is a guaranteed profit; if
   yes_bid + no_bid > $1, selling both is.

Both are reported gross of fees/slippage -- callers should apply
`min_edge` generously to leave headroom for real-world execution costs.
"""

from .types import ComplementaryEdge, CrossPlatformEdge


def find_cross_platform_edges(group_name: str, quotes: list, min_edge: float = 0.0) -> list:
    edges = []
    for sell in quotes:
        if sell.yes_bid is None:
            continue
        for buy in quotes:
            if buy.source == sell.source or buy.yes_ask is None:
                continue
            candidate = CrossPlatformEdge(
                group=group_name,
                sell_source=sell.source,
                sell_price=sell.yes_bid,
                buy_source=buy.source,
                buy_price=buy.yes_ask,
            )
            if candidate.edge > min_edge:
                edges.append(candidate)
    edges.sort(key=lambda e: e.edge, reverse=True)
    return edges


def find_complementary_edges(group_name: str, quotes: list, min_edge: float = 0.0) -> list:
    edges = []
    for q in quotes:
        if q.yes_ask is not None and q.no_ask is not None:
            candidate = ComplementaryEdge(
                group=group_name, source=q.source, side="buy", yes_price=q.yes_ask, no_price=q.no_ask
            )
            if candidate.edge > min_edge:
                edges.append(candidate)
        if q.yes_bid is not None and q.no_bid is not None:
            candidate = ComplementaryEdge(
                group=group_name, source=q.source, side="sell", yes_price=q.yes_bid, no_price=q.no_bid
            )
            if candidate.edge > min_edge:
                edges.append(candidate)
    edges.sort(key=lambda e: e.edge, reverse=True)
    return edges


def pricing_errors(quotes: list) -> dict:
    """Each platform's Yes mid-price minus the consensus (average) mid-price
    across all platforms in the group -- a quick read on which platform is
    the outlier and by how much."""
    mids = {q.source: q.yes_mid for q in quotes if q.yes_mid is not None}
    if not mids:
        return {}
    consensus = sum(mids.values()) / len(mids)
    return {source: mid - consensus for source, mid in mids.items()}
