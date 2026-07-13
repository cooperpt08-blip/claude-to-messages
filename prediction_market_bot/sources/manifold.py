"""Manifold Markets adapter, backed by Manifold's public API.

Fully public, no API key. Manifold's binary markets are AMM-priced (no
order book), so there's no separate bid/ask -- `yes_bid == yes_ask ==
probability`. Treat prices from this source as informational/consensus
signal rather than something you can actually arbitrage against, since
Manifold trades play money.
API docs: https://docs.manifold.markets/api
"""

from ..types import Quote
from .base import SourceError, get_json, to_float

BASE_URL = "https://api.manifold.markets/v0"


def _market_to_quote(market: dict, market_id: str) -> Quote:
    prob = to_float(market.get("probability"))
    return Quote(
        source="manifold",
        market_id=market_id,
        question=market.get("question", market_id),
        yes_bid=prob,
        yes_ask=prob,
        no_bid=(1.0 - prob) if prob is not None else None,
        no_ask=(1.0 - prob) if prob is not None else None,
        volume=to_float(market.get("volume")),
        url=market.get("url"),
        has_order_book=False,
    )


def fetch_market(market_id: str = None, slug: str = None) -> Quote:
    """Fetch a single binary market by Manifold `market_id` or `slug`."""
    if not market_id and not slug:
        raise ValueError("manifold.fetch_market requires 'market_id' or 'slug'")

    if market_id:
        data = get_json(f"{BASE_URL}/market/{market_id}")
    else:
        data = get_json(f"{BASE_URL}/slug/{slug}")
    if data.get("outcomeType") != "BINARY":
        raise SourceError(f"manifold: market {market_id or slug} is not a binary Yes/No market")
    return _market_to_quote(data, market_id or slug)


def search_markets(keyword: str, limit: int = 10) -> list:
    """Keyword search via Manifold's search-markets endpoint."""
    data = get_json(f"{BASE_URL}/search-markets", params={"term": keyword, "limit": limit})
    binary_markets = [m for m in data if m.get("outcomeType") == "BINARY"]
    return [_market_to_quote(m, m.get("id")) for m in binary_markets[:limit]]
