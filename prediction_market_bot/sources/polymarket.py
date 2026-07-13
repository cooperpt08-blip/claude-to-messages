"""Polymarket adapter, backed by the public Gamma markets API.

No API key is required for read-only market data.
API docs: https://docs.polymarket.com/
"""

from ..types import Quote
from .base import SourceError, get_json, to_float

BASE_URL = "https://gamma-api.polymarket.com"


def _market_to_quote(market: dict, market_id: str) -> Quote:
    yes_bid = to_float(market.get("bestBid"))
    yes_ask = to_float(market.get("bestAsk"))
    # Polymarket's binary markets settle Yes + No == $1, and No isn't always
    # quoted directly, so derive it from the Yes book when it's missing.
    no_bid = to_float(market.get("bestNoBid"))
    no_ask = to_float(market.get("bestNoAsk"))
    if no_bid is None and yes_ask is not None:
        no_bid = 1.0 - yes_ask
    if no_ask is None and yes_bid is not None:
        no_ask = 1.0 - yes_bid

    slug = market.get("slug", market_id)
    return Quote(
        source="polymarket",
        market_id=market_id,
        question=market.get("question", slug),
        yes_bid=yes_bid,
        yes_ask=yes_ask,
        no_bid=no_bid,
        no_ask=no_ask,
        volume=to_float(market.get("volume")),
        url=f"https://polymarket.com/market/{slug}",
    )


def fetch_market(slug: str = None, market_id: str = None) -> Quote:
    """Fetch a single market by its Polymarket `slug` or numeric `market_id`."""
    if not slug and not market_id:
        raise ValueError("polymarket.fetch_market requires 'slug' or 'market_id'")

    params = {"slug": slug} if slug else {"id": market_id}
    data = get_json(f"{BASE_URL}/markets", params=params)
    if isinstance(data, list):
        if not data:
            raise SourceError(f"polymarket: no market found for {params}")
        market = data[0]
    else:
        market = data
    return _market_to_quote(market, slug or str(market_id))


def search_markets(keyword: str, limit: int = 10) -> list:
    """Best-effort keyword search over active Polymarket markets, to help
    discover slugs for markets.yaml. Fetches a batch of active markets and
    filters client-side, since the public API doesn't offer full-text search."""
    data = get_json(
        f"{BASE_URL}/markets",
        params={"active": "true", "closed": "false", "limit": 100, "order": "volume", "ascending": "false"},
    )
    keyword_lower = keyword.lower()
    matches = [m for m in data if keyword_lower in (m.get("question", "") or "").lower()]
    return [_market_to_quote(m, m.get("slug", str(m.get("id")))) for m in matches[:limit]]
